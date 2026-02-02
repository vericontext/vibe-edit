---
name: gemini-video
description: Analyze and understand videos using Google Gemini. Use for video summarization, Q&A, content extraction, timestamp analysis, and YouTube video processing.
allowed-tools: Bash(curl *), Bash(python *), Read, Write
---

# Gemini Video Understanding

Analyze, summarize, and extract information from videos using Google Gemini's multimodal capabilities.

## Capabilities

| Feature | Description |
|---------|-------------|
| Video Summarization | Generate concise summaries of video content |
| Q&A | Answer questions about video content |
| Timestamp Analysis | Refer to and analyze specific moments |
| Content Extraction | Extract key events, quotes, and insights |
| YouTube Analysis | Process YouTube videos directly via URL |
| Custom Sampling | Control frame rate and clipping intervals |

## Authentication

```bash
export GOOGLE_API_KEY="your-api-key"
```

## Supported Models

| Model | Context | Max Video Length |
|-------|---------|------------------|
| `gemini-3-flash-preview` | 1M tokens | ~1 hour (default) / ~3 hours (low res) |
| `gemini-2.5-flash` | 1M tokens | ~1 hour |
| `gemini-2.5-pro` | 1M tokens | ~1 hour |

## Supported Video Formats

- `video/mp4`, `video/mpeg`, `video/mov`, `video/avi`
- `video/x-flv`, `video/mpg`, `video/webm`, `video/wmv`, `video/3gpp`

## Input Methods

### 1. Upload via File API (Recommended for large files)

Use for files >20MB or videos >1 minute:

```bash
# Upload file
curl -X POST "https://generativelanguage.googleapis.com/upload/v1beta/files?key=$GOOGLE_API_KEY" \
  -H "X-Goog-Upload-Protocol: resumable" \
  -H "X-Goog-Upload-Command: start" \
  -H "X-Goog-Upload-Header-Content-Length: $(stat -f%z video.mp4)" \
  -H "X-Goog-Upload-Header-Content-Type: video/mp4" \
  -H "Content-Type: application/json" \
  -d '{"file": {"display_name": "video.mp4"}}'

# Then use the returned upload URL to upload the file
```

### 2. Inline Data (Small files <20MB)

```json
{
  "contents": [{
    "parts": [
      {
        "inline_data": {
          "mime_type": "video/mp4",
          "data": "<base64_encoded_video>"
        }
      },
      {"text": "Summarize this video"}
    ]
  }]
}
```

### 3. YouTube URL (Preview Feature)

```json
{
  "contents": [{
    "parts": [
      {
        "file_data": {
          "file_uri": "https://www.youtube.com/watch?v=VIDEO_ID"
        }
      },
      {"text": "Summarize this video"}
    ]
  }]
}
```

**YouTube Limitations:**
- Free tier: Max 8 hours of YouTube video per day
- Only public videos (not private/unlisted)
- Gemini 2.5+: Up to 10 videos per request

## API Request Format

### Basic Analysis

```json
{
  "contents": [{
    "parts": [
      {"file_data": {"file_uri": "files/FILE_ID"}},
      {"text": "Your prompt here"}
    ]
  }],
  "generationConfig": {
    "temperature": 0.4,
    "maxOutputTokens": 8192
  }
}
```

### With Video Metadata (Clipping & FPS)

```json
{
  "contents": [{
    "parts": [
      {
        "file_data": {"file_uri": "https://www.youtube.com/watch?v=VIDEO_ID"},
        "video_metadata": {
          "start_offset": "60s",
          "end_offset": "180s",
          "fps": 2
        }
      },
      {"text": "Analyze this segment"}
    ]
  }]
}
```

### With Media Resolution Control

```json
{
  "generationConfig": {
    "mediaResolution": "low"
  }
}
```

- `low`: 66 tokens/frame (~100 tokens/second total)
- Default: 258 tokens/frame (~300 tokens/second total)

## Token Calculation

| Component | Tokens |
|-----------|--------|
| Frame (default res) | 258 tokens/frame |
| Frame (low res) | 66 tokens/frame |
| Audio | 32 tokens/second |
| **Total (default)** | ~300 tokens/second |
| **Total (low res)** | ~100 tokens/second |

## Usage with Helper Script

### Analyze Local Video

```bash
# Basic summary
python .claude/skills/gemini-video/scripts/analyze.py video.mp4 "Summarize this video"

# Detailed analysis with timestamps
python .claude/skills/gemini-video/scripts/analyze.py video.mp4 "List key events with timestamps" -v

# Custom frame rate
python .claude/skills/gemini-video/scripts/analyze.py video.mp4 "Analyze the action" --fps 5

# Video clipping
python .claude/skills/gemini-video/scripts/analyze.py video.mp4 "Summarize" --start 60 --end 180
```

### Analyze YouTube Video

```bash
# YouTube URL analysis
python .claude/skills/gemini-video/scripts/analyze.py "https://www.youtube.com/watch?v=VIDEO_ID" "Summarize in 3 sentences"

# With clipping
python .claude/skills/gemini-video/scripts/analyze.py "https://www.youtube.com/watch?v=VIDEO_ID" "What happens here?" --start 300 --end 600
```

## Integration with VibeFrame CLI

```bash
# Analyze local video
vibe ai gemini-video video.mp4 "Summarize this video"

# Analyze YouTube video
vibe ai gemini-video "https://www.youtube.com/watch?v=VIDEO_ID" "What is this video about?"

# Detailed analysis with timestamps
vibe ai gemini-video video.mp4 "List all key events with timestamps" --verbose

# Custom frame rate for action videos
vibe ai gemini-video action.mp4 "Describe the movements" --fps 5

# Analyze specific segment
vibe ai gemini-video long_video.mp4 "Summarize this part" --start 120 --end 300

# Low resolution mode for longer videos
vibe ai gemini-video lecture.mp4 "Create study notes" --low-res
```

## Prompting Examples

### Video Summarization

```
Summarize this video in 3-5 bullet points, covering the main topics discussed.
```

### Q&A with Timestamps

```
What are the examples shown at 00:45 and 01:30? Explain their significance.
```

### Detailed Event Extraction

```
Describe the key events in this video, providing both audio and visual details.
Include timestamps for salient moments in MM:SS format.
```

### Quiz Generation

```
Create a 5-question quiz with answer key based on the information in this video.
```

### Content Analysis

```
Analyze this video for:
1. Main topic and thesis
2. Key arguments or points made
3. Visual elements and their purpose
4. Tone and target audience
```

### Transcript Extraction

```
Provide a detailed transcript of the spoken content in this video,
including speaker identification where possible.
```

## Best Practices

1. **Single Video Per Request**: Use one video per prompt for optimal results
2. **Text After Video**: Place the text prompt after the video part in contents
3. **Timestamp Format**: Use MM:SS format when referring to specific moments
4. **Fast Action**: Default 1 FPS may miss details; increase FPS for action videos
5. **Long Videos**: Use low resolution mode or clipping for videos >30 minutes
6. **Static Content**: Use lower FPS (<1) for lectures or presentations

## Limitations

- Videos are sampled at 1 FPS by default (customizable)
- Audio processed at 1Kbps single channel
- Fast action sequences may lose detail at low FPS
- YouTube: Only public videos, rate limited on free tier
- Max ~1 hour at default resolution, ~3 hours at low resolution

## References

- [Gemini Video Understanding](https://ai.google.dev/gemini-api/docs/video-understanding)
- [Files API Guide](https://ai.google.dev/gemini-api/docs/files)
- [Media Resolution Guide](https://ai.google.dev/gemini-api/docs/media-resolution)
