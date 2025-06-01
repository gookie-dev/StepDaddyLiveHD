import os
import base64
import json
from diskcache import Cache
from typing import Any, Optional
import aiofiles

# Inicializar directorios de caché
cache_dir = os.path.join(os.path.dirname(__file__), ".cache")
logo_cache_dir = os.path.join(os.path.dirname(__file__), ".logo-cache")

# Crear directorios si no existen
os.makedirs(cache_dir, exist_ok=True)
os.makedirs(logo_cache_dir, exist_ok=True)

meta_cache = Cache(os.path.join(cache_dir, "meta"))
stream_cache = Cache(os.path.join(cache_dir, "stream"))
key_cache = Cache(os.path.join(cache_dir, "key"))

key_bytes = os.urandom(64)

def get_cached(cache: Cache, key: str) -> Optional[Any]:
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
    try:
        padding_needed = 4 - (len(input_string) % 4)
        if padding_needed:
            input_string += '=' * padding_needed
        input_bytes = base64.urlsafe_b64decode(input_string)
        result = xor(input_bytes)
        return result.decode('utf-8', errors='ignore')
    except UnicodeDecodeError:
        # If UTF-8 decoding fails, return the raw string
        return input_string

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

def get_meta_data() -> dict:
    """Load metadata with caching."""
    cached_meta = get_cached(meta_cache, "meta")
    if cached_meta:
        return cached_meta
    
    meta_path = os.path.join(os.path.dirname(__file__), "meta.json")
    with open(meta_path, "r") as f:
        meta = json.load(f)
    set_cached(meta_cache, "meta", meta, expire=86400)  # 24 hours
    return meta

async def cache_logo(url: str, file_name: str) -> str:
    """Cache a logo file and return its path."""
    cache_path = os.path.join(logo_cache_dir, file_name)
    
    # Si ya existe en caché, retornar la ruta
    if os.path.exists(cache_path):
        return cache_path
        
    try:
        async with aiofiles.open(cache_path, 'wb') as f:
            await f.write(b'')  # Create empty file to mark as being downloaded
            return cache_path
    except Exception as e:
        if os.path.exists(cache_path):
            os.remove(cache_path)
        raise e