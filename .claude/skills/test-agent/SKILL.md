---
name: test-agent
description: Test Agent mode with different LLM providers
disable-model-invocation: true
context: fork
agent: feature-tester
---

Test Agent mode with each available LLM provider using non-interactive single-query mode.

Create `test-output/` directory first.

## Tests

### 1. OpenAI (default)
```bash
timeout 60 pnpm vibe agent -i "What tools do you have? List them briefly." 2>&1 | tee test-output/agent-openai.log
echo "Exit: $?"
```

### 2. Claude
```bash
timeout 60 pnpm vibe agent -p claude -i "What tools do you have? List them briefly." 2>&1 | tee test-output/agent-claude.log
echo "Exit: $?"
```

### 3. Gemini
```bash
timeout 60 pnpm vibe agent -p gemini -i "What tools do you have? List them briefly." 2>&1 | tee test-output/agent-gemini.log
echo "Exit: $?"
```

### 4. xAI
```bash
timeout 60 pnpm vibe agent -p xai -i "What tools do you have? List them briefly." 2>&1 | tee test-output/agent-xai.log
echo "Exit: $?"
```

### 5. Agent with tool execution
```bash
timeout 60 pnpm vibe agent -i "Create a project called agent-e2e-test in test-output/agent-project" 2>&1 | tee test-output/agent-tool.log
echo "Exit: $?"
ls test-output/agent-project/.vibe.json 2>/dev/null && echo "Project created: PASS" || echo "Project created: FAIL"
```

### 6. Agent verbose mode
```bash
timeout 60 pnpm vibe agent -i "What is 2+2?" -v 2>&1 | tee test-output/agent-verbose.log
echo "Exit: $?"
```

## Validation
For each provider test, check:
- Exit code is 0
- Output contains tool listing or meaningful response
- No crash or unhandled error

Write results to `test-output/test-agent-report.md`.
