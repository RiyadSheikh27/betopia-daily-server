from rest_framework.throttling import AnonRateThrottle, UserRateThrottle


class AnonThrottle(AnonRateThrottle):
    """Rate limit for anonymous users"""

    scope = "anon"


class UserThrottle(UserRateThrottle):
    """Rate limit for authenticated users"""

    scope = "user"


class StrictAnonThrottle(AnonRateThrottle):
    """Strict rate limit for anonymous users on sensitive endpoints"""

    scope = "anon_strict"


class StrictUserThrottle(UserRateThrottle):
    """Strict rate limit for authenticated users on sensitive endpoints"""

    scope = "user_strict"
