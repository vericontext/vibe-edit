#!/usr/bin/env python3
"""
Kling AI Video Extension Script

Extend existing videos using Kling AI's video-extend endpoint.

Usage:
    python extend.py VIDEO_ID -o extended.mp4
    python extend.py VIDEO_ID -o extended.mp4 --prompt "continue the scene"

Requirements:
    - KLING_API_KEY environment variable (format: ACCESS_KEY:SECRET_KEY)
    - Python 3.8+
"""

import argparse
import base64
import hashlib
import hmac
import json
import os
import sys
import time
import urllib.request
import urllib.error


def generate_jwt(access_key: str, secret_key: str) -> str:
    """Generate JWT token for Kling API authentication."""
    now = int(time.time())

    header = {"alg": "HS256", "typ": "JWT"}
    payload = {"iss": access_key, "exp": now + 1800, "nbf": now - 5}

    def b64_encode(data: bytes) -> str:
        return base64.urlsafe_b64encode(data).rstrip(b"=").decode()

    header_b64 = b64_encode(json.dumps(header).encode())
    payload_b64 = b64_encode(json.dumps(payload).encode())

    signature = hmac.new(
        secret_key.encode(),
        f"{header_b64}.{payload_b64}".encode(),
        hashlib.sha256
    ).digest()
    signature_b64 = b64_encode(signature)

    return f"{header_b64}.{payload_b64}.{signature_b64}"


def extend_video(
    video_id: str,
    output_path: str,
    prompt: str | None = None,
    duration: str = "5",
    api_key: str | None = None,
) -> dict:
    """Extend a video using Kling AI."""

    api_key = api_key or os.environ.get("KLING_API_KEY")
    if not api_key:
        return {"success": False, "error": "KLING_API_KEY environment variable not set"}

    if ":" not in api_key:
        return {"success": False, "error": "KLING_API_KEY must be in format ACCESS_KEY:SECRET_KEY"}

    access_key, secret_key = api_key.split(":", 1)
    token = generate_jwt(access_key, secret_key)

    # Create extension request
    url = "https://api.klingai.com/v1/videos/video-extend"

    payload = {
        "video_id": video_id,
        "duration": duration,
    }

    if prompt:
        payload["prompt"] = prompt

    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
    }

    data = json.dumps(payload).encode()

    try:
        req = urllib.request.Request(url, data=data, headers=headers, method="POST")
        with urllib.request.urlopen(req, timeout=30) as response:
            result = json.loads(response.read().decode("utf-8"))

        if result.get("code") != 0:
            return {"success": False, "error": result.get("message", "Unknown error")}

        task_id = result.get("data", {}).get("task_id")
        if not task_id:
            return {"success": False, "error": "No task ID returned"}

        print(f"Task ID: {task_id}")
        print("Waiting for video extension...")

        # Poll for completion
        status_url = f"https://api.klingai.com/v1/videos/video-extend/{task_id}"
        start_time = time.time()
        timeout = 600  # 10 minutes

        while time.time() - start_time < timeout:
            token = generate_jwt(access_key, secret_key)  # Refresh token
            headers["Authorization"] = f"Bearer {token}"

            req = urllib.request.Request(status_url, headers=headers, method="GET")
            with urllib.request.urlopen(req, timeout=30) as response:
                status_result = json.loads(response.read().decode("utf-8"))

            task_status = status_result.get("data", {}).get("task_status")
            print(f"Status: {task_status}")

            if task_status == "succeed":
                videos = status_result.get("data", {}).get("task_result", {}).get("videos", [])
                if videos:
                    video_url = videos[0].get("url")
                    if video_url:
                        # Download video
                        urllib.request.urlretrieve(video_url, output_path)
                        return {
                            "success": True,
                            "output": output_path,
                            "task_id": task_id,
                            "duration": videos[0].get("duration"),
                        }
                return {"success": False, "error": "No video URL in result"}

            elif task_status == "failed":
                return {"success": False, "error": "Video extension failed"}

            time.sleep(5)

        return {"success": False, "error": "Timeout waiting for video extension"}

    except urllib.error.HTTPError as e:
        error_body = e.read().decode("utf-8")
        return {"success": False, "error": f"API error ({e.code}): {error_body}"}
    except Exception as e:
        return {"success": False, "error": str(e)}


def main():
    parser = argparse.ArgumentParser(
        description="Extend videos using Kling AI",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
    # Extend a video by 5 seconds
    %(prog)s video123 -o extended.mp4

    # Extend with a prompt
    %(prog)s video123 -o extended.mp4 --prompt "continue the dramatic scene"

    # Extend by 10 seconds
    %(prog)s video123 -o extended.mp4 -d 10

Note:
    The video_id is obtained from a previous video generation task result.
        """
    )

    parser.add_argument("video_id", help="Video ID from previous generation")
    parser.add_argument("-o", "--output", required=True, help="Output file path")
    parser.add_argument("-p", "--prompt", help="Prompt for extended content")
    parser.add_argument(
        "-d", "--duration",
        choices=["5", "10"],
        default="5",
        help="Extension duration in seconds (default: 5)"
    )
    parser.add_argument("-k", "--api-key", help="Kling API key (ACCESS_KEY:SECRET_KEY)")
    parser.add_argument("-v", "--verbose", action="store_true", help="Verbose output")

    args = parser.parse_args()

    result = extend_video(
        video_id=args.video_id,
        output_path=args.output,
        prompt=args.prompt,
        duration=args.duration,
        api_key=args.api_key,
    )

    if result["success"]:
        print(f"Saved: {result['output']}")
        if args.verbose:
            print(f"Task ID: {result['task_id']}")
            if result.get("duration"):
                print(f"Duration: {result['duration']}s")
        sys.exit(0)
    else:
        print(f"Error: {result['error']}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
