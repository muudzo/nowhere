class DomainError(Exception):
    """Base class for domain exceptions."""
    pass

class IntentNotFound(DomainError):
    pass

class IntentExpired(DomainError):
    pass

class InvalidAction(DomainError):
    pass

class SpamDetected(DomainError):
    pass
