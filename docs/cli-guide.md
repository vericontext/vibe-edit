# VibeFrame CLI Guide

Complete guide to using VibeFrame's command-line interface for AI-powered video editing.

---

## Installation

```bash
# Create a new directory and install
mkdir vibeframe-test && cd vibeframe-test
curl -fsSL https://raw.githubusercontent.com/vericontext/vibeframe/main/scripts/install.sh | bash
```

**Requirements:**
- Node.js 18+
- Git
- FFmpeg (recommended)

---

## Quick Start: First 5 Minutes

### Step 1: Verify Installation

```bash
vibe --version
# Expected: 0.1.0

vibe --help
# Shows all available commands
```

### Step 2: Configure API Keys

**Option A: Interactive Setup**
```bash
vibe setup
```

**Option B: Environment Variables**
```bash
# Minimum for testing (Gemini covers image + video analysis)
export GOOGLE_API_KEY="AIza..."

# Full setup
export GOOGLE_API_KEY="AIza..."          # Gemini (image gen, video analysis)
export ELEVENLABS_API_KEY="..."          # TTS, SFX
export ANTHROPIC_API_KEY="sk-ant-..."    # Claude (storyboard, highlights)
export OPENAI_API_KEY="sk-..."           # Whisper (transcription), DALL-E
export STABILITY_API_KEY="sk-..."        # Stable Diffusion
```

### Step 3: Test AI Features (CLI Mode)

```bash
# Test 1: Image Generation (Gemini)
vibe ai image "a friendly robot mascot, 3D render style" -o test-image.png

# Test 2: Text-to-Speech (ElevenLabs)
vibe ai tts "Welcome to VibeFrame, the AI video editor." -o test-tts.mp3

# Test 3: Sound Effect (ElevenLabs)
vibe ai sfx "magical sparkle sound" -o test-sfx.mp3 -d 2
```

### Step 4: Test REPL Mode (Natural Language)

```bash
vibe
```

REPL에서는 자연어로 말하면 LLM이 알아서 명령어로 변환합니다:

```
vibe> 새 프로젝트 만들어줘
# → vibe project create "새 프로젝트"

vibe> intro.mp4 파일 추가해
# → vibe timeline add-source intro.mp4

vibe> 첫번째 클립 5초로 잘라줘
# → vibe timeline trim clip-1 -d 5

vibe> 모든 클립에 페이드인 효과 넣어줘
# → vibe batch apply-effect fadeIn --all

vibe> 영상 내보내기
# → vibe export output.mp4
```

---

## Two Ways to Use VibeFrame

### 1. CLI Mode (Direct Commands)

터미널에서 직접 명령어 실행. 스크립팅과 자동화에 적합.

```bash
# 직접 명령어 실행
vibe ai image "sunset" -o sunset.png
vibe project create "my-video" -o project.vibe.json
vibe export project.vibe.json -o output.mp4
```

### 2. REPL Mode (Natural Language)

대화형 모드. 자연어로 말하면 LLM이 명령어로 변환.

```bash
vibe  # REPL 시작
```

```
vibe> 일몰 이미지 만들어서 sunset.png로 저장해
vibe> my-video라는 프로젝트 새로 만들어
vibe> 영상 내보내기 해줘
```

---

## AI Commands Reference

### Image Generation

**CLI Mode:**
```bash
# Gemini (기본값) - 빠르고 고품질
vibe ai image "cute cat illustration" -o cat.png

# 세로 비율 (9:16)
vibe ai image "phone wallpaper, aurora" -o wallpaper.png -r 9:16

# 가로 비율 (16:9)
vibe ai image "cinematic landscape" -o landscape.png -r 16:9

# DALL-E 사용
vibe ai image "abstract art" -o art.png -p dalle

# Stability AI 사용 (사실적인 이미지)
vibe ai image "professional headshot" -o headshot.png -p stability
```

**REPL Mode:**
```
vibe> 고양이 일러스트 만들어줘
vibe> 오로라 배경 세로 이미지 생성해서 wallpaper.png로 저장
vibe> DALL-E로 추상화 그려줘
```

**기본값:**
| 옵션 | 기본값 |
|------|--------|
| `--provider` | `gemini` |
| `--ratio` | `1:1` |
| `--size` (DALL-E) | `1024x1024` |

---

### Text-to-Speech (TTS)

