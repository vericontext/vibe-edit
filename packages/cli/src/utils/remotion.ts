/**
 * Remotion rendering and compositing utilities.
 *
 * Uses `npx remotion` on-demand — Remotion is NOT a package dependency.
 * Scaffolds a temporary project, renders transparent WebM, and composites with FFmpeg.
 */

import { exec } from "node:child_process";
import { promisify } from "node:util";
import { writeFile, mkdir, rm } from "node:fs/promises";
import { existsSync } from "node:fs";
import { join } from "node:path";
import { tmpdir } from "node:os";

const execAsync = promisify(exec);

// ── Types ──────────────────────────────────────────────────────────────────

export interface RenderMotionOptions {
  /** Generated TSX component code */
  componentCode: string;
  /** Export name of the component */
  componentName: string;
  width: number;
  height: number;
  fps: number;
  durationInFrames: number;
  /** Output path for rendered video (.webm or .mp4) */
  outputPath: string;
  /** Render with transparent background (default: true) */
  transparent?: boolean;
}

export interface CompositeOptions {
  /** Base video to overlay on */
  baseVideo: string;
  /** Rendered overlay (transparent WebM) */
  overlayPath: string;
  /** Final composited output */
  outputPath: string;
}

export interface RenderResult {
  success: boolean;
  outputPath?: string;
  error?: string;
}

// ── Helpers ────────────────────────────────────────────────────────────────

/**
 * Check that `npx remotion` is available. Returns an error message if not.
 */
export async function ensureRemotionInstalled(): Promise<string | null> {
  try {
    await execAsync("npx remotion --help", { timeout: 30_000 });
    return null;
  } catch {
    return [
      "Remotion CLI not found. Install it with:",
      "  npm install -g @remotion/cli",
      "Or ensure npx is available and can download @remotion/cli on demand.",
    ].join("\n");
  }
}

/**
 * Create a minimal Remotion project in a temp directory.
 * Returns the directory path.
 */
export async function scaffoldRemotionProject(
  componentCode: string,
  componentName: string,
  opts: { width: number; height: number; fps: number; durationInFrames: number },
): Promise<string> {
  const dir = join(tmpdir(), `vibe_motion_${Date.now()}`);
  await mkdir(dir, { recursive: true });

  // package.json — remotion + react deps
  const packageJson = {
    name: "vibe-motion-render",
    version: "1.0.0",
    private: true,
    dependencies: {
      remotion: "^4.0.0",
      "@remotion/cli": "^4.0.0",
      react: "^18.0.0",
      "react-dom": "^18.0.0",
      "@types/react": "^18.0.0",
    },
  };
  await writeFile(join(dir, "package.json"), JSON.stringify(packageJson, null, 2));

  // tsconfig.json — minimal config for TSX
  const tsconfig = {
    compilerOptions: {
      target: "ES2020",
      module: "ESNext",
      moduleResolution: "bundler",
      jsx: "react-jsx",
      strict: false,
      esModuleInterop: true,
      skipLibCheck: true,
    },
  };
  await writeFile(join(dir, "tsconfig.json"), JSON.stringify(tsconfig, null, 2));

  // Component.tsx — the AI-generated component
  await writeFile(join(dir, "Component.tsx"), componentCode);

  // Root.tsx — Remotion entry point
  const rootCode = `import { registerRoot, Composition } from "remotion";
import { ${componentName} } from "./Component";

const Root = () => {
  return (
    <Composition
      id="${componentName}"
      component={${componentName}}
      durationInFrames={${opts.durationInFrames}}
      fps={${opts.fps}}
      width={${opts.width}}
      height={${opts.height}}
    />
  );
};

registerRoot(Root);
`;
  await writeFile(join(dir, "Root.tsx"), rootCode);

  // Install deps (first render will be slow, subsequent cached)
  if (!existsSync(join(dir, "node_modules"))) {
    await execAsync("npm install --prefer-offline --no-audit --no-fund", {
      cwd: dir,
      timeout: 120_000,
    });
  }

  return dir;
}

/**
 * Render a Remotion composition to video.
 * When transparent: tries VP8, then VP9 (both support alpha). Fails if neither works.
 * When opaque: renders H264 MP4.
 */
