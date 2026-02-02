#!/bin/bash
#
# VibeFrame Docker Test Runner
#
# Usage:
#   ./docker/test-workflows.sh build    # Build the Docker image
#   ./docker/test-workflows.sh shell    # Open interactive shell
#   ./docker/test-workflows.sh test     # Run all workflow tests
#   ./docker/test-workflows.sh clean    # Remove containers/images
#

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"

cd "$PROJECT_DIR"

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
RED='\033[0;31m'
DIM='\033[2m'
NC='\033[0m'

log() { echo -e "${GREEN}→${NC} $1"; }
warn() { echo -e "${YELLOW}!${NC} $1"; }
error() { echo -e "${RED}✗${NC} $1"; }

# Check if .env exists
check_env() {
  if [ ! -f ".env" ]; then
    warn "No .env file found. API keys may not be available."
    echo -e "${DIM}Copy .env.example to .env and add your API keys${NC}"
  fi
}

# Build Docker image
build() {
  log "Building Docker test image..."
  docker build -f docker/Dockerfile.test -t vibeframe-test .
  log "Build complete!"
}

# Open interactive shell
shell() {
  check_env
  log "Opening interactive shell..."

  # Create test directories
  mkdir -p docker/test-media docker/test-output

  # Source .env if exists
  if [ -f ".env" ]; then
    set -a
    source .env
    set +a
  fi

  docker run -it --rm \
    -e OPENAI_API_KEY="$OPENAI_API_KEY" \
    -e ANTHROPIC_API_KEY="$ANTHROPIC_API_KEY" \
    -e GOOGLE_API_KEY="$GOOGLE_API_KEY" \
    -e ELEVENLABS_API_KEY="$ELEVENLABS_API_KEY" \
    -e STABILITY_API_KEY="$STABILITY_API_KEY" \
    -e RUNWAY_API_SECRET="$RUNWAY_API_SECRET" \
    -e KLING_API_KEY="$KLING_API_KEY" \
    -e REPLICATE_API_TOKEN="$REPLICATE_API_TOKEN" \
    -v "$PROJECT_DIR/docker/test-media:/test/media:ro" \
    -v "$PROJECT_DIR/docker/test-output:/test/output" \
    vibeframe-test bash
}

# Run workflow tests
test_workflows() {
  check_env
  log "Running workflow tests..."

  mkdir -p docker/test-media docker/test-output

  # Source .env if exists
  if [ -f ".env" ]; then
    set -a
    source .env
    set +a
  fi

  # Run test script inside container
  docker run --rm \
    -e OPENAI_API_KEY="$OPENAI_API_KEY" \
    -e ANTHROPIC_API_KEY="$ANTHROPIC_API_KEY" \
    -e GOOGLE_API_KEY="$GOOGLE_API_KEY" \
    -e ELEVENLABS_API_KEY="$ELEVENLABS_API_KEY" \
    -e STABILITY_API_KEY="$STABILITY_API_KEY" \
    -e RUNWAY_API_SECRET="$RUNWAY_API_SECRET" \
    -e KLING_API_KEY="$KLING_API_KEY" \
    -e REPLICATE_API_TOKEN="$REPLICATE_API_TOKEN" \
    -v "$PROJECT_DIR/docker/test-media:/test/media:ro" \
    -v "$PROJECT_DIR/docker/test-output:/test/output" \
    vibeframe-test bash -c '
      echo "========================================"
      echo "VibeFrame Workflow Tests"
      echo "========================================"
      echo ""

      # Test 1: CLI Version
      echo "Test 1: CLI Version"
      vibe --version
      echo ""

      # Test 2: Help
      echo "Test 2: AI Commands"
      vibe ai --help
      echo ""

      # Test 3: Image Generation (if API keys available)
      if [ -n "$OPENAI_API_KEY" ]; then
        echo "Test 3: DALL-E Image Generation"
        vibe ai image "A sunset over mountains, digital art" -o /test/output/dalle-sunset.png
        echo ""
      else
        echo "Test 3: SKIPPED (OPENAI_API_KEY not set)"
      fi

      # Test 4: Stability Image Generation
      if [ -n "$STABILITY_API_KEY" ]; then
        echo "Test 4: Stability AI Image Generation"
        vibe ai image "A cyberpunk city at night" -o /test/output/stability-city.png -p stability
        echo ""
      else
        echo "Test 4: SKIPPED (STABILITY_API_KEY not set)"
      fi

      # Test 5: Gemini Image Generation
      if [ -n "$GOOGLE_API_KEY" ]; then
        echo "Test 5: Gemini Image Generation"
        vibe ai image "A cute robot character" -o /test/output/gemini-robot.png -p gemini
        echo ""
      else
        echo "Test 5: SKIPPED (GOOGLE_API_KEY not set)"
      fi

      # Test 6: TTS
      if [ -n "$ELEVENLABS_API_KEY" ]; then
        echo "Test 6: ElevenLabs TTS"
        vibe ai tts "Hello, this is a test of VibeFrame text to speech." -o /test/output/tts-test.mp3
        echo ""
      else
        echo "Test 6: SKIPPED (ELEVENLABS_API_KEY not set)"
      fi

      # Test 7: Sound Effects
      if [ -n "$ELEVENLABS_API_KEY" ]; then
        echo "Test 7: ElevenLabs SFX"
        vibe ai sfx "whoosh transition sound" -o /test/output/sfx-whoosh.mp3 -d 2
        echo ""
      else
        echo "Test 7: SKIPPED (ELEVENLABS_API_KEY not set)"
      fi

      echo "========================================"
      echo "Tests complete! Check /test/output for results"
      echo "========================================"
      ls -la /test/output/
    '
}

# Clean up
clean() {
  log "Cleaning up..."
  docker rmi vibeframe-test 2>/dev/null || true
  rm -rf docker/test-output/*
  log "Clean complete!"
}

# Show usage
usage() {
  echo "VibeFrame Docker Test Runner"
  echo ""
  echo "Usage: $0 <command>"
  echo ""
  echo "Commands:"
  echo "  build    Build the Docker test image"
  echo "  shell    Open interactive shell in container"
  echo "  test     Run automated workflow tests"
  echo "  clean    Remove Docker image and test outputs"
  echo ""
  echo "Example workflow:"
  echo "  $0 build   # First, build the image"
  echo "  $0 shell   # Then, open shell to test manually"
  echo ""
  echo "Inside the container, try:"
  echo "  vibe --help"
  echo "  vibe ai image \"sunset\" -o output/sunset.png"
  echo "  vibe ai highlights video.mp4 --use-gemini"
}

# Main
case "${1:-}" in
  build)
    build
    ;;
  shell)
    shell
    ;;
  test)
    test_workflows
    ;;
  clean)
    clean
    ;;
  *)
    usage
    ;;
esac
