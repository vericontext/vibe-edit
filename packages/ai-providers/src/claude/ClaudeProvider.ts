import type { Clip } from "@vibe-edit/core";
import type {
  AIProvider,
  AICapability,
  ProviderConfig,
  EditSuggestion,
} from "../interface/types";

/**
 * Motion graphic generation options
 */
export interface MotionOptions {
  /** Duration in seconds */
  duration?: number;
  /** Width in pixels */
  width?: number;
  /** Height in pixels */
  height?: number;
  /** Frame rate */
  fps?: number;
  /** Style preset */
  style?: "minimal" | "corporate" | "playful" | "cinematic";
}

/**
 * Generated Remotion component
 */
export interface RemotionComponent {
  /** Component name */
  name: string;
  /** JSX/TSX code */
  code: string;
  /** Duration in frames */
  durationInFrames: number;
  /** Frame rate */
  fps: number;
  /** Width */
  width: number;
  /** Height */
  height: number;
  /** Description of what was generated */
  description: string;
}

/**
 * Motion graphic generation result
 */
export interface MotionResult {
  success: boolean;
  /** Generated Remotion component */
  component?: RemotionComponent;
  /** Error message if failed */
  error?: string;
}

/**
 * Storyboard segment
 */
export interface StoryboardSegment {
  /** Segment index */
  index: number;
  /** Start time in seconds */
  startTime: number;
  /** Duration in seconds */
  duration: number;
  /** Description of what happens */
  description: string;
  /** Suggested visuals */
  visuals: string;
  /** Suggested audio/music */
  audio?: string;
  /** Text overlays */
  textOverlays?: string[];
}

/**
 * Claude provider for AI-powered content creation
 */
export class ClaudeProvider implements AIProvider {
  id = "claude";
  name = "Anthropic Claude";
  description = "AI-powered motion graphics, content analysis, and storyboarding";
  capabilities: AICapability[] = ["auto-edit", "natural-language-command"];
  iconUrl = "/icons/claude.svg";
  isAvailable = true;

  private apiKey?: string;
  private baseUrl = "https://api.anthropic.com/v1";
  private model = "claude-sonnet-4-20250514";

  async initialize(config: ProviderConfig): Promise<void> {
    this.apiKey = config.apiKey;
    if (config.baseUrl) {
      this.baseUrl = config.baseUrl;
    }
  }

  isConfigured(): boolean {
    return !!this.apiKey;
  }

  /**
   * Generate Remotion motion graphic component from natural language
   */
  async generateMotion(
    description: string,
    options: MotionOptions = {}
  ): Promise<MotionResult> {
    if (!this.apiKey) {
      return {
        success: false,
        error: "Claude API key not configured",
      };
    }

    const width = options.width || 1920;
    const height = options.height || 1080;
    const fps = options.fps || 30;
    const duration = options.duration || 5;
    const durationInFrames = Math.round(duration * fps);

    const systemPrompt = `You are an expert Remotion developer. Generate a React component for motion graphics.

Requirements:
- Use Remotion's useCurrentFrame(), useVideoConfig(), interpolate(), spring() hooks
- Component should be self-contained with inline styles
- Use TypeScript
- Canvas size: ${width}x${height}, ${fps}fps, ${durationInFrames} frames (${duration}s)
- Style: ${options.style || "modern and clean"}

Available Remotion imports:
- useCurrentFrame, useVideoConfig, interpolate, spring, Easing from 'remotion'
- AbsoluteFill, Sequence from 'remotion'

Respond with JSON only:
{
  "name": "ComponentName",
  "code": "import { useCurrentFrame, ... } from 'remotion';\\n\\nexport const ComponentName: React.FC = () => { ... }",
  "description": "What this animation does"
}`;

    try {
      const response = await fetch(`${this.baseUrl}/messages`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          "x-api-key": this.apiKey,
          "anthropic-version": "2023-06-01",
        },
        body: JSON.stringify({
          model: this.model,
          max_tokens: 4096,
          messages: [
            {
              role: "user",
              content: `Create a Remotion motion graphic: "${description}"`,
            },
          ],
          system: systemPrompt,
        }),
      });

      if (!response.ok) {
        const error = await response.text();
        console.error("Claude API error:", error);
        return {
          success: false,
          error: `API error: ${response.status}`,
        };
      }

      const data = (await response.json()) as {
        content: Array<{ type: string; text?: string }>;
      };