**CLI Mode:**
```bash
# 기본 음성 (Rachel)
vibe ai tts "안녕하세요, 바이브프레임입니다." -o greeting.mp3

# 음성 목록 확인
vibe ai voices

# 특정 음성 사용 (Bella - 부드러운 여성)
vibe ai tts "Welcome to our channel" -o intro.mp3 -v EXAVITQu4vr4xnSDxMaL

# 긴 나레이션
vibe ai tts "This is a longer narration for a video. It explains the product features in detail." -o narration.mp3
```

**REPL Mode:**
```
vibe> "안녕하세요" 음성으로 만들어줘
vibe> 사용 가능한 음성 목록 보여줘
vibe> Bella 목소리로 인트로 나레이션 만들어
```

**기본값:**
| 옵션 | 기본값 |
|------|--------|
| `--voice` | `Rachel` (21m00Tcm4TlvDq8ikWAM) |
| `--output` | `output.mp3` |

---

### Sound Effects (SFX)

**CLI Mode:**
```bash
# 트랜지션 효과음
vibe ai sfx "whoosh transition" -o whoosh.mp3 -d 2

# 알림음
vibe ai sfx "notification ding" -o ding.mp3 -d 1

# 환경음
vibe ai sfx "rain on window" -o rain.mp3 -d 10

# 임팩트 사운드
vibe ai sfx "cinematic boom impact" -o boom.mp3 -d 3

# 타이핑 소리
vibe ai sfx "keyboard typing" -o typing.mp3 -d 5
```

**REPL Mode:**
```
vibe> 휙 하는 트랜지션 효과음 만들어줘
vibe> 비 오는 소리 10초짜리 생성해
vibe> 영화같은 임팩트 사운드 만들어
```

**기본값:**
| 옵션 | 기본값 |
|------|--------|
| `--duration` | auto (AI가 결정) |
| `--output` | `sound-effect.mp3` |

---

### Transcription (음성→자막)

**CLI Mode:**
```bash
# SRT 자막 생성
vibe ai transcribe interview.mp3 -o subtitles.srt

# VTT 형식
vibe ai transcribe podcast.mp3 -o subtitles.vtt

# 한국어 힌트
vibe ai transcribe korean-audio.mp3 -o subs.srt -l ko

# 영어 힌트
vibe ai transcribe english-audio.mp3 -o subs.srt -l en
```

**REPL Mode:**
```
vibe> interview.mp3 자막 만들어줘
vibe> 팟캐스트 음성 VTT 형식으로 변환해
vibe> 한국어 오디오 자막 추출해
```

---

### Video Generation (Image-to-Video)

**CLI Mode:**
```bash
# Runway Gen-3 (기본)
vibe ai video "camera slowly zooms in, cinematic" -i photo.png -o video.mp4

# Kling AI
vibe ai kling "dramatic lighting change" -i scene.png -o dramatic.mp4

# 생성 상태 확인
vibe ai video-status abc123

# 생성 취소
vibe ai video-cancel abc123
```

**REPL Mode:**
```
vibe> photo.png를 영상으로 만들어줘, 천천히 줌인하는 느낌으로
vibe> Kling으로 드라마틱한 영상 생성해
vibe> 영상 생성 상태 확인해줘
```

---

## Advanced Workflows

### 1. Script-to-Video (스크립트→영상)

텍스트 스크립트를 이미지/영상으로 자동 변환.

**CLI Mode:**
```bash
# 이미지만 생성 (빠른 테스트)
vibe ai script-to-video "우주 탐험 이야기. 로켓 발사. 우주 비행사. 지구 전경." \
  -o ./space-video/ \
  --images-only \
  --no-voiceover

# Gemini 이미지 + 나레이션
vibe ai script-to-video "제품 소개. 대시보드 화면. 리포트 생성. 가입 유도." \
  -o ./demo/ \
  --image-provider gemini

# DALL-E 이미지 사용
vibe ai script-to-video "판타지 세계. 마법의 숲. 용과 기사." \
  -o ./fantasy/ \
  --image-provider dalle \
  --images-only

# Stability AI 이미지 (사실적)
vibe ai script-to-video "요리 레시피. 재료 준비. 조리 과정. 완성된 요리." \
  -o ./cooking/ \
  --image-provider stability \
  --images-only
```

**REPL Mode:**
```
vibe> "우주 탐험 이야기" 스크립트로 영상 만들어줘
vibe> 제품 소개 스크립트를 Gemini 이미지로 생성해
vibe> 요리 레시피 영상 만들어줘, 사실적인 이미지로
```

