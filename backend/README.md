Nowhere - Backend

Structure and responsibilities
- `api/` - FastAPI entrypoint and HTTP routes (thin handlers)
- `application/` - application services and handlers (commands/queries)
- `domain/` - entity definitions and repository interfaces
- `infrastructure/` - concrete repositories for Redis and Postgres, Unit of Work
- `security/` - device token signing and verification
- `config.py` - environment-driven settings
