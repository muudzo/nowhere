#!/usr/bin/env bash
# check_stack.sh - Verify Docker Compose stack health and connectivity

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

set -euo pipefail

echo -e "${YELLOW}Checking Docker containers status...${NC}"
docker-compose ps

echo -e "\n${YELLOW}Checking container logs for errors (last 10 lines each)...${NC}"
services=("api" "postgres" "redis")
for service in "${services[@]}"; do
    echo -e "\n--- ${service} ---"
    docker-compose logs --tail=10 "$service" || true
done

echo -e "\n${YELLOW}Testing API endpoint...${NC}"
API_RESPONSE=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:8000/health || true)
if [ "${API_RESPONSE}" = "200" ]; then
    echo -e "${GREEN}API is reachable at http://localhost:8000/health${NC}"
else
    echo -e "${RED}API check failed! Status code: ${API_RESPONSE}${NC}"
fi

echo -e "\n${YELLOW}Testing Postgres connection from Postgres container...${NC}"
if docker-compose exec -T postgres pg_isready -U postgres >/dev/null 2>&1; then
    echo -e "${GREEN}Postgres is accepting connections (pg_isready successful)${NC}"
else
    echo -e "${RED}Postgres is not accepting connections${NC}"
    docker-compose exec -T postgres pg_isready -U postgres || true
fi

echo -e "\n${YELLOW}Testing Redis connection from Redis container...${NC}"
REDIS_PONG=$(docker-compose exec -T redis redis-cli ping 2>/dev/null || true)
if [ "${REDIS_PONG}" = "PONG" ]; then
    echo -e "${GREEN}Redis connection successful${NC}"
else
    echo -e "${RED}Failed to connect to Redis (redis-cli ping did not return PONG)${NC}"
fi

echo -e "\n${YELLOW}Testing Caddy proxy routing...${NC}"
PROXY_RESPONSE=$(curl -s -o /dev/null -w "%{http_code}" http://localhost/health || true)
if [ "${PROXY_RESPONSE}" = "200" ]; then
    echo -e "${GREEN}Proxy routing works (http://localhost/health)${NC}"
else
    echo -e "${RED}Proxy routing failed! Status code: ${PROXY_RESPONSE}${NC}"
fi

echo -e "\n${GREEN}✅ Stack verification complete${NC}"
