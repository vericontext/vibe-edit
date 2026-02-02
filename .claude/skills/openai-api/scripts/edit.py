#!/usr/bin/env python3
"""
OpenAI DALL-E Image Edit Script

Edit images using DALL-E 2's inpainting capability.

Usage:
    python edit.py image.png mask.png "add a sunset sky" -o edited.png
    python edit.py image.png "add a cat on the table" -o edited.png --generate-mask

Requirements:
    - OPENAI_API_KEY environment variable
    - Python 3.8+
    - Image must be square PNG, max 4MB
    - Mask: transparent areas will be edited
"""

import argparse
import base64
import json
import os
import sys
import urllib.request
import urllib.error
from pathlib import Path


def create_simple_mask(width: int, height: int) -> bytes:
    """Create a simple transparent PNG mask (all editable)."""
    # Minimal transparent PNG
    # This is a placeholder - for real use, you'd want proper mask generation
    import struct
    import zlib

    def png_chunk(chunk_type, data):
        chunk_len = len(data)
        chunk = struct.pack('>I', chunk_len) + chunk_type + data
        checksum = zlib.crc32(chunk_type + data) & 0xffffffff
        return chunk + struct.pack('>I', checksum)

    signature = b'\x89PNG\r\n\x1a\n'

    # IHDR
    ihdr_data = struct.pack('>IIBBBBB', width, height, 8, 6, 0, 0, 0)
    ihdr = png_chunk(b'IHDR', ihdr_data)

    # IDAT - transparent pixels
    raw_data = b''
    for _ in range(height):
        raw_data += b'\x00'  # filter byte
        for _ in range(width):
            raw_data += b'\x00\x00\x00\x00'  # RGBA = transparent

    compressed = zlib.compress(raw_data)
    idat = png_chunk(b'IDAT', compressed)

    # IEND
    iend = png_chunk(b'IEND', b'')

    return signature + ihdr + idat + iend


def edit_image(
    image_path: str,
    prompt: str,
    output_path: str,
    mask_path: str | None = None,
    size: str = "1024x1024",
    n: int = 1,
    api_key: str | None = None,
) -> dict:
    """Edit an image using DALL-E 2."""

    api_key = api_key or os.environ.get("OPENAI_API_KEY")
    if not api_key:
        return {"success": False, "error": "OPENAI_API_KEY environment variable not set"}

    if not os.path.exists(image_path):
        return {"success": False, "error": f"Image not found: {image_path}"}

    if mask_path and not os.path.exists(mask_path):
        return {"success": False, "error": f"Mask not found: {mask_path}"}

    url = "https://api.openai.com/v1/images/edits"

    # Build multipart form data
    boundary = "----WebKitFormBoundary7MA4YWxkTrZu0gW"

    # Read image
    with open(image_path, "rb") as f:
        image_data = f.read()

    body_parts = []

    # Add image
    body_parts.append(f"--{boundary}".encode())
    body_parts.append(b'Content-Disposition: form-data; name="image"; filename="image.png"')
    body_parts.append(b"Content-Type: image/png")
    body_parts.append(b"")
    body_parts.append(image_data)

    # Add mask if provided
    if mask_path:
        with open(mask_path, "rb") as f:
            mask_data = f.read()
        body_parts.append(f"--{boundary}".encode())
        body_parts.append(b'Content-Disposition: form-data; name="mask"; filename="mask.png"')
        body_parts.append(b"Content-Type: image/png")
        body_parts.append(b"")
        body_parts.append(mask_data)

    # Add prompt
    body_parts.append(f"--{boundary}".encode())
    body_parts.append(b'Content-Disposition: form-data; name="prompt"')
    body_parts.append(b"")
    body_parts.append(prompt.encode())

    # Add model (DALL-E 2 for edits)
    body_parts.append(f"--{boundary}".encode())
    body_parts.append(b'Content-Disposition: form-data; name="model"')
    body_parts.append(b"")
    body_parts.append(b"dall-e-2")

    # Add size
    body_parts.append(f"--{boundary}".encode())
    body_parts.append(b'Content-Disposition: form-data; name="size"')
    body_parts.append(b"")
    body_parts.append(size.encode())

    # Add n
    body_parts.append(f"--{boundary}".encode())
    body_parts.append(b'Content-Disposition: form-data; name="n"')
    body_parts.append(b"")
    body_parts.append(str(n).encode())

    # Add response format
    body_parts.append(f"--{boundary}".encode())
    body_parts.append(b'Content-Disposition: form-data; name="response_format"')
    body_parts.append(b"")
    body_parts.append(b"url")

    body_parts.append(f"--{boundary}--".encode())
    body_parts.append(b"")

    body = b"\r\n".join(body_parts)

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": f"multipart/form-data; boundary={boundary}",
    }

    try:
        req = urllib.request.Request(url, data=body, headers=headers, method="POST")
        with urllib.request.urlopen(req, timeout=120) as response:
            result = json.loads(response.read().decode("utf-8"))

        images = result.get("data", [])
        if not images:
            return {"success": False, "error": "No images in response"}

        # Download the first image
        image_url = images[0].get("url")
        if image_url:
            urllib.request.urlretrieve(image_url, output_path)
            return {
                "success": True,
                "output": output_path,
                "revised_prompt": images[0].get("revised_prompt"),
            }

        return {"success": False, "error": "No image URL in response"}

    except urllib.error.HTTPError as e:
        error_body = e.read().decode("utf-8")
        try:
            error_json = json.loads(error_body)
            error_msg = error_json.get("error", {}).get("message", error_body)
        except json.JSONDecodeError:
            error_msg = error_body
        return {"success": False, "error": f"API error ({e.code}): {error_msg}"}
    except Exception as e:
        return {"success": False, "error": str(e)}


