#!/usr/bin/env python3
"""
Stability AI Background Removal Script

Remove backgrounds from images using Stability AI.

Usage:
    python remove-bg.py input.png -o output.png
    python remove-bg.py photo.jpg -o transparent.png

Requirements:
    - STABILITY_API_KEY environment variable
    - Python 3.8+
"""

import argparse
import json
import os
import sys
import urllib.request
import urllib.error
from pathlib import Path


def remove_background(
    image_path: str,
    output_path: str,
    output_format: str = "png",
    api_key: str | None = None,
) -> dict:
    """Remove background from an image using Stability AI."""

    api_key = api_key or os.environ.get("STABILITY_API_KEY")
    if not api_key:
        return {"success": False, "error": "STABILITY_API_KEY environment variable not set"}

    if not os.path.exists(image_path):
        return {"success": False, "error": f"Image not found: {image_path}"}

    url = "https://api.stability.ai/v2beta/stable-image/edit/remove-background"

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
        with urllib.request.urlopen(req, timeout=60) as response:
            # Save the image
            with open(output_path, "wb") as f:
                f.write(response.read())

            return {
                "success": True,
                "output": output_path,
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
        description="Remove background from images using Stability AI",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
    # Remove background
    %(prog)s photo.png -o transparent.png

    # Save as WebP
    %(prog)s photo.jpg -o output.webp -f webp
        """
    )

    parser.add_argument("image", help="Input image path")
    parser.add_argument("-o", "--output", required=True, help="Output file path")
    parser.add_argument(
        "-f", "--format",
        choices=["png", "webp"],
        default="png",
        help="Output format (default: png)"
    )
    parser.add_argument("-k", "--api-key", help="Stability API key")

    args = parser.parse_args()

    print("Removing background...")

    result = remove_background(
        image_path=args.image,
        output_path=args.output,
        output_format=args.format,
        api_key=args.api_key,
    )

    if result["success"]:
        print(f"Saved: {result['output']}")
        sys.exit(0)
    else:
        print(f"Error: {result['error']}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
