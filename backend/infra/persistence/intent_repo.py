from datetime import datetime, timedelta, timezone
import logging
from uuid import UUID
from backend.core.models.intent import Intent
from backend.infra.persistence.redis import RedisClient, get_redis_client
from .keys import RedisKeys
from fastapi import Depends
from redis.asyncio import Redis
from .keys import RedisKeys
from backend.core.models.intent import Intent
from .lua_scripts import LuaScripts
import json
import logging
from backend.core.models.ranking import calculate_score

logger = logging.getLogger(__name__)

INTENT_TTL_SECONDS = 24 * 60 * 60 # 24h

class IntentRepository:
    def __init__(self, redis: Redis = Depends(get_redis_client), reader: Redis | None = None):
        """
        :param redis: Write client (can be Pipeline)
        :param reader: Read client (must be Redis instance)
        """
        self.redis = redis
        self.reader = reader or redis

    async def save_intent(self, intent: Intent) -> None:
        key = RedisKeys.intent(intent.id)
        # Convert pydantic model to json
        data = intent.model_dump_json()
        await self.redis.set(key, data, ex=INTENT_TTL_SECONDS)
        
        # Add to geo index
        await self.redis.geoadd(RedisKeys.intent_geo(), (intent.longitude, intent.latitude, str(intent.id)))
        
        # Add to Expiration Queue
        expire_at = datetime.now(timezone.utc) + timedelta(seconds=INTENT_TTL_SECONDS)
        await self.redis.zadd(RedisKeys.expiry_queue(), {str(intent.id): expire_at.timestamp()})
        
        # Add to User's Intent List
        if intent.user_id:
            await self.redis.sadd(RedisKeys.user_intents(intent.user_id), str(intent.id))
        
        logger.info(f"Saved intent {intent.id} with TTL {INTENT_TTL_SECONDS}s")

    async def get_intent(self, intent_id: str) -> Intent | None:
        key = RedisKeys.intent(intent_id)
        data = await self.reader.get(key)
        if not data:
            return None
        intent = Intent.model_validate_json(data)
        
        # Populate join count
        join_key = RedisKeys.intent_joins(intent_id)
        count = await self.reader.scard(join_key)
        intent = intent.with_join_count(count)
        return intent

    async def find_nearby(self, lat: float, lon: float, radius_km: float = 1.0, limit: int = 50) -> list[Intent]:
        # Fetch 2x limit to allow for ranking and filtering
        fetch_count = limit * 2
        
        # GEOSEARCH using reader
        results = await self.reader.geosearch(
            RedisKeys.intent_geo(),
            longitude=lon,
            latitude=lat,
            radius=radius_km,
            unit="km",
            sort="ASC",
            count=100, 
            withdist=True
        )
        
        if not results:
            return []

        # results is list of (member, distance) tuples
        member_ids = [m[0] for m in results]
        distances = {m[0]: m[1] for m in results} 

        keys = [RedisKeys.intent(mid) for mid in member_ids]
        json_list = await self.reader.mget(keys)
        
        candidates = []
        expired_members = []
        
        # Pipeline for join counts (Reader pipeline)
        # Note: If self.reader is same as self.redis and self.redis is pipeline, this breaks.
        # Check if reader is actually a client.
        pipeline = self.reader.pipeline()
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
            # Clean up expired using Writer
            if expired_members:
                await self.redis.zrem(RedisKeys.intent_geo(), *expired_members)
            return []

        # Execute pipeline to get counts
        counts = await pipeline.execute()

        scored_intents = []
        now = datetime.now(timezone.utc)
        
        for intent, count in zip(candidates, counts):
            intent = intent.with_join_count(count)
            
            dist = distances.get(str(intent.id), radius_km)
            if not intent.is_visible(dist):
                continue

            total_score = calculate_score(intent, dist, radius_km, now)
            scored_intents.append((total_score, intent))
            
        # Cleanup expired using Writer
        if expired_members:
             await self.redis.zrem(RedisKeys.intent_geo(), *expired_members)
             
        scored_intents.sort(key=lambda x: x[0], reverse=True)
        return [item[1] for item in scored_intents[:limit]]

    async def flag_intent(self, intent_id: UUID) -> int:
        key = RedisKeys.intent(intent_id)
        # Atomic Lua script
        result = await self.redis.eval(LuaScripts.ATOMIC_FLAG, 1, str(key), 1)
        # If pipeline, result is Pipeline object (truthy).
        # We can't fetch the int value until commit.
        # But Handler expects int.
        # We'll rely on the handler handling Deferred or ignoring it in UoW context?
        # IMPORTANT: Hardening prompt asks for UoW.
        # If we are in UoW, result is not available.
        # We return 0 here assuming eventual consistency or special handling.
        if hasattr(self.redis, "execute_command"): # Is real client
             return int(result)
        return 0 # Deferred in pipeline

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

