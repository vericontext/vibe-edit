#!/usr/bin/env python3
"""
Stability AI Search & Replace Script

Replace objects in images using Stability AI's search-and-replace endpoint.

Usage:
    python replace.py input.png "red sports car" "blue car" -o output.png
    python replace.py photo.jpg "golden retriever" "cat" -o output.jpg

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


def search_and_replace(
    image_path: str,
    prompt: str,
    search_prompt: str,
    output_path: str,
    negative_prompt: str | None = None,
    seed: int | None = None,
    output_format: str = "png",
    api_key: str | None = None,
) -> dict:
    """Search and replace objects in an image using Stability AI."""

    api_key = api_key or os.environ.get("STABILITY_API_KEY")
    if not api_key:
        return {"success": False, "error": "STABILITY_API_KEY environment variable not set"}

    if not os.path.exists(image_path):
        return {"success": False, "error": f"Image not found: {image_path}"}

    url = "https://api.stability.ai/v2beta/stable-image/edit/search-and-replace"

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

    # Add prompt (what to replace with)
    body_parts.append(f"--{boundary}".encode())
    body_parts.append(b'Content-Disposition: form-data; name="prompt"')
    body_parts.append(b"")
    body_parts.append(prompt.encode())

    # Add search prompt (what to find)
    body_parts.append(f"--{boundary}".encode())
    body_parts.append(b'Content-Disposition: form-data; name="search_prompt"')
    body_parts.append(b"")
    body_parts.append(search_prompt.encode())

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
                "search": search_prompt,
                "replace": prompt,
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
        description="Search and replace objects in images using Stability AI",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
    # Replace blue car with red sports car
    %(prog)s photo.png "red sports car" "blue car" -o replaced.png

    # Replace dog with cat
    %(prog)s photo.jpg "fluffy cat" "dog" -o output.jpg

    # Replace background object
    %(prog)s scene.png "modern skyscraper" "old building" -o updated.png
        """
    )

    parser.add_argument("image", help="Input image path")
    parser.add_argument("prompt", help="What to replace with (new object)")
    parser.add_argument("search", help="What to find (object to replace)")
    parser.add_argument("-o", "--output", required=True, help="Output file path")
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

    print(f"Replacing '{args.search}' with '{args.prompt}'...")

    result = search_and_replace(
        image_path=args.image,
        prompt=args.prompt,
        search_prompt=args.search,
        output_path=args.output,
        negative_prompt=args.negative,
        seed=args.seed,
        output_format=args.format,
        api_key=args.api_key,
    )

    if result["success"]:
        print(f"Saved: {result['output']}")
        if args.verbose:
            print(f"Search: {result['search']}")
            print(f"Replace: {result['replace']}")
        sys.exit(0)
    else:
        print(f"Error: {result['error']}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
