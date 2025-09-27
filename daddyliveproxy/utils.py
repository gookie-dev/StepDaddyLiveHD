import base64
import binascii
import json
import os
import re
from typing import Any, Dict

key_bytes = os.urandom(64)


def encrypt(value: str) -> str:
    """Return an obfuscated, URL-safe representation of ``value``."""

    input_bytes = value.encode("utf-8")
    result = xor(input_bytes)
    return base64.urlsafe_b64encode(result).decode("utf-8").rstrip("=")


def decrypt(value: str) -> str:
    """Reverse :func:`encrypt` and return the original string."""

    padding_needed = (-len(value)) % 4
    padded = value + ("=" * padding_needed)
    try:
        input_bytes = base64.b64decode(
            padded,
            altchars=b"-_",
            validate=True,
        )
    except (ValueError, binascii.Error) as exc:
        raise ValueError("Encrypted value is not valid base64") from exc
    result = xor(input_bytes)
    return result.decode("utf-8")


def xor(input_bytes: bytes) -> bytes:
    """Apply a repeating XOR mask to ``input_bytes``."""

    return bytes(
        input_bytes[i] ^ key_bytes[i % len(key_bytes)] for i in range(len(input_bytes))
    )


def urlsafe_base64(value: str) -> str:
    """Encode ``value`` as a URL-safe base64 string."""

    input_bytes = value.encode("utf-8")
    return base64.urlsafe_b64encode(input_bytes).decode("utf-8")


def urlsafe_base64_decode(value: str) -> str:
    """Decode a URL-safe base64 encoded string."""

    padding = "=" * (-len(value) % 4)
    try:
        decoded_bytes = base64.b64decode(
            (value + padding).encode("utf-8"),
            altchars=b"-_",
            validate=True,
        )
    except (ValueError, binascii.Error) as exc:
        raise ValueError("Input is not valid base64") from exc
    return decoded_bytes.decode("utf-8")


def extract_and_decode_var(var_name: str, response: str) -> str:
    """Extract an ``atob`` encoded JavaScript variable from ``response``."""

    pattern = rf'var\s+{re.escape(var_name)}\s*=\s*atob\("([^"]+)"\);'
    matches = re.findall(pattern, response)
    if not matches:
        raise ValueError(f"Variable '{var_name}' not found in response")
    try:
        return base64.b64decode(matches[-1], validate=True).decode("utf-8")
    except (ValueError, binascii.Error) as exc:
        raise ValueError(f"Variable '{var_name}' is not valid base64") from exc


def decode_bundle(bundle: str) -> Dict[str, Any]:
    """Decode the XJZ bundle returned by the upstream site."""

    try:
        decoded_bundle = base64.b64decode(bundle, validate=True).decode("utf-8")
    except (ValueError, binascii.Error) as exc:
        raise ValueError("Bundle is not valid base64") from exc
    data = json.loads(decoded_bundle)
    decoded: Dict[str, Any] = {}
    for key, value in data.items():
        if isinstance(value, str):
            try:
                pad = "=" * (-len(value) % 4)
                decoded[key] = base64.b64decode(value + pad, validate=True).decode(
                    "utf-8"
                )
            except (ValueError, binascii.Error):
                decoded[key] = value
        else:
            decoded[key] = value
    return decoded
