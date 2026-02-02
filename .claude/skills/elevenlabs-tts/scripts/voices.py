#!/usr/bin/env python3
"""
ElevenLabs Voice List Script

List available voices from ElevenLabs API.

Usage:
    python voices.py
    python voices.py --json
    python voices.py --filter "female"

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


def list_voices(
    filter_text: str | None = None,
    api_key: str | None = None,
) -> dict:
    """List available voices from ElevenLabs."""

    api_key = api_key or os.environ.get("ELEVENLABS_API_KEY")
    if not api_key:
        return {"success": False, "error": "ELEVENLABS_API_KEY environment variable not set"}

    url = "https://api.elevenlabs.io/v1/voices"

    headers = {
        "xi-api-key": api_key,
        "Accept": "application/json",
    }

    try:
        req = urllib.request.Request(url, headers=headers, method="GET")
        with urllib.request.urlopen(req, timeout=30) as response:
            result = json.loads(response.read().decode("utf-8"))

            voices = result.get("voices", [])

            # Filter if specified
            if filter_text:
                filter_lower = filter_text.lower()
                voices = [
                    v for v in voices
                    if filter_lower in v.get("name", "").lower()
                    or filter_lower in v.get("labels", {}).get("gender", "").lower()
                    or filter_lower in v.get("labels", {}).get("accent", "").lower()
                    or filter_lower in v.get("labels", {}).get("description", "").lower()
                ]

            return {
                "success": True,
                "voices": voices,
                "total": len(voices),
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
        description="List available voices from ElevenLabs",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
    # List all voices
    %(prog)s

    # Output as JSON
    %(prog)s --json

    # Filter by keyword
    %(prog)s --filter "female"
    %(prog)s --filter "british"
        """
    )

    parser.add_argument("-f", "--filter", help="Filter voices by keyword")
    parser.add_argument("-k", "--api-key", help="ElevenLabs API key")
    parser.add_argument("--json", action="store_true", help="Output as JSON")

    args = parser.parse_args()

    result = list_voices(
        filter_text=args.filter,
        api_key=args.api_key,
    )

    if result["success"]:
        voices = result["voices"]

        if args.json:
            print(json.dumps(voices, indent=2))
        else:
            print(f"Found {result['total']} voice(s):\n")
            print(f"{'ID':<30} {'Name':<20} {'Gender':<10} {'Accent':<15}")
            print("-" * 75)

            for voice in voices:
                voice_id = voice.get("voice_id", "")[:28]
                name = voice.get("name", "")[:18]
                labels = voice.get("labels", {})
                gender = labels.get("gender", "")[:8]
                accent = labels.get("accent", "")[:13]

                print(f"{voice_id:<30} {name:<20} {gender:<10} {accent:<15}")

        sys.exit(0)
    else:
        print(f"Error: {result['error']}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