**Output:**
```
./space-video/
├── storyboard.json      # 씬 구성
├── scene-1.png          # 로켓 발사
├── scene-2.png          # 우주 비행사
├── scene-3.png          # 지구 전경
├── voiceover.mp3        # 나레이션 (옵션)
└── project.vibe.json    # 프로젝트 파일
```

---

### 2. Highlights Extraction (하이라이트 추출)

긴 영상에서 베스트 장면 자동 추출.

**CLI Mode:**
```bash
# 기본 (Whisper + Claude, 오디오 분석)
vibe ai highlights lecture.mp4 -o highlights.json

# Gemini Video (시각 + 오디오 분석) - 권장
vibe ai highlights lecture.mp4 -o highlights.json --use-gemini

# 감정적인 순간만
vibe ai highlights wedding.mp4 -o highlights.json --use-gemini --criteria emotional

# 정보성 순간만
vibe ai highlights tutorial.mp4 -o highlights.json --use-gemini --criteria informative

# 웃긴 순간만
vibe ai highlights comedy.mp4 -o highlights.json --use-gemini --criteria funny

# 최대 5개, 신뢰도 80% 이상
vibe ai highlights video.mp4 -o highlights.json --use-gemini -n 5 -t 0.8

# 60초 하이라이트 릴 목표
vibe ai highlights video.mp4 -o highlights.json --use-gemini -d 60

# 긴 영상 (저해상도 모드)
vibe ai highlights long-video.mp4 -o highlights.json --use-gemini --low-res

# 프로젝트 파일로 생성
vibe ai highlights event.mp4 -o hl.json -p highlight-reel.vibe.json --use-gemini
```

**REPL Mode:**
```
vibe> 강의 영상에서 하이라이트 추출해줘
vibe> 결혼식 영상에서 감동적인 순간들 찾아줘
vibe> 튜토리얼에서 중요한 부분만 뽑아줘
vibe> 이 영상에서 웃긴 순간 5개 찾아줘
```

**Output (highlights.json):**
```json
{
  "sourceFile": "lecture.mp4",
  "totalDuration": 3600,
  "highlights": [
    {
      "startTime": 120.5,
      "endTime": 145.2,
      "duration": 24.7,
      "category": "informative",
      "confidence": 0.95,
      "reason": "핵심 개념 설명",
      "transcript": "이 부분이 가장 중요합니다..."
    }
  ]
}
```

---

### 3. Auto-Shorts (자동 숏폼 생성)

긴 영상을 TikTok/Reels/Shorts용 클립으로 자동 변환.

**CLI Mode:**
```bash
# 분석만 (미리보기)
vibe ai auto-shorts podcast.mp4 -n 5 --analyze-only --use-gemini

# TikTok/Reels용 (9:16)
vibe ai auto-shorts podcast.mp4 \
  -n 3 \
  -d 30 \
  --output-dir ./shorts/ \
  --use-gemini \
  -a 9:16

# YouTube Shorts용 (60초)
vibe ai auto-shorts interview.mp4 \
  -n 5 \
  -d 60 \
  --output-dir ./yt-shorts/ \
  --use-gemini \
  -a 9:16

# Instagram 정사각형
vibe ai auto-shorts vlog.mp4 \
  -n 3 \
  -d 45 \
  --output-dir ./insta/ \
  --use-gemini \
  -a 1:1

# 긴 영상 (저해상도 모드)
vibe ai auto-shorts webinar.mp4 \
  -n 5 \
  --output-dir ./clips/ \
  --use-gemini \
  --low-res
```

**REPL Mode:**
```
vibe> 팟캐스트에서 숏폼 3개 만들어줘
vibe> 인터뷰 영상 틱톡용으로 잘라줘
vibe> 브이로그에서 인스타 정사각형 클립 만들어
vibe> 이 영상에서 바이럴 될만한 순간 찾아줘
```

**Output:**
```
./shorts/
├── podcast-short-1.mp4   # 608x1080 (9:16), 30초
├── podcast-short-2.mp4   # 608x1080 (9:16), 28초
└── podcast-short-3.mp4   # 608x1080 (9:16), 32초
```

---

### 4. Gemini Video Analysis (비디오 분석)

Gemini로 비디오 내용 분석 및 Q&A.

