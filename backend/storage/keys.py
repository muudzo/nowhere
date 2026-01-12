from uuid import UUID

class RedisKeys:
    @staticmethod
    def intent(intent_id: UUID | str) -> str:
        return f"intent:{str(intent_id)}"

    @staticmethod
    def intent_geo() -> str:
        return "intents:geo" # Global geo index

    @staticmethod
    def intent_messages(intent_id: UUID | str) -> str:
        return f"intent:{str(intent_id)}:msgs"

    @staticmethod
    def intent_joins(intent_id: UUID | str) -> str:
        return f"intent:{str(intent_id)}:joins" # Set of user_ids

    @staticmethod
    def rate_limit(user_id: str, action: str) -> str:
        return f"identity:{user_id}:limits:{action}"
