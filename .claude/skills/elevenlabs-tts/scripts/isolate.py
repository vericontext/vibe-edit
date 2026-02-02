#!/usr/bin/env python3
"""
ElevenLabs Audio Isolation Script

Separate vocals from background audio using ElevenLabs API.

Usage:
    python isolate.py audio.mp3 -o vocals.mp3
    python isolate.py song.wav -o clean_voice.mp3

Requirements:
    - ELEVENLABS_API_KEY environment variable
    - Python 3.8+
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


def isolate_audio(
    audio_path: str,
    output_path: str,
    api_key: str | None = None,
) -> dict:
    """Isolate vocals from audio using ElevenLabs."""

    api_key = api_key or os.environ.get("ELEVENLABS_API_KEY")
    if not api_key:
        return {"success": False, "error": "ELEVENLABS_API_KEY environment variable not set"}

    if not os.path.exists(audio_path):
        return {"success": False, "error": f"Audio file not found: {audio_path}"}

    url = "https://api.elevenlabs.io/v1/audio-isolation"

    # Build multipart form data
    boundary = "----WebKitFormBoundary7MA4YWxkTrZu0gW"

    filename = Path(audio_path).name
    mime_type = get_mime_type(audio_path)

    with open(audio_path, "rb") as f:
        audio_data = f.read()

    body_parts = []

    # Add audio file
    body_parts.append(f"--{boundary}".encode())
    body_parts.append(f'Content-Disposition: form-data; name="audio"; filename="{filename}"'.encode())
    body_parts.append(f"Content-Type: {mime_type}".encode())
    body_parts.append(b"")
    body_parts.append(audio_data)

    body_parts.append(f"--{boundary}--".encode())
    body_parts.append(b"")

    body = b"\r\n".join(body_parts)

    headers = {
        "xi-api-key": api_key,
        "Accept": "audio/mpeg",
        "Content-Type": f"multipart/form-data; boundary={boundary}",
    }

    try:
        req = urllib.request.Request(url, data=body, headers=headers, method="POST")
        with urllib.request.urlopen(req, timeout=300) as response:
            # Save the isolated audio
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
            error_msg = error_json.get("detail", {}).get("message", error_body)
        except (json.JSONDecodeError, TypeError):
            error_msg = error_body
        return {"success": False, "error": f"API error ({e.code}): {error_msg}"}
    except Exception as e:
        return {"success": False, "error": str(e)}


def main():
    parser = argparse.ArgumentParser(
        description="Isolate vocals from audio using ElevenLabs",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
    # Isolate vocals from a song
    %(prog)s song.mp3 -o vocals.mp3

    # Clean up speech from noisy recording
    %(prog)s noisy_recording.wav -o clean_speech.mp3

Use cases:
    - Extract vocals from songs
    - Clean up speech from background noise
    - Separate dialogue from music/effects
        """
    )

    parser.add_argument("audio", help="Input audio file path")
    parser.add_argument("-o", "--output", required=True, help="Output file path")
    parser.add_argument("-k", "--api-key", help="ElevenLabs API key")

    args = parser.parse_args()

    print("Isolating audio...")

    result = isolate_audio(
        audio_path=args.audio,
        output_path=args.output,
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
