#!/usr/bin/env python3
"""
Kling AI Task Status Script

Check the status of a Kling AI video generation task.

Usage:
    python status.py TASK_ID
    python status.py TASK_ID --type text2video
    python status.py TASK_ID --type image2video

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


def get_task_status(
    task_id: str,
    task_type: str = "text2video",
    api_key: str | None = None,
) -> dict:
    """Get status of a Kling AI task."""

    api_key = api_key or os.environ.get("KLING_API_KEY")
    if not api_key:
        return {"success": False, "error": "KLING_API_KEY environment variable not set"}

    if ":" not in api_key:
        return {"success": False, "error": "KLING_API_KEY must be in format ACCESS_KEY:SECRET_KEY"}

    access_key, secret_key = api_key.split(":", 1)
    token = generate_jwt(access_key, secret_key)

    # Build URL based on task type
    url = f"https://api.klingai.com/v1/videos/{task_type}/{task_id}"

    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
    }

    try:
        req = urllib.request.Request(url, headers=headers, method="GET")
        with urllib.request.urlopen(req, timeout=30) as response:
            result = json.loads(response.read().decode("utf-8"))

        if result.get("code") != 0:
            return {"success": False, "error": result.get("message", "Unknown error")}

        data = result.get("data", {})
        task_status = data.get("task_status")
        task_result = data.get("task_result", {})

        response_data = {
            "success": True,
            "task_id": task_id,
            "status": task_status,
            "type": task_type,
        }

        if task_status == "succeed":
            videos = task_result.get("videos", [])
            if videos:
                response_data["videos"] = [
                    {
                        "id": v.get("id"),
                        "url": v.get("url"),
                        "duration": v.get("duration"),
                    }
                    for v in videos
                ]

        return response_data

    except urllib.error.HTTPError as e:
        error_body = e.read().decode("utf-8")
        return {"success": False, "error": f"API error ({e.code}): {error_body}"}
    except Exception as e:
        return {"success": False, "error": str(e)}


def main():
    parser = argparse.ArgumentParser(
        description="Check status of Kling AI video generation task",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
    # Check text-to-video task status
    %(prog)s task123

    # Check image-to-video task status
    %(prog)s task123 --type image2video

    # Output as JSON
    %(prog)s task123 --json

Status values:
    - submitted: Task submitted
    - processing: Generation in progress
    - succeed: Complete
    - failed: Error occurred
        """
    )

    parser.add_argument("task_id", help="Task ID to check")
    parser.add_argument(
        "-t", "--type",
        choices=["text2video", "image2video", "video-extend"],
        default="text2video",
        help="Task type (default: text2video)"
    )
    parser.add_argument("-k", "--api-key", help="Kling API key (ACCESS_KEY:SECRET_KEY)")
    parser.add_argument("--json", action="store_true", help="Output as JSON")

    args = parser.parse_args()

    result = get_task_status(
        task_id=args.task_id,
        task_type=args.type,
        api_key=args.api_key,
    )

    if result["success"]:
        if args.json:
            print(json.dumps(result, indent=2))
        else:
            print(f"Task ID: {result['task_id']}")
            print(f"Type: {result['type']}")
            print(f"Status: {result['status']}")

            if result.get("videos"):
                print("\nVideos:")
                for i, video in enumerate(result["videos"], 1):
                    print(f"  {i}. ID: {video['id']}")
                    print(f"     Duration: {video['duration']}s")
                    print(f"     URL: {video['url'][:80]}...")

        sys.exit(0)
    else:
        print(f"Error: {result['error']}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
