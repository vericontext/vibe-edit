---
name: test-project
description: Test project CRUD and timeline operations
disable-model-invocation: true
context: fork
agent: feature-tester
---

Test project management and timeline editing commands.

Create `test-output/` directory first.

## Phase 1: Project CRUD

### Create
```bash
pnpm vibe project create test-output/proj-test 2>&1
echo "Exit: $?"
cat test-output/proj-test/.vibe.json 2>/dev/null | head -20
```

### Info
```bash
pnpm vibe project info test-output/proj-test/.vibe.json 2>&1
echo "Exit: $?"
```

### Create with name
```bash
pnpm vibe project create test-output/proj-named --name "My Test Project" 2>&1
echo "Exit: $?"
```

## Phase 2: Timeline Operations

First, check what timeline subcommands are available:
```bash
pnpm vibe timeline --help 2>&1
```

Then test each available subcommand with the project created above.

### Add source (if a test media file exists)
```bash
# Generate a quick test image first
timeout 120 pnpm vibe ai image "white square" -o test-output/test-media.png 2>&1

# Add as source
pnpm vibe timeline add-source test-output/proj-test/.vibe.json test-output/test-media.png 2>&1
echo "Exit: $?"
```

### List timeline
```bash
pnpm vibe timeline list test-output/proj-test/.vibe.json 2>&1
echo "Exit: $?"
```

## Phase 3: Export (if sources added)
```bash
pnpm vibe export --help 2>&1
timeout 120 pnpm vibe export test-output/proj-test/.vibe.json -o test-output/export-test.mp4 2>&1
echo "Exit: $?"
```

## Phase 4: Media Utils
```bash
pnpm vibe media --help 2>&1
pnpm vibe media info test-output/test-media.png 2>&1
echo "Exit: $?"
```

## Report
Write results to `test-output/test-project-report.md`.
