#!/usr/bin/env python3
"""
Stability AI Image-to-Image Script

Transform images using Stability AI's SD3 model.

Usage:
    python img2img.py input.png "transform to watercolor painting" -o output.png
    python img2img.py photo.jpg "make it look like anime" -o anime.png --strength 0.8

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


def image_to_image(
    image_path: str,
    prompt: str,
    output_path: str,
    strength: float = 0.7,
    negative_prompt: str | None = None,
    seed: int | None = None,
    output_format: str = "png",
    api_key: str | None = None,
) -> dict:
    """Transform an image using Stability AI SD3."""

    api_key = api_key or os.environ.get("STABILITY_API_KEY")
    if not api_key:
        return {"success": False, "error": "STABILITY_API_KEY environment variable not set"}

    if not os.path.exists(image_path):
        return {"success": False, "error": f"Image not found: {image_path}"}

    # SD3 endpoint supports image-to-image with mode parameter
    url = "https://api.stability.ai/v2beta/stable-image/generate/sd3"

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

    # Add mode
    body_parts.append(f"--{boundary}".encode())
    body_parts.append(b'Content-Disposition: form-data; name="mode"')
    body_parts.append(b"")
    body_parts.append(b"image-to-image")

    # Add prompt
    body_parts.append(f"--{boundary}".encode())
    body_parts.append(b'Content-Disposition: form-data; name="prompt"')
    body_parts.append(b"")
    body_parts.append(prompt.encode())

    # Add strength
    body_parts.append(f"--{boundary}".encode())
    body_parts.append(b'Content-Disposition: form-data; name="strength"')
    body_parts.append(b"")
    body_parts.append(str(strength).encode())

    # Add output format
    body_parts.append(f"--{boundary}".encode())
    body_parts.append(b'Content-Disposition: form-data; name="output_format"')
    body_parts.append(b"")
    body_parts.append(output_format.encode())

    # Add optional negative prompt
    if negative_prompt:
        body_parts.append(f"--{boundary}".encode())
        body_parts.append(b'Content-Disposition: form-data; name="negative_prompt"')
        body_parts.append(b"")
        body_parts.append(negative_prompt.encode())

    # Add optional seed
    if seed is not None:
        body_parts.append(f"--{boundary}".encode())
        body_parts.append(b'Content-Disposition: form-data; name="seed"')
        body_parts.append(b"")
        body_parts.append(str(seed).encode())

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
                "strength": strength,
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
        description="Transform images using Stability AI SD3",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
    # Transform to watercolor
    %(prog)s photo.png "transform to watercolor painting" -o watercolor.png

    # Anime style with high strength
    %(prog)s photo.jpg "anime style portrait" -o anime.png --strength 0.9

    # Subtle enhancement
    %(prog)s photo.png "enhance lighting and colors" -o enhanced.png --strength 0.3
        """
    )

    parser.add_argument("image", help="Input image path")
    parser.add_argument("prompt", help="Transformation prompt")
    parser.add_argument("-o", "--output", required=True, help="Output file path")
    parser.add_argument(
        "-s", "--strength",
        type=float,
        default=0.7,
        help="Transformation strength 0-1 (default: 0.7)"
    )
    parser.add_argument("-n", "--negative", help="Negative prompt")
    parser.add_argument("--seed", type=int, help="Random seed")
    parser.add_argument(
        "-f", "--format",
        choices=["png", "jpeg", "webp"],
        default="png",
        help="Output format (default: png)"
    )
    parser.add_argument("-k", "--api-key", help="Stability API key")
    parser.add_argument("-v", "--verbose", action="store_true", help="Verbose output")

    args = parser.parse_args()

    print("Transforming image...")

    result = image_to_image(
        image_path=args.image,
        prompt=args.prompt,
        output_path=args.output,
        strength=args.strength,
        negative_prompt=args.negative,
        seed=args.seed,
        output_format=args.format,
        api_key=args.api_key,
    )

    if result["success"]:
        print(f"Saved: {result['output']}")
        if args.verbose:
            print(f"Strength: {result['strength']}")
        sys.exit(0)
    else:
        print(f"Error: {result['error']}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
