import os
import base64
import json
from diskcache import Cache
from typing import Any, Optional

# Inicializar caché
cache_dir = os.path.join(os.path.dirname(__file__), ".cache")
meta_cache = Cache(os.path.join(cache_dir, "meta"))
stream_cache = Cache(os.path.join(cache_dir, "stream"))
key_cache = Cache(os.path.join(cache_dir, "key"))

key_bytes = os.urandom(64)

def get_cached(cache: Cache, key: str, expire: int = 3600) -> Optional[Any]:
    """Get a value from cache if it exists."""
    return cache.get(key) if key in cache else None

def set_cached(cache: Cache, key: str, value: Any, expire: int = 3600) -> None:
    """Set a value in cache with expiration."""
    cache.set(key, value, expire=expire)

def encrypt(input_string: str) -> str:
    input_bytes = input_string.encode()
    result = xor(input_bytes)
    return base64.urlsafe_b64encode(result).decode().rstrip('=')

def decrypt(input_string: str) -> str:
    padding_needed = 4 - (len(input_string) % 4)
    if padding_needed:
        input_string += '=' * padding_needed
    input_bytes = base64.urlsafe_b64decode(input_string)
    result = xor(input_bytes)
    return result.decode()

def xor(input_bytes: bytes) -> bytes:
    return bytes([input_bytes[i] ^ key_bytes[i % len(key_bytes)] for i in range(len(input_bytes))])

def urlsafe_base64(input_string: str) -> str:
    input_bytes = input_string.encode("utf-8")
    base64_bytes = base64.urlsafe_b64encode(input_bytes)
    base64_string = base64_bytes.decode("utf-8")
    return base64_string

def urlsafe_base64_decode(base64_string: str) -> str:
    padding = '=' * (-len(base64_string) % 4)
    base64_string_padded = base64_string + padding
    base64_bytes = base64_string_padded.encode("utf-8")
    decoded_bytes = base64.urlsafe_b64decode(base64_bytes)
    return decoded_bytes.decode("utf-8")

def load_meta_data() -> dict:
    """Load metadata with caching."""
    cached_meta = get_cached(meta_cache, "meta", expire=86400)  # 24 hours
    if cached_meta:
        return cached_meta
    
    with open(os.path.join(os.path.dirname(__file__), "meta.json"), "r") as f:
        meta = json.load(f)
    set_cached(meta_cache, "meta", meta, expire=86400)
    return meta