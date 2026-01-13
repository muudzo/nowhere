import asyncio
import httpx
from uuid import uuid4
from backend.tasks.seeder import seed_ambient_intents
from backend.infra.persistence.intent_repo import IntentRepository
from backend.infra.persistence.redis import RedisClient

BASE_URL = "http://localhost:8000"

async def main():
    print("Starting Clustering verification...")
    
    # 0. Connect Redis for direct seeding
    await RedisClient.connect("redis://localhost:6379")
    redis = RedisClient.get_client()
    repo = IntentRepository(redis)
    
    # 1. Seed 50 intents at (40.7, -74.0) with small radius (0.5km)
    # This ensures they fall into the same or few grid cells.
    print("1. Seeding 50 intents...")
    await seed_ambient_intents(repo, 40.7, -74.0, count=50, radius_km=0.5)
    
    async with httpx.AsyncClient(base_url=BASE_URL, timeout=30.0) as client:
        # 2. Handshake for token (needed for rate limits / general access?)
        # Actually /nearby and /clusters are likely public or need simple auth?
        # Middleware checks headers.
        # Let's use anonymous ID.
        headers = {"X-Nowhere-Identity": str(uuid4())}
        
        # 3. Call Clusters
        print("2. Fetching Clusters...")
        r = await client.get("/intents/clusters?lat=40.7&lon=-74.0&radius=10", headers=headers)
        
        if r.status_code != 200:
            print(f"FAILED: {r.status_code} {r.text}")
            return
            
        data = r.json()
        clusters = data.get("clusters", [])
        print(f"   Got {len(clusters)} clusters.")
        
        total_count = sum(c["count"] for c in clusters)
        print(f"   Total grouped count: {total_count}")
        
        if len(clusters) > 0 and len(clusters) < 50:
            print("   SUCCESS: Cloning happened (clustered into groups).")
        elif len(clusters) == 50:
             print("   WARNING: No grouping happened (precision too high?).")
        else:
             print("   FAILED: No clusters found.")

        # 4. Check Nearby still works
        print("3. Fetching Nearby...")
        r = await client.get("/intents/nearby?lat=40.7&lon=-74.0&radius=10", headers=headers)
        if r.status_code == 200:
            print(f"   Success. Got {r.json()['count']} items.")
        else:
            print(f"   FAILED nearpy: {r.status_code}")

    await RedisClient.disconnect()

if __name__ == "__main__":
    asyncio.run(main())
