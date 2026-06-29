"""Prepare screenshot bytes for vision models — preserve quality, avoid tiny inputs."""
from __future__ import annotations

import io

from PIL import Image, ImageOps

MIN_LONG_EDGE = 1024
MAX_LONG_EDGE = 2560
JPEG_QUALITY = 92


def prepare_vision_image(image_bytes: bytes) -> tuple[bytes, str]:
    """Return (jpeg_bytes, mime). Upscale small crops; only downscale if huge."""
    with Image.open(io.BytesIO(image_bytes)) as img:
        img = ImageOps.exif_transpose(img)
        if img.mode not in ("RGB", "L"):
            img = img.convert("RGB")

        w, h = img.size
        long_edge = max(w, h)

        if long_edge < MIN_LONG_EDGE:
            scale = MIN_LONG_EDGE / long_edge
            img = img.resize((int(w * scale), int(h * scale)), Image.Resampling.LANCZOS)
        elif long_edge > MAX_LONG_EDGE:
            scale = MAX_LONG_EDGE / long_edge
            img = img.resize((int(w * scale), int(h * scale)), Image.Resampling.LANCZOS)

        out = io.BytesIO()
        img.save(out, format="JPEG", quality=JPEG_QUALITY, optimize=True)
        return out.getvalue(), "image/jpeg"
