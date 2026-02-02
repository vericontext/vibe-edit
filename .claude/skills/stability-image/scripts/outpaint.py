#!/usr/bin/env python3
"""
Stability AI Outpaint Script

Extend image boundaries using Stability AI's outpaint endpoint.

Usage:
    python outpaint.py input.png -o wider.png --left 200 --right 200
    python outpaint.py photo.jpg -o taller.png --up 300 --down 300 -p "sky with clouds"

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


def outpaint(
    image_path: str,
    output_path: str,
    left: int = 0,
    right: int = 0,
    up: int = 0,
    down: int = 0,
    prompt: str | None = None,
    creativity: float = 0.5,
    output_format: str = "png",
    api_key: str | None = None,
) -> dict:
    """Extend image boundaries using Stability AI outpaint."""

    api_key = api_key or os.environ.get("STABILITY_API_KEY")
    if not api_key:
        return {"success": False, "error": "STABILITY_API_KEY environment variable not set"}

    if not os.path.exists(image_path):
        return {"success": False, "error": f"Image not found: {image_path}"}

    if left == 0 and right == 0 and up == 0 and down == 0:
        return {"success": False, "error": "At least one direction must be specified (--left, --right, --up, --down)"}

    url = "https://api.stability.ai/v2beta/stable-image/edit/outpaint"

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

    # Add direction values
    if left > 0:
        body_parts.append(f"--{boundary}".encode())
        body_parts.append(b'Content-Disposition: form-data; name="left"')
        body_parts.append(b"")
        body_parts.append(str(left).encode())

    if right > 0:
        body_parts.append(f"--{boundary}".encode())
        body_parts.append(b'Content-Disposition: form-data; name="right"')
        body_parts.append(b"")
        body_parts.append(str(right).encode())

    if up > 0:
        body_parts.append(f"--{boundary}".encode())
        body_parts.append(b'Content-Disposition: form-data; name="up"')
        body_parts.append(b"")
        body_parts.append(str(up).encode())

    if down > 0:
        body_parts.append(f"--{boundary}".encode())
        body_parts.append(b'Content-Disposition: form-data; name="down"')
        body_parts.append(b"")
        body_parts.append(str(down).encode())

    # Add prompt if provided
    if prompt:
        body_parts.append(f"--{boundary}".encode())
        body_parts.append(b'Content-Disposition: form-data; name="prompt"')
        body_parts.append(b"")
        body_parts.append(prompt.encode())

    # Add creativity
    body_parts.append(f"--{boundary}".encode())
    body_parts.append(b'Content-Disposition: form-data; name="creativity"')
    body_parts.append(b"")
    body_parts.append(str(creativity).encode())

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
        with urllib.request.urlopen(req, timeout=120) as response:
            # Save the image
            with open(output_path, "wb") as f:
                f.write(response.read())

            return {
                "success": True,
                "output": output_path,
                "extensions": {
                    "left": left,
                    "right": right,
                    "up": up,
                    "down": down,
                },
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
        description="Extend image boundaries using Stability AI outpaint",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
    # Extend left and right (make wider)
    %(prog)s photo.png -o wider.png --left 200 --right 200

    # Extend up and down (make taller)
    %(prog)s photo.png -o taller.png --up 300 --down 300

    # Extend with prompt guidance
    %(prog)s landscape.png -o extended.png --right 500 -p "continue the mountain range"

    # High creativity outpaint
    %(prog)s scene.png -o creative.png --left 400 --right 400 -c 0.8
        """
    )

    parser.add_argument("image", help="Input image path")
    parser.add_argument("-o", "--output", required=True, help="Output file path")
    parser.add_argument("--left", type=int, default=0, help="Pixels to extend left (0-2000)")
    parser.add_argument("--right", type=int, default=0, help="Pixels to extend right (0-2000)")
    parser.add_argument("--up", type=int, default=0, help="Pixels to extend up (0-2000)")
    parser.add_argument("--down", type=int, default=0, help="Pixels to extend down (0-2000)")
    parser.add_argument("-p", "--prompt", help="Description for extended area")
    parser.add_argument(
        "-c", "--creativity",
        type=float,
        default=0.5,
        help="Creativity level 0-1 (default: 0.5)"
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

    print("Extending image...")

    result = outpaint(
        image_path=args.image,
        output_path=args.output,
        left=args.left,
        right=args.right,
        up=args.up,
        down=args.down,
        prompt=args.prompt,
        creativity=args.creativity,
        output_format=args.format,
        api_key=args.api_key,
    )

    if result["success"]:
        print(f"Saved: {result['output']}")
        if args.verbose:
            ext = result["extensions"]
            print(f"Extensions: L={ext['left']}, R={ext['right']}, U={ext['up']}, D={ext['down']}")
        sys.exit(0)
    else:
        print(f"Error: {result['error']}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