**CLI Mode:**
```bash
# 요약
vibe ai gemini-video video.mp4 "이 영상을 3줄로 요약해줘"

# 타임스탬프 추출
vibe ai gemini-video tutorial.mp4 "주요 단계별 타임스탬프 알려줘"

# 질문 답변
vibe ai gemini-video product.mp4 "이 영상에 나오는 제품 이름이 뭐야?"

# YouTube URL 분석
vibe ai gemini-video "https://youtube.com/watch?v=xxx" "영상 주제가 뭐야?"

# 액션 영상 (높은 FPS)
vibe ai gemini-video sports.mp4 "득점 장면 찾아줘" --fps 5

# 특정 구간 분석
vibe ai gemini-video movie.mp4 "이 장면에서 무슨 일이 일어나?" --start 60 --end 120

# 긴 영상 (저해상도)
vibe ai gemini-video lecture.mp4 "강의 목차 만들어줘" --low-res
```

**REPL Mode:**
```
vibe> 이 영상 요약해줘
vibe> 튜토리얼 타임스탬프 뽑아줘
vibe> 영상에 나오는 제품이 뭐야?
vibe> 유튜브 영상 분석해줘
vibe> 60초부터 2분까지 무슨 내용이야?
```

---

## Image Editing (Stability AI)

**CLI Mode:**
```bash
# 업스케일 (4배)
vibe ai sd-upscale small.png -o large.png -s 4

# 배경 제거
vibe ai sd-remove-bg photo.png -o no-bg.png

# 이미지 변환
vibe ai sd-img2img photo.png "수채화 스타일로 변환" -o watercolor.png
vibe ai sd-img2img photo.png "사이버펑크 스타일" -o cyberpunk.png
vibe ai sd-img2img photo.png "애니메이션 스타일" -o anime.png

# 객체 교체
vibe ai sd-replace photo.png "자동차" "오토바이" -o replaced.png
vibe ai sd-replace room.png "의자" "소파" -o new-room.png

# 아웃페인팅 (이미지 확장)
vibe ai sd-outpaint photo.png --left 200 --right 200 -o wider.png
vibe ai sd-outpaint portrait.png --up 100 --down 100 -o taller.png
```

**REPL Mode:**
```
vibe> 이미지 4배 업스케일해줘
vibe> 사진 배경 제거해줘
vibe> 이 사진 수채화 스타일로 바꿔줘
vibe> 사진에서 자동차를 오토바이로 바꿔
vibe> 이미지 좌우로 넓혀줘
```

---

## Project Management

### Creating Projects

**CLI Mode:**
```bash
vibe project create "My Video" -o project.vibe.json
vibe project info project.vibe.json
vibe project set project.vibe.json --name "New Name"
```

**REPL Mode:**
```
vibe> 새 프로젝트 만들어줘
vibe> 프로젝트 정보 보여줘
vibe> 프로젝트 이름 바꿔줘
```

### Timeline Operations

**CLI Mode:**
```bash
# 소스 추가
vibe timeline add-source project.vibe.json intro.mp4 -d 30

# 클립 추가
vibe timeline add-clip project.vibe.json source-1 -s 0 -d 10

# 이펙트 추가
vibe timeline add-effect project.vibe.json clip-1 fadeIn -d 1

# 타임라인 보기
vibe timeline list project.vibe.json

# 클립 트림
vibe timeline trim project.vibe.json clip-1 -d 5

# 클립 분할
vibe timeline split project.vibe.json clip-1 -t 3

# 클립 삭제
vibe timeline delete project.vibe.json clip-1
```

**REPL Mode:**
```
vibe> intro.mp4 추가해
vibe> 첫번째 소스로 10초 클립 만들어
vibe> clip-1에 페이드인 넣어줘
vibe> 타임라인 보여줘
vibe> 첫번째 클립 5초로 줄여줘
vibe> 클립을 3초 지점에서 나눠줘
vibe> 마지막 클립 삭제해
```

### Batch Operations

**CLI Mode:**
```bash
vibe batch import project.vibe.json ./videos/ --filter ".mp4"
vibe batch concat project.vibe.json --all
vibe batch apply-effect project.vibe.json fadeIn --all
```

**REPL Mode:**
```
vibe> videos 폴더의 mp4 파일 다 가져와
vibe> 모든 클립 연결해
vibe> 전체 클립에 페이드인 적용해
```

### Export

**CLI Mode:**
```bash
vibe export project.vibe.json -o output.mp4 -p standard
vibe export project.vibe.json -o output.mp4 -p high -y
```

**REPL Mode:**
```
vibe> 영상 내보내기
vibe> 고화질로 내보내줘
vibe> output.mp4로 저장해
```

