from datetime import datetime, timedelta, timezone
import logging
from backend.core.models.intent import Intent
from backend.infra.persistence.redis import RedisClient, get_redis_client
from .keys import RedisKeys
from fastapi import Depends
from redis.asyncio import Redis
from .keys import RedisKeys
from backend.core.models.intent import Intent
import json
import logging
from backend.core.models.ranking import calculate_score

logger = logging.getLogger(__name__)

INTENT_TTL_SECONDS = 24 * 60 * 60 # 24h

class IntentRepository:
    def __init__(self, redis: Redis = Depends(get_redis_client)):
        self.redis = redis

    async def save_intent(self, intent: Intent) -> None:
        key = RedisKeys.intent(intent.id)
        # Convert pydantic model to json
        data = intent.model_dump_json()
        await self.redis.set(key, data, ex=INTENT_TTL_SECONDS)
        
        # Add to geo index
        # GEOADD key longitude latitude member
        await self.redis.geoadd(RedisKeys.intent_geo(), (intent.longitude, intent.latitude, str(intent.id)))
        
        # Add to Expiration Queue (Sorted Set by timestamp)
        expire_at = datetime.now(timezone.utc) + timedelta(seconds=INTENT_TTL_SECONDS)
        await self.redis.zadd(RedisKeys.expiry_queue(), {str(intent.id): expire_at.timestamp()})
        
        # Add to User's Intent List
        if intent.user_id:
            await self.redis.sadd(RedisKeys.user_intents(intent.user_id), str(intent.id))
        
        logger.info(f"Saved intent {intent.id} with TTL {INTENT_TTL_SECONDS}s")

    async def get_intent(self, intent_id: str) -> Intent | None:
        key = RedisKeys.intent(intent_id)
        data = await self.redis.get(key)
        if not data:
            return None
        intent = Intent.model_validate_json(data)
        
        # Populate join count
        join_key = RedisKeys.intent_joins(intent_id)
        count = await self.redis.scard(join_key)
        # We need to manually update the field since the model is frozen and it was loaded from JSON without it (or with default 0).
        # Actually Pydantic models with frozen=True invoke copy to update.
        # But wait, create_intent saves with default 0.
        # So we just need to overwrite it with the fresh count from Redis.
        # Using model_copy with update.
        intent = intent.with_join_count(count)
        return intent

    async def find_nearby(self, lat: float, lon: float, radius_km: float = 1.0, limit: int = 50) -> list[Intent]:
        # Fetch 2x limit to allow for ranking and filtering
        fetch_count = limit * 2
        
        # GEOSEARCH with distance
        results = await self.redis.geosearch(
            RedisKeys.intent_geo(),
            longitude=lon,
            latitude=lat,
            radius=radius_km,
            unit="km",
            sort="ASC",
            count=100, # ample sample for density
            withdist=True
        )
        
        if not results:
            return []

        # results is list of (member, distance) tuples
        member_ids = [m[0] for m in results]
        distances = {m[0]: m[1] for m in results} # Map id -> dist

        keys = [RedisKeys.intent(mid) for mid in member_ids]
        json_list = await self.redis.mget(keys)
        
        candidates = []
        expired_members = []
        
        # Pipeline for join counts
        pipeline = self.redis.pipeline()
        valid_indices = []

        for i, json_str in enumerate(json_list):
            if json_str:
                intent = Intent.model_validate_json(json_str)
                if intent.flags < 3:
                    candidates.append(intent)
                    pipeline.scard(RedisKeys.intent_joins(intent.id))
            else:
                expired_members.append(member_ids[i])
        
        if not candidates:
            if expired_members:
                await self.redis.zrem(RedisKeys.intent_geo(), *expired_members)
            return []

        # Execute pipeline to get counts
        counts = await pipeline.execute()
        

        scored_intents = []
        now = datetime.now(timezone.utc)
        
        for intent, count in zip(candidates, counts):
            # Update count
            intent = intent.with_join_count(count)
            
            # Check Visibility
            dist = distances.get(str(intent.id), radius_km)
            if not intent.is_visible(dist):
                continue

            # Calculate Score
            total_score = calculate_score(intent, dist, radius_km, now)
            
            scored_intents.append((total_score, intent))
            
        # Cleanup expired
        if expired_members:
             await self.redis.zrem(RedisKeys.intent_geo(), *expired_members)
             
        # Sort by score descending
        scored_intents.sort(key=lambda x: x[0], reverse=True)
        
        # Return top 'limit' intents
        return [item[1] for item in scored_intents[:limit]]

    async def flag_intent(self, intent_id: UUID) -> int:
        key = RedisKeys.intent(intent_id)
        data = await self.redis.get(key)
        if not data:
            return 0
            
        intent = Intent.model_validate_json(data)
        intent = intent.flag()
        
        # Save back. We should use a lua script for atomicity but MVP.
        # Preserve TTL?
        ttl = await self.redis.ttl(key)
        if ttl > 0:
            await self.redis.set(key, intent.model_dump_json(), ex=ttl)
            
        return intent.flags

    async def get_clusters(self, lat: float, lon: float, radius_km: float = 10.0) -> list[dict]:
        """
        Aggregates intents into clusters based on a simple grid system.
        """
        # Fetch all items in valid radius (limit to 500 for sanity)
        res = await self.redis.geosearch(
               name=RedisKeys.intent_geo(),
               longitude=lon,
               latitude=lat,
               radius=radius_km,
               unit="km",
               count=1000,
               withcoord=True
        )
        if not res:
            return []
            
        # Basic clustering: Round to decimal places
        # 3 decimal places ~110m (Street level)
        # 2 decimal places ~1.1km (Neighborhood)
        # We can dynamically choose based on radius. 
        # For radius=10km, precision 2 is good.
        precision = 2 if radius_km > 5 else 3
        
        clusters = {}
        
        for member_hash, point in res: # redis-py returns [ [member, (lon, lat)], ... ]
             # member_hash is the member string, point is (lon, lat) tuple
             # Actually withcoord=True returns: [[member, dist, (lon,lat)]] if withdist=True?
             # Docs say: return list of (member, distance, (longitude, latitude))
             # We didn't ask for dist, so it's (member, (longitude, latitude))
             r_lon, r_lat = point
             
             # Create grid key
             grid_lat = round(r_lat, precision)
             grid_lon = round(r_lon, precision)
             key = (grid_lat, grid_lon)
             
             if key not in clusters:
                 clusters[key] = {"count": 0, "lat_sum": 0, "lon_sum": 0}
            
             clusters[key]["count"] += 1
             clusters[key]["lat_sum"] += r_lat
             clusters[key]["lon_sum"] += r_lon
             
        # Format results
        results = []
        for key, data in clusters.items():
            count = data["count"]
            # Centroid
            avg_lat = data["lat_sum"] / count
            avg_lon = data["lon_sum"] / count
            
            # Helper for ID
            geohash_sim = f"{key[0]},{key[1]}"
            
            results.append({
                "geohash": geohash_sim,
                "latitude": avg_lat,
                "longitude": avg_lon,
                "count": count
            })
            
        return results

    async def count_nearby(self, lat: float, lon: float, radius_km: float = 1.0) -> int:
        try:
           # GEOSEARCH key FROMLONLAT lon lat BYRADIUS radius km ASC count 100
           res = await self.redis.geosearch(
               name=RedisKeys.intent_geo(),
               longitude=lon,
               latitude=lat,
               radius=radius_km,
               unit="km",
               sort="ASC",
               count=100
           )
           logger.info(f"Count nearby lat={lat} lon={lon} r={radius_km} -> {len(res)} items")
           return len(res)
        except Exception as e:
            logger.error(f"Count nearby failed: {e}")
            return 0