export async function renderMotion(options: RenderMotionOptions): Promise<RenderResult> {
  const transparent = options.transparent !== false;

  // 1. Scaffold project
  const dir = await scaffoldRemotionProject(
    options.componentCode,
    options.componentName,
    {
      width: options.width,
      height: options.height,
      fps: options.fps,
      durationInFrames: options.durationInFrames,
    },
  );

  try {
    const entryPoint = join(dir, "Root.tsx");

    if (transparent) {
      const webmOut = options.outputPath.replace(/\.\w+$/, ".webm");

      // Try VP8 with alpha (best Remotion support)
      try {
        const cmd = [
          "npx remotion render",
          `"${entryPoint}"`,
          options.componentName,
          `"${webmOut}"`,
          "--codec vp8",
          "--image-format png",
          "--pixel-format yuva420p",
        ].join(" ");

        await execAsync(cmd, { cwd: dir, timeout: 300_000 });
        return { success: true, outputPath: webmOut };
      } catch {
        // VP8 failed, try VP9
      }

      // Try VP9 with alpha as fallback
      try {
        const cmd = [
          "npx remotion render",
          `"${entryPoint}"`,
          options.componentName,
          `"${webmOut}"`,
          "--codec vp9",
          "--image-format png",
          "--pixel-format yuva420p",
        ].join(" ");

        await execAsync(cmd, { cwd: dir, timeout: 300_000 });
        return { success: true, outputPath: webmOut };
      } catch (error) {
        const msg = error instanceof Error ? error.message : String(error);
        return { success: false, error: `Transparent render failed (VP8 & VP9): ${msg}` };
      }
    }

    // Non-transparent: H264 MP4
    const mp4Out = options.outputPath.replace(/\.\w+$/, ".mp4");
    const cmd = [
      "npx remotion render",
      `"${entryPoint}"`,
      options.componentName,
      `"${mp4Out}"`,
      "--codec h264",
      "--crf 18",
    ].join(" ");

    await execAsync(cmd, { cwd: dir, timeout: 300_000 });
    return { success: true, outputPath: mp4Out };
  } catch (error) {
    const msg = error instanceof Error ? error.message : String(error);
    return { success: false, error: `Remotion render failed: ${msg}` };
  } finally {
    // Cleanup temp project
    await rm(dir, { recursive: true, force: true }).catch(() => {});
  }
}

/**
 * Composite a transparent overlay on top of a base video using FFmpeg.
 */
export async function compositeOverlay(options: CompositeOptions): Promise<RenderResult> {
  try {
    const cmd = [
      "ffmpeg -y",
      `-i "${options.baseVideo}"`,
      `-i "${options.overlayPath}"`,
      '-filter_complex "[0:v][1:v]overlay=0:0:shortest=1[out]"',
      '-map "[out]"',
      "-map 0:a?",
      "-c:a copy",
      "-c:v libx264 -crf 18",
      `"${options.outputPath}"`,
    ].join(" ");

    await execAsync(cmd, { timeout: 300_000 });
    return { success: true, outputPath: options.outputPath };
  } catch (error) {
    const msg = error instanceof Error ? error.message : String(error);
    return { success: false, error: `FFmpeg composite failed: ${msg}` };
  }
}

// ── Caption Component Generator ───────────────────────────────────────────

export interface CaptionSegment {
  start: number;
  end: number;
  text: string;
}

export type CaptionStylePreset = "bold" | "minimal" | "outline" | "karaoke";

export interface GenerateCaptionComponentOptions {
  segments: CaptionSegment[];
  style: CaptionStylePreset;
  fontSize: number;
  fontColor: string;
  position: "top" | "center" | "bottom";
  width: number;
  height: number;
  /** When set, embed the video inside the component (no transparency needed) */
  videoFileName?: string;
}

/**
 * Generate a Remotion TSX component that renders styled captions.
 * No LLM call — purely programmatic from SRT segments + style config.
 */
export function generateCaptionComponent(options: GenerateCaptionComponentOptions): {
  code: string;
  name: string;
} {
  const { segments, style, fontSize, fontColor, position, width, height, videoFileName } = options;
  const name = videoFileName ? "VideoCaptioned" : "CaptionOverlay";

  // Serialize segments as a JSON array embedded in the TSX
  const segmentsJSON = JSON.stringify(
    segments.map((s) => ({ start: s.start, end: s.end, text: s.text })),
  );

  // Build CSS styles per preset
  const styleMap: Record<CaptionStylePreset, string> = {
    bold: `
      fontWeight: "bold" as const,
      color: "${fontColor === "yellow" ? "#FFFF00" : "#FFFFFF"}",
      textShadow: "3px 3px 6px rgba(0,0,0,0.9), -1px -1px 3px rgba(0,0,0,0.7)",
      WebkitTextStroke: "1px rgba(0,0,0,0.5)",
    `,
    minimal: `
      fontWeight: "normal" as const,
      color: "#FFFFFF",
      textShadow: "1px 1px 3px rgba(0,0,0,0.5)",
    `,
    outline: `
      fontWeight: "bold" as const,
      color: "#FFFFFF",
      WebkitTextStroke: "2px #FF0000",
      textShadow: "none",
    `,
    karaoke: `
      fontWeight: "bold" as const,
      color: "#00FFFF",
      textShadow: "2px 2px 4px rgba(0,0,0,0.8), -1px -1px 2px rgba(0,0,0,0.6)",
    `,
  };

  const justifyContent =
    position === "top" ? "flex-start" : position === "center" ? "center" : "flex-end";
  const paddingDir = position === "top" ? "paddingTop" : position === "bottom" ? "paddingBottom" : "";
  const paddingVal = position === "center" ? "" : `${paddingDir}: 40,`;

  // Video import line (only when embedding video)
  const videoImport = videoFileName
    ? `, Video, staticFile`
    : "";

  // Video background element
  const videoElement = videoFileName
    ? `<Video src={staticFile("${videoFileName}")} style={{ width: "100%", height: "100%" }} />`
    : "";

  const code = `import { AbsoluteFill, useCurrentFrame, useVideoConfig${videoImport} } from "remotion";

interface Segment {
  start: number;
  end: number;
  text: string;
}

const segments: Segment[] = ${segmentsJSON};

export const ${name} = () => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const currentTime = frame / fps;

  const activeSegment = segments.find(
    (s) => currentTime >= s.start && currentTime < s.end
  );

  return (
    <AbsoluteFill>
      ${videoElement}
      {activeSegment && (
        <AbsoluteFill
          style={{
            display: "flex",
            justifyContent: "${justifyContent}",
            alignItems: "center",
            ${paddingVal}
          }}
        >
          <div
            style={{
              fontSize: ${fontSize},
              fontFamily: "Arial, Helvetica, sans-serif",
              textAlign: "center" as const,
              maxWidth: "${Math.round(width * 0.9)}px",
              lineHeight: 1.3,
              padding: "8px 16px",
              ${styleMap[style]}
            }}
          >
            {activeSegment.text}
          </div>
        </AbsoluteFill>
      )}
    </AbsoluteFill>
  );
};
`;

  return { code, name };
}

