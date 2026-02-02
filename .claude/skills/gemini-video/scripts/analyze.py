#!/usr/bin/env python3
"""
Gemini Video Understanding Script

Analyze videos using Google Gemini's multimodal capabilities.

Usage:
    python analyze.py video.mp4 "Summarize this video"
    python analyze.py "https://www.youtube.com/watch?v=ID" "What is this about?"
    python analyze.py video.mp4 "Describe key events" --fps 2 --start 60 --end 180

Requirements:
    - GOOGLE_API_KEY environment variable
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

MODELS = {
    "flash": "gemini-3-flash-preview",
    "flash-2.5": "gemini-2.5-flash",
    "pro": "gemini-2.5-pro",
}

MIME_TYPES = {
    ".mp4": "video/mp4",
    ".mpeg": "video/mpeg",
    ".mpg": "video/mpg",
    ".mov": "video/mov",
    ".avi": "video/avi",
    ".flv": "video/x-flv",
    ".webm": "video/webm",
    ".wmv": "video/wmv",
    ".3gp": "video/3gpp",
    ".3gpp": "video/3gpp",
}


def is_youtube_url(source: str) -> bool:
    """Check if source is a YouTube URL."""
    return "youtube.com" in source or "youtu.be" in source


def get_mime_type(file_path: str) -> str:
    """Get MIME type from file extension."""
    ext = Path(file_path).suffix.lower()
    return MIME_TYPES.get(ext, "video/mp4")


def upload_file(file_path: str, api_key: str) -> dict:
    """Upload a file using the Files API."""
    file_size = os.path.getsize(file_path)
    mime_type = get_mime_type(file_path)
    display_name = Path(file_path).name

    # Step 1: Initiate resumable upload
    init_url = f"https://generativelanguage.googleapis.com/upload/v1beta/files?key={api_key}"
    init_headers = {
        "X-Goog-Upload-Protocol": "resumable",
        "X-Goog-Upload-Command": "start",
        "X-Goog-Upload-Header-Content-Length": str(file_size),
        "X-Goog-Upload-Header-Content-Type": mime_type,
        "Content-Type": "application/json",
    }
    init_data = json.dumps({"file": {"display_name": display_name}}).encode("utf-8")

    try:
        req = urllib.request.Request(init_url, data=init_data, headers=init_headers, method="POST")
        with urllib.request.urlopen(req, timeout=60) as response:
            upload_url = response.headers.get("X-Goog-Upload-URL")
            if not upload_url:
                return {"success": False, "error": "No upload URL returned"}
    except Exception as e:
        return {"success": False, "error": f"Failed to initiate upload: {e}"}

    # Step 2: Upload the file content
    with open(file_path, "rb") as f:
        file_data = f.read()

    upload_headers = {
        "Content-Length": str(file_size),
        "X-Goog-Upload-Offset": "0",
        "X-Goog-Upload-Command": "upload, finalize",
    }

    try:
        req = urllib.request.Request(upload_url, data=file_data, headers=upload_headers, method="POST")
        with urllib.request.urlopen(req, timeout=300) as response:
            result = json.loads(response.read().decode("utf-8"))
            file_info = result.get("file", {})
            return {
                "success": True,
                "file_uri": file_info.get("uri"),
                "name": file_info.get("name"),
                "state": file_info.get("state"),
            }
    except Exception as e:
        return {"success": False, "error": f"Failed to upload file: {e}"}


def wait_for_processing(file_name: str, api_key: str, timeout: int = 300) -> dict:
    """Wait for file processing to complete."""
    url = f"https://generativelanguage.googleapis.com/v1beta/{file_name}?key={api_key}"
    start_time = time.time()

    while time.time() - start_time < timeout:
        try:
            req = urllib.request.Request(url, method="GET")
            with urllib.request.urlopen(req, timeout=30) as response:
                result = json.loads(response.read().decode("utf-8"))
                state = result.get("state")

                if state == "ACTIVE":
                    return {"success": True, "file_uri": result.get("uri")}
                elif state == "FAILED":
                    return {"success": False, "error": "File processing failed"}

                # Still processing, wait and retry
                time.sleep(2)
        except Exception as e:
            return {"success": False, "error": f"Failed to check file status: {e}"}

    return {"success": False, "error": "File processing timed out"}


def analyze_video(
    source: str,
    prompt: str,
    model: str = "flash",
    fps: float | None = None,
    start_offset: int | None = None,
    end_offset: int | None = None,
    low_res: bool = False,
    api_key: str | None = None,
) -> dict:
    """Analyze video using Gemini API."""

    api_key = api_key or os.environ.get("GOOGLE_API_KEY")
    if not api_key:
        return {"success": False, "error": "GOOGLE_API_KEY environment variable not set"}

    model_id = MODELS.get(model, model)
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{model_id}:generateContent?key={api_key}"

    # Build the video part based on source type
    video_part = {}

    if is_youtube_url(source):
        # YouTube URL
        video_part["file_data"] = {"file_uri": source}
    elif os.path.exists(source):
        # Local file - check size
        file_size = os.path.getsize(source)

        if file_size > 20 * 1024 * 1024:  # >20MB, use File API
            print("Uploading video file...")
            upload_result = upload_file(source, api_key)
            if not upload_result["success"]:
                return upload_result

            # Wait for processing
            print("Processing video...")
            process_result = wait_for_processing(upload_result["name"], api_key)
            if not process_result["success"]:
                return process_result

            video_part["file_data"] = {"file_uri": process_result["file_uri"]}
        else:
            # Small file, use inline data
            with open(source, "rb") as f:
                video_data = base64.b64encode(f.read()).decode("utf-8")
            video_part["inline_data"] = {
                "mime_type": get_mime_type(source),
                "data": video_data,
            }
    else:
        return {"success": False, "error": f"Source not found: {source}"}

    # Add video metadata if specified
    video_metadata = {}
    if fps is not None:
        video_metadata["fps"] = fps
    if start_offset is not None:
        video_metadata["start_offset"] = f"{start_offset}s"
    if end_offset is not None:
        video_metadata["end_offset"] = f"{end_offset}s"

    if video_metadata:
        video_part["video_metadata"] = video_metadata

    # Build request payload
    payload = {
        "contents": [{
            "parts": [
                video_part,
                {"text": prompt}
            ]
        }],
        "generationConfig": {
            "temperature": 0.4,
            "maxOutputTokens": 8192,
        }
    }

    # Add low resolution mode
    if low_res:
        payload["generationConfig"]["mediaResolution"] = "low"

    headers = {"Content-Type": "application/json"}
    data = json.dumps(payload).encode("utf-8")

    try:
        req = urllib.request.Request(url, data=data, headers=headers, method="POST")
        with urllib.request.urlopen(req, timeout=300) as response:
            result = json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        error_body = e.read().decode("utf-8")
        try:
            error_json = json.loads(error_body)
            error_msg = error_json.get("error", {}).get("message", error_body)
        except json.JSONDecodeError:
            error_msg = error_body
        return {"success": False, "error": f"API error ({e.code}): {error_msg}"}
    except Exception as e:
        return {"success": False, "error": str(e)}

    # Extract response text
    candidates = result.get("candidates", [])
    if not candidates:
        return {"success": False, "error": "No response from model"}

    parts = candidates[0].get("content", {}).get("parts", [])
    text_parts = [p.get("text", "") for p in parts if "text" in p]
    response_text = "\n".join(text_parts)

    # Get usage metadata
    usage = result.get("usageMetadata", {})

    return {
        "success": True,
        "response": response_text,
        "model": model_id,
        "prompt_tokens": usage.get("promptTokenCount"),
        "response_tokens": usage.get("candidatesTokenCount"),
        "total_tokens": usage.get("totalTokenCount"),
    }


def main():
    parser = argparse.ArgumentParser(
        description="Analyze videos using Gemini",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
    # Summarize a local video
    %(prog)s video.mp4 "Summarize this video in 3 sentences"

    # Analyze a YouTube video
    %(prog)s "https://www.youtube.com/watch?v=VIDEO_ID" "What are the main points?"

    # Extract events with timestamps
    %(prog)s video.mp4 "List key events with timestamps" -v

    # Analyze specific segment with custom FPS
    %(prog)s video.mp4 "Describe the action" --start 60 --end 120 --fps 5

    # Long video with low resolution
    %(prog)s lecture.mp4 "Create study notes" --low-res
        """
    )

    parser.add_argument("source", help="Video file path or YouTube URL")
    parser.add_argument("prompt", help="Analysis prompt")
    parser.add_argument(
        "-m", "--model",
        default="flash",
        help="Model: flash (default), flash-2.5, pro"
    )
    parser.add_argument(
        "--fps",
        type=float,
        help="Frames per second (default: 1, use higher for action, lower for static)"
    )
    parser.add_argument(
        "--start",
        type=int,
        help="Start offset in seconds (for clipping)"
    )
    parser.add_argument(
        "--end",
        type=int,
        help="End offset in seconds (for clipping)"
    )
    parser.add_argument(
        "--low-res",
        action="store_true",
        help="Use low resolution mode (66 tokens/frame vs 258)"
    )
    parser.add_argument("-k", "--api-key", help="Google API key (or set GOOGLE_API_KEY env)")
    parser.add_argument("-v", "--verbose", action="store_true", help="Show token usage")

    args = parser.parse_args()

    source_type = "YouTube" if is_youtube_url(args.source) else "local file"
    print(f"Analyzing {source_type}...")

    result = analyze_video(
        source=args.source,
        prompt=args.prompt,
        model=args.model,
        fps=args.fps,
        start_offset=args.start,
        end_offset=args.end,
        low_res=args.low_res,
        api_key=args.api_key,
    )

    if result["success"]:
        print()
        print(result["response"])
        print()

        if args.verbose:
            print("-" * 40)
            print(f"Model: {result['model']}")
            if result.get("prompt_tokens"):
                print(f"Prompt tokens: {result['prompt_tokens']:,}")
            if result.get("response_tokens"):
                print(f"Response tokens: {result['response_tokens']:,}")
            if result.get("total_tokens"):
                print(f"Total tokens: {result['total_tokens']:,}")

        sys.exit(0)
    else:
        print(f"Error: {result['error']}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
