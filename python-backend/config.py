"""
Configuration file for the OpenAI CS Agents Demo.
Optimized for free tier usage with rate limiting.
"""

import os
import asyncio
from typing import Dict, Any

# Set the OpenAI API key
os.environ["OPENAI_API_KEY"] = "<your_api_key>"


# Configuration variables
DEBUG = True
LOG_LEVEL = "INFO"

# Rate limiting configuration for free tier
RATE_LIMIT_DELAY = 1.0  # Delay between requests in seconds
MAX_RETRIES = 3
RETRY_DELAY = 2.0

# Model optimization for free tier
USE_FAST_MODEL = True  # Use gpt-3.5-turbo instead of gpt-4 for most operations
FAST_MODEL = "gpt-3.5-turbo"
PREMIUM_MODEL = "gpt-4"

# Context optimization
MAX_CONTEXT_LENGTH = 4000  # Reduced context length for free tier
MAX_CONVERSATION_HISTORY = 10  # Limit conversation history
CACHE_RESPONSES = True
CACHE_TTL = 300  # 5 minutes

# Response optimization
MAX_RESPONSE_LENGTH = 500
USE_STREAMING = False  # Disable streaming for free tier

# Rate limiter
class RateLimiter:
    def __init__(self, delay: float = RATE_LIMIT_DELAY):
        self.delay = delay
        self.last_request = 0
    
    async def wait(self):
        """Wait if necessary to respect rate limits."""
        now = asyncio.get_event_loop().time()
        time_since_last = now - self.last_request
        if time_since_last < self.delay:
            await asyncio.sleep(self.delay - time_since_last)
        self.last_request = asyncio.get_event_loop().time()

# Global rate limiter instance
rate_limiter = RateLimiter()

# Simple in-memory cache
response_cache: Dict[str, Any] = {}

def get_cached_response(key: str) -> Any:
    """Get cached response if available and not expired."""
    if not CACHE_RESPONSES:
        return None
    
    if key in response_cache:
        cached_data = response_cache[key]
        import time
        if time.time() - cached_data['timestamp'] < CACHE_TTL:
            return cached_data['response']
        else:
            del response_cache[key]
    return None

def cache_response(key: str, response: Any):
    """Cache a response."""
    if not CACHE_RESPONSES:
        return
    
    import time
    response_cache[key] = {
        'response': response,
        'timestamp': time.time()
    }