/**
 * Full pipeline: render motion graphic → composite onto base video.
 * If no base video, just renders the motion graphic.
 */
export async function renderAndComposite(
  motionOpts: RenderMotionOptions,
  baseVideo?: string,
  finalOutput?: string,
): Promise<RenderResult> {
  // Step 1: Render motion graphic (transparent if compositing)
  const renderOpts = {
    ...motionOpts,
    transparent: !!baseVideo,
    outputPath: baseVideo
      ? motionOpts.outputPath.replace(/\.\w+$/, "_overlay.webm")
      : motionOpts.outputPath,
  };

  const renderResult = await renderMotion(renderOpts);
  if (!renderResult.success || !renderResult.outputPath) {
    return renderResult;
  }

  // Step 2: If no base video, we're done
  if (!baseVideo) {
    return renderResult;
  }

  // Step 3: Composite overlay onto base video
  const output = finalOutput || motionOpts.outputPath;
  const compositeResult = await compositeOverlay({
    baseVideo,
    overlayPath: renderResult.outputPath,
    outputPath: output,
  });

  // Cleanup overlay file
  await rm(renderResult.outputPath, { force: true }).catch(() => {});

  return compositeResult;
}

/**
 * Render a Remotion caption component that embeds the video directly.
 * No transparency needed — the component includes <Video> + caption text.
 * After rendering, copies audio from the original video to the output.
 */
export async function renderCaptionedVideo(options: {
  componentCode: string;
  componentName: string;
  width: number;
  height: number;
  fps: number;
  durationInFrames: number;
  videoPath: string;
  videoFileName: string;
  outputPath: string;
}): Promise<RenderResult> {
  const dir = await scaffoldRemotionProject(
    options.componentCode,
    options.componentName,
    {
      width: options.width,
      height: options.height,
      fps: options.fps,
      durationInFrames: options.durationInFrames,
    },
  );

  try {
    // Copy video to public/ so Remotion's staticFile() can access it
    const publicDir = join(dir, "public");
    await mkdir(publicDir, { recursive: true });
    const { copyFile } = await import("node:fs/promises");
    await copyFile(options.videoPath, join(publicDir, options.videoFileName));

    const entryPoint = join(dir, "Root.tsx");
    const mp4Out = options.outputPath.replace(/\.\w+$/, "_video_only.mp4");

    // Render H264 (video-only from Remotion, no audio)
    const renderCmd = [
      "npx remotion render",
      `"${entryPoint}"`,
      options.componentName,
      `"${mp4Out}"`,
      "--codec h264",
      "--crf 18",
    ].join(" ");

    await execAsync(renderCmd, { cwd: dir, timeout: 600_000, maxBuffer: 50 * 1024 * 1024 });

    // Mux: take video from Remotion render, audio from original video
    const muxCmd = [
      "ffmpeg -y",
      `-i "${mp4Out}"`,
      `-i "${options.videoPath}"`,
      "-map 0:v:0",
      "-map 1:a:0?",
      "-c:v copy",
      "-c:a copy",
      "-shortest",
      `"${options.outputPath}"`,
    ].join(" ");

    await execAsync(muxCmd, { timeout: 120_000 });

    // Cleanup temp video-only file
    await rm(mp4Out, { force: true }).catch(() => {});

    return { success: true, outputPath: options.outputPath };
  } catch (error) {
    const msg = error instanceof Error ? error.message : String(error);
    return { success: false, error: `Remotion caption render failed: ${msg}` };
  } finally {
    await rm(dir, { recursive: true, force: true }).catch(() => {});
  }
}
