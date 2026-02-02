#!/usr/bin/env python3
"""
Replicate Style Transfer Script

Apply artistic style transfer to images using Replicate models.

Usage:
    python style-transfer.py content.png style.png -o stylized.png
    python style-transfer.py --content-url URL --style-url URL -o stylized.png

Requirements:
    - REPLICATE_API_TOKEN environment variable
    - Python 3.8+
"""

import argparse
import base64
import json
import os
import sys
import time
import urllib.request
import urllib.error
from pathlib import Path


def image_to_data_uri(file_path: str) -> str:
    """Convert image file to data URI."""
    ext = Path(file_path).suffix.lower()
    mime_types = {
        ".png": "image/png",
        ".jpg": "image/jpeg",
        ".jpeg": "image/jpeg",
        ".webp": "image/webp",
    }
    mime_type = mime_types.get(ext, "image/png")

    with open(file_path, "rb") as f:
        data = base64.b64encode(f.read()).decode()

    return f"data:{mime_type};base64,{data}"


def style_transfer(
    content_url: str,
    style_url: str,
    output_path: str,
    style_strength: float = 0.5,
    api_key: str | None = None,
) -> dict:
    """Apply style transfer using Replicate."""

    api_key = api_key or os.environ.get("REPLICATE_API_TOKEN")
    if not api_key:
        return {"success": False, "error": "REPLICATE_API_TOKEN environment variable not set"}

    url = "https://api.replicate.com/v1/predictions"

    # Using a neural style transfer model
    # Note: Model version may change, check Replicate for latest
    payload = {
        "version": "7f178b5b60c5a22097f1f3c5ba7ee4e71b5e3c6d8c5f5d9f1f2f3f4f5f6f7f8f9",  # Placeholder
        "input": {
            "content": content_url,
            "style": style_url,
            "style_weight": style_strength,
        }
    }

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }

    data = json.dumps(payload).encode()

    try:
        req = urllib.request.Request(url, data=data, headers=headers, method="POST")
        with urllib.request.urlopen(req, timeout=30) as response:
            result = json.loads(response.read().decode("utf-8"))

        prediction_id = result.get("id")
        if not prediction_id:
            return {"success": False, "error": "No prediction ID returned"}

        print(f"Prediction ID: {prediction_id}")
        print("Applying style transfer...")

        # Poll for completion
        status_url = f"https://api.replicate.com/v1/predictions/{prediction_id}"
        headers_get = {"Authorization": f"Bearer {api_key}"}
        start_time = time.time()
        timeout = 300  # 5 minutes

        while time.time() - start_time < timeout:
            req = urllib.request.Request(status_url, headers=headers_get, method="GET")
            with urllib.request.urlopen(req, timeout=30) as response:
                status_result = json.loads(response.read().decode("utf-8"))

            status = status_result.get("status")
            print(f"Status: {status}")

            if status == "succeeded":
                output_url = status_result.get("output")
                if output_url:
                    if isinstance(output_url, list):
                        output_url = output_url[0]
                    urllib.request.urlretrieve(output_url, output_path)
                    return {
                        "success": True,
                        "output": output_path,
                        "prediction_id": prediction_id,
                    }
                return {"success": False, "error": "No output URL in result"}

            elif status == "failed":
                error = status_result.get("error", "Unknown error")
                return {"success": False, "error": f"Processing failed: {error}"}

            time.sleep(3)

        return {"success": False, "error": "Timeout waiting for processing"}

    except urllib.error.HTTPError as e:
        error_body = e.read().decode("utf-8")
        return {"success": False, "error": f"API error ({e.code}): {error_body}"}
    except Exception as e:
        return {"success": False, "error": str(e)}


def main():
    parser = argparse.ArgumentParser(
        description="Apply artistic style transfer using Replicate",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
    # Style transfer with local files (converted to data URIs)
    %(prog)s photo.png painting.jpg -o stylized.png

    # Style transfer with URLs
    %(prog)s --content-url https://example.com/photo.png --style-url https://example.com/style.jpg -o stylized.png

    # Adjust style strength
    %(prog)s photo.png painting.jpg -o stylized.png -s 0.8

Style strength:
    - 0.0: Mostly content image
    - 0.5: Balanced (default)
    - 1.0: Mostly style image
        """
    )

    parser.add_argument("content", nargs="?", help="Content image file")
    parser.add_argument("style", nargs="?", help="Style image file")
    parser.add_argument("--content-url", help="Content image URL")
    parser.add_argument("--style-url", help="Style image URL")
    parser.add_argument("-o", "--output", required=True, help="Output file path")
    parser.add_argument(
        "-s", "--strength",
        type=float,
        default=0.5,
        help="Style strength 0-1 (default: 0.5)"
    )
    parser.add_argument("-k", "--api-key", help="Replicate API token")
    parser.add_argument("-v", "--verbose", action="store_true", help="Verbose output")

    args = parser.parse_args()

    # Determine content URL
    if args.content_url:
        content_url = args.content_url
    elif args.content:
        if not os.path.exists(args.content):
            print(f"Error: Content image not found: {args.content}", file=sys.stderr)
            sys.exit(1)
        content_url = image_to_data_uri(args.content)
    else:
        print("Error: Either content file or --content-url required", file=sys.stderr)
        sys.exit(1)

    # Determine style URL
    if args.style_url:
        style_url = args.style_url
    elif args.style:
        if not os.path.exists(args.style):
            print(f"Error: Style image not found: {args.style}", file=sys.stderr)
            sys.exit(1)
        style_url = image_to_data_uri(args.style)
    else:
        print("Error: Either style file or --style-url required", file=sys.stderr)
        sys.exit(1)

    result = style_transfer(
        content_url=content_url,
        style_url=style_url,
        output_path=args.output,
        style_strength=args.strength,
        api_key=args.api_key,
    )

    if result["success"]:
        print(f"Saved: {result['output']}")
        if args.verbose:
            print(f"Prediction ID: {result['prediction_id']}")
        sys.exit(0)
    else:
        print(f"Error: {result['error']}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
