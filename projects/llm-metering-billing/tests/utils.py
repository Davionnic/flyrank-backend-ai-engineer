import time
import hmac
import hashlib
import json
from app.config import settings


def generate_stripe_signature_header(payload_bytes: bytes, secret: str = None) -> str:
    webhook_secret = secret or settings.stripe_webhook_secret
    timestamp = int(time.time())
    signed_payload = f"{timestamp}.".encode("utf-8") + payload_bytes
    signature = hmac.new(webhook_secret.encode("utf-8"), signed_payload, hashlib.sha256).hexdigest()
    return f"t={timestamp},v1={signature}"

