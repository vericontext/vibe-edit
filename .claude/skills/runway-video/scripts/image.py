#!/usr/bin/env python3
"""
Runway Image Generation Script

Usage:
    python image.py "a sunset over mountains" -o sunset.png
    python image.py "portrait" -o portrait.png -m gen4_image -i reference.png

Models:
    gemini (default) - Text-to-image, no reference needed
    gen4_image - Requires reference image, high quality
    gen4_image_turbo - Requires reference image, fast (2 credits)

Requires: pip install runwayml
"""

import argparse
import base64
import os
import sys
import urllib.request

try:
    from runwayml import RunwayML
except ImportError:
    print("Error: runwayml package not installed. Run: pip install runwayml", file=sys.stderr)
    sys.exit(1)


MODELS = {
    "gemini": "gemini_2.5_flash",         # 5 credits, no reference needed
    "gen4_image": "gen4_image",           # 5-8 credits, requires reference
    "gen4_image_turbo": "gen4_image_turbo",  # 2 credits, requires reference
    "turbo": "gen4_image_turbo",          # alias
}

# Ratios differ by model
GEMINI_RATIOS = {
    "16:9": "1344:768",
    "9:16": "768:1344",
    "1:1": "1024:1024",
    "4:3": "1184:864",
    "3:4": "864:1184",
}

GEN4_RATIOS = {
    "16:9": "1920:1080",
    "720p": "1280:720",
    "1080p": "1920:1080",
    "9:16": "1080:1920",
    "1:1": "1080:1080",
    "square": "1024:1024",
}


def generate_image(
    prompt: str,
    output_path: str,
    model: str = "gemini_2.5_flash",
    ratio: str = "16:9",
    reference_image: str | None = None,
    api_key: str | None = None,
) -> dict:
    """Generate image using Runway."""

    api_key = api_key or os.environ.get("RUNWAY_API_SECRET")
    if not api_key:
        return {"success": False, "error": "RUNWAY_API_SECRET not set"}

    # Resolve model alias
    if model in MODELS:
        model = MODELS[model]

    # Check if reference image is required
    needs_reference = model in ["gen4_image", "gen4_image_turbo"]
    if needs_reference and not reference_image:
        return {"success": False, "error": f"{model} requires a reference image. Use -i option or use 'gemini' model for text-only."}

    # Resolve ratio based on model
    if model == "gemini_2.5_flash":
        api_ratio = GEMINI_RATIOS.get(ratio, ratio)
    else:
        api_ratio = GEN4_RATIOS.get(ratio, ratio)

    # Initialize client
    client = RunwayML(api_key=api_key)

    try:
        print(f"Generating image with {model}...")
        print(f"Prompt: {prompt}")
        print(f"Ratio: {api_ratio}")

        # Prepare reference images if needed
        ref_images = []
        if reference_image:
            if reference_image.startswith(("http://", "https://")):
                ref_images = [{"uri": reference_image}]
            else:
                # Local file - convert to base64
                with open(reference_image, "rb") as f:
                    image_data = base64.b64encode(f.read()).decode("utf-8")
                ext = reference_image.lower().split(".")[-1]
                mime_types = {"jpg": "image/jpeg", "jpeg": "image/jpeg", "png": "image/png"}
                mime_type = mime_types.get(ext, "image/png")
                ref_images = [{"uri": f"data:{mime_type};base64,{image_data}"}]

        # Create task
        if needs_reference:
            task = client.text_to_image.create(
                model=model,
                prompt_text=prompt,
                ratio=api_ratio,
                reference_images=ref_images,
            ).wait_for_task_output()
        else:
            task = client.text_to_image.create(
                model=model,
                prompt_text=prompt,
                ratio=api_ratio,
            ).wait_for_task_output()

        print(f"Task complete: {task.id}")

        # Get image URL from task output
        if task.output and len(task.output) > 0:
            image_url = task.output[0]

            # Download image
            print(f"Downloading image...")
            req = urllib.request.Request(image_url)
            with urllib.request.urlopen(req, timeout=60) as response:
                image_data = response.read()

            with open(output_path, "wb") as f:
                f.write(image_data)

            return {
                "success": True,
                "output_path": output_path,
                "size_bytes": len(image_data),
                "task_id": task.id,
            }
        else:
            return {"success": False, "error": "No output URL in task result"}

    except Exception as e:
        return {"success": False, "error": str(e)}


def main():
    parser = argparse.ArgumentParser(description="Runway Image Generation")
    parser.add_argument("prompt", help="Text description of the image")
    parser.add_argument("-o", "--output", required=True, help="Output image path")
    parser.add_argument("-m", "--model", default="gemini",
                        choices=list(MODELS.keys()),
                        help="Model: gemini (text-only), gen4_image/turbo (needs reference)")
    parser.add_argument("-r", "--ratio", default="16:9",
                        help="Aspect ratio (16:9, 9:16, 1:1, 4:3, 720p, 1080p)")
    parser.add_argument("-i", "--reference", help="Reference image (required for gen4 models)")
    parser.add_argument("-k", "--api-key", help="API key (or set RUNWAY_API_SECRET)")

    args = parser.parse_args()

    result = generate_image(
        prompt=args.prompt,
        output_path=args.output,
        model=args.model,
        ratio=args.ratio,
        reference_image=args.reference,
        api_key=args.api_key,
    )

    if result["success"]:
        print(f"Saved to: {result['output_path']}")
        print(f"Size: {result['size_bytes']:,} bytes")
    else:
        print(f"Error: {result['error']}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
