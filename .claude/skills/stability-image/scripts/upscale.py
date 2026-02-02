#!/usr/bin/env python3
"""
Stability AI Image Upscale Script

Upscale images using Stability AI's upscale endpoints.

Usage:
    python upscale.py input.png -o upscaled.png
    python upscale.py input.png -o upscaled.png --mode creative --prompt "enhance details"
    python upscale.py input.png -o upscaled.png --mode fast

Requirements:
    - STABILITY_API_KEY environment variable
    - Python 3.8+
"""

import argparse
import base64
import json
import os
import sys
import urllib.request
import urllib.error
from pathlib import Path


def upscale_image(
    image_path: str,
    output_path: str,
    mode: str = "fast",
    prompt: str | None = None,
    creativity: float = 0.3,
    output_format: str = "png",
    api_key: str | None = None,
) -> dict:
    """Upscale an image using Stability AI."""

    api_key = api_key or os.environ.get("STABILITY_API_KEY")
    if not api_key:
        return {"success": False, "error": "STABILITY_API_KEY environment variable not set"}

    if not os.path.exists(image_path):
        return {"success": False, "error": f"Image not found: {image_path}"}

    # Choose endpoint based on mode
    if mode == "creative":
        url = "https://api.stability.ai/v2beta/stable-image/upscale/creative"
    else:
        url = "https://api.stability.ai/v2beta/stable-image/upscale/fast"

    # Build multipart form data
    boundary = "----WebKitFormBoundary7MA4YWxkTrZu0gW"

    with open(image_path, "rb") as f:
        image_data = f.read()

    # Build form data
    body_parts = []

    # Add image file
    body_parts.append(f"--{boundary}".encode())
    body_parts.append(b'Content-Disposition: form-data; name="image"; filename="image.png"')
    body_parts.append(b"Content-Type: image/png")
    body_parts.append(b"")
    body_parts.append(image_data)

    # Add output format
    body_parts.append(f"--{boundary}".encode())
    body_parts.append(b'Content-Disposition: form-data; name="output_format"')
    body_parts.append(b"")
    body_parts.append(output_format.encode())

    # Add creative mode specific params
    if mode == "creative":
        if prompt:
            body_parts.append(f"--{boundary}".encode())
            body_parts.append(b'Content-Disposition: form-data; name="prompt"')
            body_parts.append(b"")
            body_parts.append(prompt.encode())

        body_parts.append(f"--{boundary}".encode())
        body_parts.append(b'Content-Disposition: form-data; name="creativity"')
        body_parts.append(b"")
        body_parts.append(str(creativity).encode())

    body_parts.append(f"--{boundary}--".encode())
    body_parts.append(b"")

    body = b"\r\n".join(body_parts)

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Accept": "image/*",
        "Content-Type": f"multipart/form-data; boundary={boundary}",
    }

    try:
        req = urllib.request.Request(url, data=body, headers=headers, method="POST")
        with urllib.request.urlopen(req, timeout=120) as response:
            # Save the image
            with open(output_path, "wb") as f:
                f.write(response.read())

            return {
                "success": True,
                "output": output_path,
                "mode": mode,
            }
    except urllib.error.HTTPError as e:
        error_body = e.read().decode("utf-8")
        try:
            error_json = json.loads(error_body)
            error_msg = error_json.get("message", error_body)
        except json.JSONDecodeError:
            error_msg = error_body
        return {"success": False, "error": f"API error ({e.code}): {error_msg}"}
    except Exception as e:
        return {"success": False, "error": str(e)}


def main():
    parser = argparse.ArgumentParser(
        description="Upscale images using Stability AI",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
    # Fast upscale (4x)
    %(prog)s input.png -o upscaled.png

    # Creative upscale with prompt
    %(prog)s input.png -o upscaled.png --mode creative --prompt "enhance details"

    # Creative upscale with custom creativity
    %(prog)s input.png -o upscaled.png --mode creative -c 0.5
        """
    )

    parser.add_argument("image", help="Input image path")
    parser.add_argument("-o", "--output", required=True, help="Output file path")
    parser.add_argument(
        "-m", "--mode",
        choices=["fast", "creative"],
        default="fast",
        help="Upscale mode (default: fast)"
    )
    parser.add_argument("-p", "--prompt", help="Enhancement prompt (creative mode only)")
    parser.add_argument(
        "-c", "--creativity",
        type=float,
        default=0.3,
        help="Creativity level 0-1 (creative mode only, default: 0.3)"
    )
    parser.add_argument(
        "-f", "--format",
        choices=["png", "jpeg", "webp"],
        default="png",
        help="Output format (default: png)"
    )
    parser.add_argument("-k", "--api-key", help="Stability API key")
    parser.add_argument("-v", "--verbose", action="store_true", help="Verbose output")

    args = parser.parse_args()

    print(f"Upscaling image ({args.mode} mode)...")

    result = upscale_image(
        image_path=args.image,
        output_path=args.output,
        mode=args.mode,
        prompt=args.prompt,
        creativity=args.creativity,
        output_format=args.format,
        api_key=args.api_key,
    )

    if result["success"]:
        print(f"Saved: {result['output']}")
        if args.verbose:
            print(f"Mode: {result['mode']}")
        sys.exit(0)
    else:
        print(f"Error: {result['error']}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
