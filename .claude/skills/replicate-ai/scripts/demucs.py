#!/usr/bin/env python3
"""
Replicate Audio Separation Script (Demucs)

Separate audio stems (vocals, drums, bass, other) using Demucs on Replicate.

Usage:
    python demucs.py song.mp3 -o vocals.mp3 --stem vocals
    python demucs.py song.mp3 -o separated/ --all

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


def audio_to_data_uri(file_path: str) -> str:
    """Convert audio file to data URI."""
    ext = Path(file_path).suffix.lower()
    mime_types = {
        ".mp3": "audio/mpeg",
        ".wav": "audio/wav",
        ".m4a": "audio/mp4",
        ".ogg": "audio/ogg",
        ".flac": "audio/flac",
    }
    mime_type = mime_types.get(ext, "audio/mpeg")

    with open(file_path, "rb") as f:
        data = base64.b64encode(f.read()).decode()

    return f"data:{mime_type};base64,{data}"


def separate_audio(
    audio_path: str | None = None,
    audio_url: str | None = None,
    output_path: str = None,
    stem: str | None = None,
    all_stems: bool = False,
    api_key: str | None = None,
) -> dict:
    """Separate audio using Demucs on Replicate."""

    api_key = api_key or os.environ.get("REPLICATE_API_TOKEN")
    if not api_key:
        return {"success": False, "error": "REPLICATE_API_TOKEN environment variable not set"}

    # Determine audio source
    if audio_url:
        source = audio_url
    elif audio_path:
        if not os.path.exists(audio_path):
            return {"success": False, "error": f"Audio file not found: {audio_path}"}
        source = audio_to_data_uri(audio_path)
    else:
        return {"success": False, "error": "Either audio file or URL required"}

    url = "https://api.replicate.com/v1/predictions"

    # Using cjwbw/demucs model
    # https://replicate.com/cjwbw/demucs
    payload = {
        "version": "25a173108cff36ef9f80f854c162d01df9e6528be175794b81158fa03836d953",
        "input": {
            "audio": source,
        }
    }

    # If specific stem requested
    if stem and not all_stems:
        payload["input"]["stem"] = stem

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
        print("Separating audio stems...")

        # Poll for completion
        status_url = f"https://api.replicate.com/v1/predictions/{prediction_id}"
        headers_get = {"Authorization": f"Bearer {api_key}"}
        start_time = time.time()
        timeout = 600  # 10 minutes

        while time.time() - start_time < timeout:
            req = urllib.request.Request(status_url, headers=headers_get, method="GET")
            with urllib.request.urlopen(req, timeout=30) as response:
                status_result = json.loads(response.read().decode("utf-8"))

            status = status_result.get("status")
            print(f"Status: {status}")

            if status == "succeeded":
                output = status_result.get("output")

                if isinstance(output, dict):
                    # Multiple stems returned
                    if all_stems:
                        # Save all stems
                        output_dir = Path(output_path)
                        output_dir.mkdir(parents=True, exist_ok=True)

                        saved_files = []
                        for stem_name, stem_url in output.items():
                            stem_path = output_dir / f"{stem_name}.mp3"
                            urllib.request.urlretrieve(stem_url, str(stem_path))
                            saved_files.append(str(stem_path))

                        return {
                            "success": True,
                            "output": saved_files,
                            "prediction_id": prediction_id,
                        }
                    elif stem and stem in output:
                        urllib.request.urlretrieve(output[stem], output_path)
                        return {
                            "success": True,
                            "output": output_path,
                            "stem": stem,
                            "prediction_id": prediction_id,
                        }
                    else:
                        # Default to vocals if available
                        stem_url = output.get("vocals") or list(output.values())[0]
                        urllib.request.urlretrieve(stem_url, output_path)
                        return {
                            "success": True,
                            "output": output_path,
                            "prediction_id": prediction_id,
                        }

                elif isinstance(output, str):
                    urllib.request.urlretrieve(output, output_path)
                    return {
                        "success": True,
                        "output": output_path,
                        "prediction_id": prediction_id,
                    }

                return {"success": False, "error": "Unexpected output format"}

            elif status == "failed":
                error = status_result.get("error", "Unknown error")
                return {"success": False, "error": f"Processing failed: {error}"}

            time.sleep(5)

        return {"success": False, "error": "Timeout waiting for processing"}

    except urllib.error.HTTPError as e:
        error_body = e.read().decode("utf-8")
        return {"success": False, "error": f"API error ({e.code}): {error_body}"}
    except Exception as e:
        return {"success": False, "error": str(e)}


def main():
    parser = argparse.ArgumentParser(
        description="Separate audio stems using Demucs on Replicate",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
    # Extract vocals
    %(prog)s song.mp3 -o vocals.mp3 --stem vocals

    # Extract drums
    %(prog)s song.mp3 -o drums.mp3 --stem drums

    # Extract all stems
    %(prog)s song.mp3 -o stems_folder/ --all

    # From URL
    %(prog)s --url https://example.com/song.mp3 -o vocals.mp3 --stem vocals

Available stems:
    - vocals: Vocal track
    - drums: Drum track
    - bass: Bass track
    - other: Everything else (instruments)
        """
    )

    parser.add_argument("audio", nargs="?", help="Audio file path")
    parser.add_argument("-u", "--url", help="Audio URL")
    parser.add_argument("-o", "--output", required=True, help="Output file/directory path")
    parser.add_argument(
        "--stem",
        choices=["vocals", "drums", "bass", "other"],
        help="Specific stem to extract"
    )
    parser.add_argument(
        "--all",
        action="store_true",
        help="Extract all stems (output must be a directory)"
    )
    parser.add_argument("-k", "--api-key", help="Replicate API token")
    parser.add_argument("-v", "--verbose", action="store_true", help="Verbose output")

    args = parser.parse_args()

    if not args.audio and not args.url:
        print("Error: Either audio file or --url required", file=sys.stderr)
        sys.exit(1)

    result = separate_audio(
        audio_path=args.audio,
        audio_url=args.url,
        output_path=args.output,
        stem=args.stem,
        all_stems=args.all,
        api_key=args.api_key,
    )

    if result["success"]:
        output = result["output"]
        if isinstance(output, list):
            print("Saved stems:")
            for f in output:
                print(f"  - {f}")
        else:
            print(f"Saved: {output}")

        if args.verbose:
            print(f"Prediction ID: {result['prediction_id']}")
            if result.get("stem"):
                print(f"Stem: {result['stem']}")
        sys.exit(0)
    else:
        print(f"Error: {result['error']}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
