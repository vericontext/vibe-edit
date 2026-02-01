# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

VibeEdit is an AI-first web-based video editor that prioritizes natural language commands over traditional UI. The philosophy is "Buttons < Agents" - users describe what they want and AI handles the editing.

## Development Commands

```bash
pnpm install          # Install all dependencies
pnpm dev              # Start development server (runs all packages)
pnpm build            # Build all packages for production
pnpm test             # Run tests across all packages
pnpm lint             # Run ESLint checks
pnpm format           # Format code with Prettier

# Run tests for a single package
pnpm --filter @vibe-edit/core test
pnpm --filter @vibe-edit/ai-providers test

# Build a single package
pnpm --filter @vibe-edit/core build
```

## CLI Commands

```bash
pnpm vibe --help                    # Show all commands

# Project management
pnpm vibe project create <name>     # Create new project file
pnpm vibe project info <file>       # Show project info
pnpm vibe project set <file>        # Update project settings

# Timeline editing
pnpm vibe timeline add-source <project> <media>   # Add media source
pnpm vibe timeline add-clip <project> <source-id> # Add clip to timeline
pnpm vibe timeline add-track <project> <type>     # Add video/audio track
pnpm vibe timeline add-effect <project> <clip-id> <type>  # Add effect
pnpm vibe timeline trim <project> <clip-id>       # Trim clip
pnpm vibe timeline list <project>                 # List contents

# AI providers
pnpm vibe ai providers              # List available AI providers
pnpm vibe ai transcribe <audio>     # Transcribe audio with Whisper
pnpm vibe ai suggest <project> <instruction>  # Get AI edit suggestions
```

## Architecture

### Monorepo Structure (Turborepo + pnpm workspaces)

- **apps/web**: Next.js 14 application (App Router) - the main editor UI
- **packages/core**: Core video editing logic and state management
- **packages/cli**: Command-line interface for headless operations
- **packages/ui**: Shared Radix UI components with Tailwind CSS
- **packages/ai-providers**: Pluggable AI provider system

### State Management

**Web (Zustand)**: Central store in `packages/core/src/timeline/store.ts`
- `useTimelineStore` - main store with all actions
- Selector hooks: `usePlaybackState()`, `useTracks()`, `useClips()`, `useSources()`, `useZoom()`

**CLI (Headless)**: `Project` class in `packages/cli/src/engine/project.ts`
- Pure TypeScript, no React/Zustand dependency
- Same operations as Zustand store but for headless use
- Serializes to `.vibe.json` project files

ID generation: `${Date.now()}-${Math.random().toString(36).slice(2, 11)}`

### AI Provider Plugin System

Located in `packages/ai-providers/src/interface/`:
- `AIProvider` interface defines capabilities (text-to-video, speech-to-text, auto-edit, etc.)
- `AIProviderRegistry` manages provider registration and lookup by capability
- Providers: Whisper (transcription), Gemini (auto-edit), Runway Gen-4, Kling 2.x (video generation)

### Web App Layout (apps/web)

4-panel layout: Header → Sidebar (MediaLibrary) + Center (Preview + Timeline) + Sidebar (ChatPanel)
- `components/timeline/` - Timeline editor with tracks, clips, ruler
- `components/preview/` - Canvas-based video preview with playback controls
- `components/library/` - Media library with drag-and-drop upload
- `components/chat/` - Natural language command interface

## Type Conventions

```typescript
type Id = string;
type TimeSeconds = number;
type MediaType = "video" | "audio" | "image";
type AspectRatio = "16:9" | "9:16" | "1:1" | "4:5";
```

## Vibe Terminology

The project uses friendly terms instead of traditional video editing jargon:
- Timeline → 스토리보드, Clip → 조각, Track → 겹침, Keyframe → 포인트
- Render → 내보내기, Transition → 전환, Trim → 자르기

## Code Style

- Conventional commits: `feat:`, `fix:`, `docs:`, `style:`, `refactor:`, `test:`, `chore:`
- Client components use `"use client"` directive
- Styling: Tailwind CSS + CVA (class-variance-authority) + clsx + tailwind-merge
- Components use Radix UI primitives from `@vibe-edit/ui`
