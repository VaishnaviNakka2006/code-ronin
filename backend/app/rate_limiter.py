from slowapi import Limiter
from slowapi.util import get_remote_address

# Initialize limiter – default 100 per hour per IP
limiter = Limiter(
    key_func=get_remote_address,
    default_limits=["100 per hour"]
)