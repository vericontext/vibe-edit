---
name: test-pipeline
description: Test the script-to-video pipeline end-to-end
disable-model-invocation: true
context: fork
agent: feature-tester
---

Test the script-to-video pipeline, which is the most complex workflow in VibeFrame.

Create `test-output/` directory first.

## Step 1: Create a test script

Write a minimal test script to `test-output/test-script.txt`:
```
A 10 second product ad for a coffee brand.
Scene 1: A steaming cup of coffee on a wooden table. Narrator says "Start your morning right."
Scene 2: Close-up of coffee beans. Narrator says "Premium beans from Colombia."
```

## Step 2: Test storyboard generation
```bash
timeout 120 pnpm vibe ai storyboard "$(cat test-output/test-script.txt)" -o test-output/pipeline-storyboard.json
```
Verify: JSON file exists, has scenes array, each scene has description and narration.

## Step 3: Test script-to-video (if storyboard works)
```bash
timeout 600 pnpm vibe ai script-to-video test-output/test-script.txt -o test-output/pipeline-output
```
This is the full pipeline: storyboard → TTS → images → videos → project.
Use a 10-minute timeout as this involves multiple API calls.

## Step 4: Verify outputs
Check what files were created in `test-output/pipeline-output/`:
- `.vibe.json` project file
- Audio files (TTS narration)
- Image files
- Video files (if video generation was included)

## Report
Write `test-output/test-pipeline-report.md` with:
- Each step: PASS/FAIL
- Files generated
- Any errors encountered
- Time taken for each step