**Presets:**
| Preset | Resolution |
|--------|------------|
| `draft` | 360p |
| `standard` | 720p |
| `high` | 1080p |
| `ultra` | 4K |

---

## Complete Workflow Examples

### Example A: 팟캐스트 → 숏폼 클립

```bash
# 1. 폴더 생성
mkdir podcast-shorts && cd podcast-shorts

# 2. 분석 (미리보기)
vibe ai auto-shorts ../podcast.mp4 -n 5 --analyze-only --use-gemini

# 3. 숏폼 생성
vibe ai auto-shorts ../podcast.mp4 \
  -n 5 \
  -d 45 \
  --output-dir ./ \
  --use-gemini \
  -a 9:16

# 4. 결과 확인
ls -la
```

**REPL로 하기:**
```
vibe> podcast.mp4에서 바이럴 될만한 순간 5개 찾아줘
vibe> 찾은 순간들 틱톡용 세로 영상으로 만들어줘
```

### Example B: 스크립트 → 제품 데모

```bash
# 1. 폴더 생성
mkdir demo && cd demo

# 2. 스크립트로 이미지 생성
vibe ai script-to-video "제품 소개. 대시보드. 리포트. 가입 유도." \
  -o ./ \
  --image-provider gemini \
  --images-only

# 3. 나레이션 추가
vibe ai tts "새로운 대시보드를 소개합니다. 한눈에 모든 데이터를 확인하세요." \
  -o narration.mp3

# 4. 배경음악 추가
vibe ai sfx "upbeat corporate music" -o bgm.mp3 -d 30

# 5. 결과 확인
ls -la
```

**REPL로 하기:**
```
vibe> "제품 소개 영상" 스크립트로 이미지 만들어줘
vibe> 나레이션 음성 생성해줘
vibe> 배경음악 만들어줘
```

### Example C: 이벤트 → 하이라이트 릴

```bash
# 1. 하이라이트 추출
vibe ai highlights event.mp4 \
  -o highlights.json \
  -p reel.vibe.json \
  --use-gemini \
  --criteria emotional \
  -d 120

# 2. 프로젝트 확인
vibe project info reel.vibe.json

# 3. 내보내기
vibe export reel.vibe.json -o highlight-reel.mp4 -p high
```

**REPL로 하기:**
```
vibe> event.mp4에서 감동적인 순간들 찾아서 2분짜리 하이라이트 만들어줘
vibe> 프로젝트 정보 보여줘
vibe> 고화질로 내보내기 해줘
```

---

## Configuration

### Config File Location
```
~/.vibeframe/config.yaml
```

### Example Configuration
```yaml
version: "1.0.0"
llm:
  provider: claude          # claude, openai, gemini, ollama
providers:
  anthropic: sk-ant-...     # Claude
  openai: sk-...            # GPT, Whisper, DALL-E
  google: AIza...           # Gemini
  elevenlabs: ...           # TTS, SFX
  stability: sk-...         # Stable Diffusion
  runway: ...               # Video generation
  kling: ...                # Video generation
defaults:
  aspectRatio: "16:9"
  exportQuality: standard
```

### Environment Variables
```bash
export GOOGLE_API_KEY="AIza..."          # Gemini (image, video analysis)
export ELEVENLABS_API_KEY="..."          # TTS, SFX
export ANTHROPIC_API_KEY="sk-ant-..."    # Claude
export OPENAI_API_KEY="sk-..."           # Whisper, DALL-E
export STABILITY_API_KEY="sk-..."        # Stable Diffusion
export RUNWAY_API_SECRET="..."           # Runway
export KLING_API_KEY="..."               # Kling
```

---

## Troubleshooting

### "Command not found: vibe"
```bash
curl -fsSL https://raw.githubusercontent.com/vericontext/vibeframe/main/scripts/install.sh | bash
```

### "FFmpeg not found"
```bash
# macOS
brew install ffmpeg

# Ubuntu/Debian
sudo apt install ffmpeg
```

### "API key invalid"
```bash
vibe setup  # 다시 설정
```

### Video analysis fails (large files)
```bash
vibe ai highlights video.mp4 --use-gemini --low-res
```

---

## Getting Help

```bash
vibe --help              # 전체 명령어
vibe ai --help           # AI 명령어
vibe ai image --help     # 특정 명령어
```

- **GitHub:** https://github.com/vericontext/vibeframe
- **Issues:** https://github.com/vericontext/vibeframe/issues
