# VibeEdit Roadmap

**Vision**: The open-source standard for AI-native video editing.

---

## Phase 1: Foundation (MVP) ✅

Core infrastructure and basic editing capabilities.

- [x] Turborepo monorepo setup
- [x] Next.js 14 app with App Router
- [x] Core timeline data structures (Zustand + Immer)
- [x] Basic UI components (Radix UI + Tailwind)
- [x] Drag-and-drop timeline
- [x] Video preview with playback controls
- [x] Media library with upload
- [x] CLI package for headless operations
- [x] FFmpeg.wasm export pipeline

---

## Phase 2: AI Provider Integration 🚧

Unified interface for AI services.

### Text / Language
- [x] Provider interface design
- [x] Provider registry system
- [ ] **OpenAI GPT** - Natural language commands, script generation
- [ ] **Gemini** - Multimodal understanding, auto-edit suggestions
- [ ] **Claude** - Long-form content analysis, timeline planning

### Audio
- [ ] **Whisper** - Speech-to-text, auto-subtitles
- [ ] **ElevenLabs** - Text-to-speech, voice cloning
- [ ] **Suno** - AI music generation
- [ ] Beat detection & sync

### Image
- [ ] **DALL-E** - Thumbnail generation, image editing
- [ ] **Midjourney** (via API) - Concept art, storyboards
- [ ] **Stable Diffusion** - Local image generation
- [ ] Background removal / replacement

### Video
- [ ] **Runway Gen-3** - Video generation, inpainting
- [ ] **Kling** - Video generation
- [ ] **Pika** - Video-to-video transformation
- [ ] **HeyGen** - AI avatars, lip sync
- [ ] Scene detection & auto-cutting

---

## Phase 3: MCP Integration 📋

Model Context Protocol for extensible AI workflows.

- [ ] MCP server implementation for VibeEdit
- [ ] Tool definitions (timeline manipulation, export, effects)
- [ ] Resource providers (project files, media assets)
- [ ] Prompt templates for common editing tasks
- [ ] Claude Desktop / Cursor integration
- [ ] Custom MCP server for third-party AI tools

**Example MCP tools:**
```
vibe://tools/add-clip
vibe://tools/apply-effect
vibe://tools/export
vibe://resources/project/{id}
vibe://prompts/edit-suggestions
```

---

## Phase 4: AI-Native Editing 📋

Intelligence built into every interaction.

- [ ] Natural language timeline control ("trim last 3 seconds")
- [ ] Auto-reframe for different aspect ratios
- [ ] Smart scene detection & chapter markers
- [ ] AI color grading suggestions
- [ ] Automatic B-roll suggestions
- [ ] Content-aware speed ramping
- [ ] AI-powered audio ducking
- [ ] Auto-generate shorts from long-form content

---

## Phase 5: Advanced Features 📋

Power user features and ecosystem.

### Collaboration
- [ ] Real-time multiplayer editing
- [ ] Version history & branching
- [ ] Comments & review workflow
- [ ] Team workspaces

### Ecosystem
- [ ] Plugin marketplace
- [ ] Template library
- [ ] Effect presets sharing
- [ ] Community AI prompts

### Developer Experience
- [ ] REST API for automation
- [ ] Webhooks for CI/CD pipelines
- [ ] SDK for custom integrations
- [ ] Headless rendering service

---

## Phase 6: Scale 📋

Enterprise and platform features.

- [ ] Self-hosted deployment option
- [ ] S3/GCS media storage
- [ ] Distributed rendering
- [ ] Usage analytics
- [ ] White-label solution

---

## CLI Status

**101 tests passing** (51 unit + 50 integration)

```
vibe project    create | info | set
vibe timeline   add-source | add-clip | add-track | add-effect | trim | list
                split | duplicate | delete | move
vibe batch      import | concat | apply-effect | remove-clips | info
vibe media      info | duration
vibe export     <project> -o <output> -p <preset>
vibe ai         providers | transcribe | suggest
```

---

## Design Principles

1. **AI-Native** - AI is not a feature, it's the foundation
2. **Open Source** - Community-driven development
3. **Headless First** - CLI/API before UI
4. **Provider Agnostic** - Swap AI providers freely
5. **MCP Compatible** - Standard protocol for AI tools
6. **Local First** - Works offline, sync when online

---

## Legend

- ✅ Completed
- 🚧 In Progress
- 📋 Planned
