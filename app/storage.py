from app.config import settings


def blueprint_public_url(object_key: str) -> str:
    """Build the public URL for a blueprint already stored in the object bucket."""
    base = settings.cloud_storage_public_base_url.rstrip("/")
    key = object_key.lstrip("/")
    return f"{base}/{key}"