def main():
    parser = argparse.ArgumentParser(
        description="Edit images using DALL-E 2 inpainting",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
    # Edit with mask (transparent areas will be modified)
    %(prog)s image.png mask.png "add a sunset sky" -o edited.png

    # Edit without explicit mask
    %(prog)s image.png "add a mountain in the background" -o edited.png

Requirements:
    - Image must be square PNG, max 4MB
    - Mask must have transparent areas where edits should occur
    - Only DALL-E 2 supports image editing (not DALL-E 3)

Available sizes:
    - 256x256
    - 512x512
    - 1024x1024 (default)
        """
    )

    parser.add_argument("image", help="Input image path (square PNG)")
    parser.add_argument("mask_or_prompt", help="Mask image path OR prompt if no mask")
    parser.add_argument("prompt", nargs="?", help="Edit prompt (required if mask provided)")
    parser.add_argument("-o", "--output", required=True, help="Output file path")
    parser.add_argument(
        "-s", "--size",
        choices=["256x256", "512x512", "1024x1024"],
        default="1024x1024",
        help="Output size (default: 1024x1024)"
    )
    parser.add_argument("-n", "--num", type=int, default=1, help="Number of images")
    parser.add_argument("-k", "--api-key", help="OpenAI API key")
    parser.add_argument("-v", "--verbose", action="store_true", help="Verbose output")

    args = parser.parse_args()

    # Determine if mask_or_prompt is a file path or prompt
    if os.path.exists(args.mask_or_prompt):
        # It's a mask file
        mask_path = args.mask_or_prompt
        if not args.prompt:
            print("Error: Prompt required when using mask", file=sys.stderr)
            sys.exit(1)
        prompt = args.prompt
    else:
        # It's a prompt, no mask
        mask_path = None
        prompt = args.mask_or_prompt

    print("Editing image...")

    result = edit_image(
        image_path=args.image,
        prompt=prompt,
        output_path=args.output,
        mask_path=mask_path,
        size=args.size,
        n=args.num,
        api_key=args.api_key,
    )

    if result["success"]:
        print(f"Saved: {result['output']}")
        if args.verbose and result.get("revised_prompt"):
            print(f"Revised prompt: {result['revised_prompt']}")
        sys.exit(0)
    else:
        print(f"Error: {result['error']}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