      const text = data.content.find((c) => c.type === "text")?.text;
      if (!text) {
        return {
          success: false,
          error: "No response from Claude",
        };
      }

      // Extract JSON from response
      const jsonMatch = text.match(/\{[\s\S]*\}/);
      if (!jsonMatch) {
        return {
          success: false,
          error: "Could not parse response",
        };
      }

      const result = JSON.parse(jsonMatch[0]) as {
        name: string;
        code: string;
        description: string;
      };

      return {
        success: true,
        component: {
          name: result.name,
          code: result.code,
          durationInFrames,
          fps,
          width,
          height,
          description: result.description,
        },
      };
    } catch (error) {
      return {
        success: false,
        error: error instanceof Error ? error.message : "Unknown error",
      };
    }
  }

  /**
   * Analyze long-form content and generate storyboard
   */
  async analyzeContent(
    content: string,
    targetDuration?: number
  ): Promise<StoryboardSegment[]> {
    if (!this.apiKey) {
      return [];
    }

    const systemPrompt = `You are a video editor analyzing content to create a storyboard.
Break down the content into visual segments suitable for a video.
${targetDuration ? `Target total duration: ${targetDuration} seconds` : ""}

Respond with JSON array:
[
  {
    "index": 0,
    "startTime": 0,
    "duration": 5,
    "description": "What happens in this segment",
    "visuals": "Suggested visuals/footage",
    "audio": "Suggested audio/music",
    "textOverlays": ["Text to show on screen"]
  }
]`;

    try {
      const response = await fetch(`${this.baseUrl}/messages`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          "x-api-key": this.apiKey,
          "anthropic-version": "2023-06-01",
        },
        body: JSON.stringify({
          model: this.model,
          max_tokens: 4096,
          messages: [
            {
              role: "user",
              content: `Analyze this content and create a video storyboard:\n\n${content}`,
            },
          ],
          system: systemPrompt,
        }),
      });

      if (!response.ok) {
        return [];
      }

      const data = (await response.json()) as {
        content: Array<{ type: string; text?: string }>;
      };

      const text = data.content.find((c) => c.type === "text")?.text;
      if (!text) return [];

      const jsonMatch = text.match(/\[[\s\S]*\]/);
      if (!jsonMatch) return [];

      return JSON.parse(jsonMatch[0]) as StoryboardSegment[];
    } catch {
      return [];
    }
  }

  /**
   * Get edit suggestions using Claude (implements AIProvider interface)
   */
  async autoEdit(clips: Clip[], instruction: string): Promise<EditSuggestion[]> {
    if (!this.apiKey) {
      return [];
    }

    const clipsInfo = clips.map((clip) => ({
      id: clip.id,
      startTime: clip.startTime,
      duration: clip.duration,
      effects: clip.effects?.map((e) => e.type) || [],
    }));

    const systemPrompt = `You are a video editor. Analyze clips and suggest edits.

Respond with JSON array:
[
  {
    "type": "trim|cut|add-effect|reorder|delete|split|merge",
    "description": "What this edit does",
    "clipIds": ["clip-id"],
    "params": {},
    "confidence": 0.9
  }
]`;

    try {
      const response = await fetch(`${this.baseUrl}/messages`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          "x-api-key": this.apiKey,
          "anthropic-version": "2023-06-01",
        },
        body: JSON.stringify({
          model: this.model,
          max_tokens: 2048,
          messages: [
            {
              role: "user",
              content: `Clips: ${JSON.stringify(clipsInfo)}\n\nInstruction: ${instruction}`,
            },
          ],
          system: systemPrompt,
        }),
      });

      if (!response.ok) return [];

      const data = (await response.json()) as {
        content: Array<{ type: string; text?: string }>;
      };

      const text = data.content.find((c) => c.type === "text")?.text;
      if (!text) return [];

      const jsonMatch = text.match(/\[[\s\S]*\]/);
      if (!jsonMatch) return [];

      const suggestions = JSON.parse(jsonMatch[0]) as Array<{
        type: string;
        description: string;
        clipIds: string[];
        params: Record<string, unknown>;
        confidence: number;
      }>;

      return suggestions.map((s) => ({
        id: crypto.randomUUID(),
        type: s.type as EditSuggestion["type"],
        description: s.description,
        clipIds: s.clipIds,
        params: s.params,
        confidence: s.confidence,
      }));
    } catch {
      return [];
    }
  }
}

export const claudeProvider = new ClaudeProvider();
