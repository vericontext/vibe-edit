# VibeEdit Roadmap

Overall project roadmap and milestone tracking.

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

---

## Phase 2: AI Integration 🚧

Connect AI providers and enable natural language editing.

- [x] AI Provider interface design
- [x] Provider registry system
- [ ] Whisper integration for subtitles (API ready, UI pending)
- [ ] Gemini auto-edit suggestions (basic parser done, LLM integration pending)
- [ ] Natural language command parser (regex-based, needs LLM upgrade)
- [ ] Real-time transcription display

---

## Phase 3: Video Processing 📋

Actual video rendering and export capabilities.

- [ ] WebCodecs API integration
- [ ] FFmpeg.wasm for encoding
- [ ] Real-time effect preview
- [ ] Export pipeline (MP4, WebM)
- [ ] Quality presets (draft, standard, high, ultra)

---

## Phase 4: Advanced Features 📋

Power user features and collaboration.

- [ ] Beat sync (auto-cut to music beats)
- [ ] Real-time collaboration
- [ ] Template system
- [ ] Plugin marketplace
- [ ] Keyboard shortcuts customization

---

## Legend

- ✅ Completed
- 🚧 In Progress
- 📋 Planned
