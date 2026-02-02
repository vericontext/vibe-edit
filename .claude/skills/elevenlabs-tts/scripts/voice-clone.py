#!/usr/bin/env python3
"""
ElevenLabs Voice Clone Script

Clone a voice from audio samples using ElevenLabs API.

Usage:
    python voice-clone.py "My Voice" sample1.mp3 sample2.mp3
    python voice-clone.py "Custom Voice" audio.wav --description "Deep male voice"

Requirements:
    - ELEVENLABS_API_KEY environment variable
    - Python 3.8+
    - Audio samples: MP3, WAV, or other common formats
    - Clear speech with minimal background noise
    - Each sample 30s-3min recommended
"""

import argparse
import json
import os
import sys
import urllib.request
import urllib.error
from pathlib import Path


def get_mime_type(file_path: str) -> str:
    """Get MIME type from file extension."""
    ext = Path(file_path).suffix.lower()
    mime_types = {
        ".mp3": "audio/mpeg",
        ".wav": "audio/wav",
        ".m4a": "audio/mp4",
        ".ogg": "audio/ogg",
        ".flac": "audio/flac",
    }
    return mime_types.get(ext, "audio/mpeg")


def clone_voice(
    name: str,
    files: list[str],
    description: str | None = None,
    labels: dict | None = None,
    api_key: str | None = None,
) -> dict:
    """Clone a voice from audio samples using ElevenLabs."""

    api_key = api_key or os.environ.get("ELEVENLABS_API_KEY")
    if not api_key:
        return {"success": False, "error": "ELEVENLABS_API_KEY environment variable not set"}

    # Validate files
    for file_path in files:
        if not os.path.exists(file_path):
            return {"success": False, "error": f"File not found: {file_path}"}

    if len(files) > 25:
        return {"success": False, "error": "Maximum 25 audio samples allowed"}

    url = "https://api.elevenlabs.io/v1/voices/add"

    # Build multipart form data
    boundary = "----WebKitFormBoundary7MA4YWxkTrZu0gW"

    body_parts = []

    # Add name
    body_parts.append(f"--{boundary}".encode())
    body_parts.append(b'Content-Disposition: form-data; name="name"')
    body_parts.append(b"")
    body_parts.append(name.encode())

    # Add files
    for file_path in files:
        filename = Path(file_path).name
        mime_type = get_mime_type(file_path)

        with open(file_path, "rb") as f:
            file_data = f.read()

        body_parts.append(f"--{boundary}".encode())
        body_parts.append(f'Content-Disposition: form-data; name="files"; filename="{filename}"'.encode())
        body_parts.append(f"Content-Type: {mime_type}".encode())
        body_parts.append(b"")
        body_parts.append(file_data)

    # Add optional description
    if description:
        body_parts.append(f"--{boundary}".encode())
        body_parts.append(b'Content-Disposition: form-data; name="description"')
        body_parts.append(b"")
        body_parts.append(description.encode())

    # Add optional labels
    if labels:
        body_parts.append(f"--{boundary}".encode())
        body_parts.append(b'Content-Disposition: form-data; name="labels"')
        body_parts.append(b"")
        body_parts.append(json.dumps(labels).encode())

    body_parts.append(f"--{boundary}--".encode())
    body_parts.append(b"")

    body = b"\r\n".join(body_parts)

    headers = {
        "xi-api-key": api_key,
        "Accept": "application/json",
        "Content-Type": f"multipart/form-data; boundary={boundary}",
    }

    try:
        req = urllib.request.Request(url, data=body, headers=headers, method="POST")
        with urllib.request.urlopen(req, timeout=120) as response:
            result = json.loads(response.read().decode("utf-8"))

            return {
                "success": True,
                "voice_id": result.get("voice_id"),
                "name": name,
                "samples": len(files),
            }
    except urllib.error.HTTPError as e:
        error_body = e.read().decode("utf-8")
        try:
            error_json = json.loads(error_body)
            error_msg = error_json.get("detail", {}).get("message", error_body)
        except (json.JSONDecodeError, TypeError):
            error_msg = error_body
        return {"success": False, "error": f"API error ({e.code}): {error_msg}"}
    except Exception as e:
        return {"success": False, "error": str(e)}


def main():
    parser = argparse.ArgumentParser(
        description="Clone a voice from audio samples using ElevenLabs",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
    # Clone voice from single sample
    %(prog)s "My Voice" sample.mp3

    # Clone voice from multiple samples
    %(prog)s "Custom Voice" sample1.mp3 sample2.mp3 sample3.wav

    # Clone with description
    %(prog)s "Character Voice" audio.mp3 --description "Deep male narrator voice"

Requirements:
    - 1-25 audio samples (MP3, WAV, etc.)
    - Clear speech with minimal background noise
    - Each sample should be 30 seconds to 3 minutes
    - Total audio should be at least 1 minute
        """
    )

    parser.add_argument("name", help="Name for the cloned voice")
    parser.add_argument("files", nargs="+", help="Audio sample file(s)")
    parser.add_argument("-d", "--description", help="Voice description")
    parser.add_argument("-k", "--api-key", help="ElevenLabs API key")
    parser.add_argument("-v", "--verbose", action="store_true", help="Verbose output")

    args = parser.parse_args()

    print(f"Cloning voice '{args.name}' from {len(args.files)} sample(s)...")

    result = clone_voice(
        name=args.name,
        files=args.files,
        description=args.description,
        api_key=args.api_key,
    )

    if result["success"]:
        print(f"Voice cloned successfully!")
        print(f"Voice ID: {result['voice_id']}")
        print(f"Name: {result['name']}")
        if args.verbose:
            print(f"Samples used: {result['samples']}")
        sys.exit(0)
    else:
        print(f"Error: {result['error']}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
