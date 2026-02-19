---
name: test-ai
description: Test all AI generation commands (image, video, tts, sfx, music, storyboard)
disable-model-invocation: true
context: fork
agent: feature-tester
---

Test all AI generation commands. For each command, test the happy path with a simple prompt and verify the output file is created.

Create `test-output/` directory first.

## Commands to Test

1. **Image generation** (3 providers):
   ```bash
   timeout 120 pnpm vibe ai image "red circle" -o test-output/img-openai.png
   timeout 120 pnpm vibe ai image "blue square" -o test-output/img-gemini.png --provider gemini
   timeout 120 pnpm vibe ai image "green triangle" -o test-output/img-stability.png --provider stability
   ```

2. **TTS**:
   ```bash
   timeout 60 pnpm vibe ai tts "Hello world" -o test-output/tts.mp3
   ```

3. **SFX**:
   ```bash
   timeout 60 pnpm vibe ai sfx "rain on window" -o test-output/sfx.mp3
   ```

4. **Music**:
   ```bash
   timeout 120 pnpm vibe ai music "calm piano" -o test-output/music.mp3
   ```

5. **Video - Kling**:
   ```bash
   timeout 300 pnpm vibe ai kling "a ball bouncing" -o test-output/video-kling.mp4
   ```

6. **Video - Runway**:
   ```bash
   timeout 300 pnpm vibe ai video "ocean waves" -o test-output/video-runway.mp4
   ```

7. **Storyboard**:
   ```bash
   timeout 120 pnpm vibe ai storyboard "10 second coffee ad" -o test-output/storyboard.json
   ```

For each test, record: command, exit code, output file size (or error message).
Write results to `test-output/test-ai-report.md`.
