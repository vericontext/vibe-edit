/**
 * REPL Command Executor
 * Handles both built-in commands and natural language AI commands
 */

import { extname } from "node:path";
import { exec } from "node:child_process";
import { promisify } from "node:util";
import chalk from "chalk";
import ora from "ora";

const execAsync = promisify(exec);
import { Session } from "./session.js";
import { success, error, warn, info, getHelpText, formatProjectInfo } from "./prompts.js";
import { getApiKeyFromConfig, loadConfig, type LLMProvider } from "../config/index.js";
import { executeCommand } from "../commands/ai.js";
import { Project } from "../engine/index.js";
import {
  OpenAIProvider,
  ClaudeProvider,
  OllamaProvider,
} from "@vibeframe/ai-providers";

/** Built-in command result */
export interface CommandResult {
  success: boolean;
  message: string;
  shouldExit?: boolean;
  showHelp?: boolean;
  showSetup?: boolean;
}

/**
 * Try to execute AI generation commands (image, tts, sfx)
 * These don't require a project
 */
async function tryExecuteAICommand(
  input: string,
  lowerInput: string
): Promise<CommandResult | null> {
  // Image generation patterns
  const imageMatch = lowerInput.match(
    /(?:generate|create|make|draw)\s+(?:an?\s+)?(?:image|picture|photo|illustration)\s+(?:of\s+)?(.+?)(?:\s+(?:and\s+)?(?:save|output|export)\s+(?:as|to|it\s+as)\s+(\S+))?$/i
  );
  if (imageMatch) {
    const prompt = imageMatch[1].trim();
    const outputFile = imageMatch[2] || `${prompt.split(/\s+/).slice(0, 3).join("-").toLowerCase()}.png`;
    return await runVibeCommand("ai image", `"${prompt}" -o "${outputFile}"`);
  }

  // TTS / audio generation patterns
  const ttsMatch = lowerInput.match(
    /(?:generate|create|make)\s+(?:an?\s+)?(?:audio|voice|speech|tts|narration|voiceover)\s+(?:message\s+)?(?:saying\s+|of\s+|for\s+)?["']?(.+?)["']?(?:\s+(?:and\s+)?(?:save|output|export)\s+(?:as|to|it\s+as)\s+(\S+))?$/i
  );
  if (ttsMatch) {
    const text = ttsMatch[1].trim();
    const outputFile = ttsMatch[2] || "output.mp3";
    return await runVibeCommand("ai tts", `"${text}" -o "${outputFile}"`);
  }

  // Sound effect patterns
  const sfxMatch = lowerInput.match(
    /(?:generate|create|make)\s+(?:an?\s+)?(?:sound\s*effect|sfx|sound)\s+(?:of\s+)?(.+?)(?:\s+(?:and\s+)?(?:save|output|export)\s+(?:as|to|it\s+as)\s+(\S+))?$/i
  );
  if (sfxMatch) {
    const prompt = sfxMatch[1].trim();
    const outputFile = sfxMatch[2] || "sound-effect.mp3";
    return await runVibeCommand("ai sfx", `"${prompt}" -o "${outputFile}"`);
  }

  // Direct "image of X" pattern
  const simpleImageMatch = lowerInput.match(
    /^(?:an?\s+)?(?:image|picture|photo)\s+(?:of\s+)?(.+)$/i
  );
  if (simpleImageMatch) {
    const prompt = simpleImageMatch[1].trim();
    const outputFile = `${prompt.split(/\s+/).slice(0, 3).join("-").toLowerCase()}.png`;
    return await runVibeCommand("ai image", `"${prompt}" -o "${outputFile}"`);
  }

  return null;
}

/**
 * Run a vibe CLI command and return the result
 */
async function runVibeCommand(
  command: string,
  args: string
): Promise<CommandResult> {
  const spinner = ora({ text: `Running: vibe ${command}...`, spinner: "dots" }).start();

  try {
    const { stdout, stderr } = await execAsync(`vibe ${command} ${args}`, {
      timeout: 120000, // 2 minute timeout
    });

    spinner.succeed();

    const output = stdout || stderr;
    return {
      success: true,
      message: success(output.trim() || `Completed: vibe ${command}`),
    };
  } catch (e: unknown) {
    spinner.fail();
    const errorMessage = e instanceof Error ? e.message : String(e);
    return {
      success: false,
      message: error(`Command failed: ${errorMessage}`),
    };
  }
}

/** Parse a built-in command into parts */
function parseBuiltinCommand(input: string): { cmd: string; args: string[] } {
  const trimmed = input.trim();
  const parts = trimmed.split(/\s+/);
  const cmd = parts[0].toLowerCase();
  const args = parts.slice(1);
  return { cmd, args };
}

/** Check if input looks like a built-in command */
function isBuiltinCommand(input: string): boolean {
  const builtins = [
    "new", "open", "save", "info", "list", "add", "export",
    "undo", "setup", "help", "exit", "quit", "q", "clear"
  ];
  const { cmd } = parseBuiltinCommand(input);
  return builtins.includes(cmd);
}

/**
 * Execute a command in the REPL
 */
export async function executeReplCommand(
  input: string,
  session: Session
): Promise<CommandResult> {
  const trimmed = input.trim();

  if (!trimmed) {
    return { success: true, message: "" };
  }

  // Handle built-in commands
  if (isBuiltinCommand(trimmed)) {
    return executeBuiltinCommand(trimmed, session);
  }

  // Handle natural language commands
  return executeNaturalLanguageCommand(trimmed, session);
}

/**
 * Execute a built-in command
 */
async function executeBuiltinCommand(
  input: string,
  session: Session
): Promise<CommandResult> {
  const { cmd, args } = parseBuiltinCommand(input);

  switch (cmd) {
    case "exit":
    case "quit":
    case "q":
      return { success: true, message: "Goodbye!", shouldExit: true };

    case "help":
      return { success: true, message: getHelpText() };

    case "setup":
      return { success: true, message: "", showSetup: true };

    case "clear":
      console.clear();
      return { success: true, message: "" };

    case "new": {
      const name = args.join(" ") || "Untitled Project";
      session.createProject(name);
      return { success: true, message: success(`Created project: ${name}`) };
    }

    case "open": {
      if (args.length === 0) {
        return { success: false, message: error("Usage: open <project-file>") };
      }
      const filePath = args.join(" ");
      try {
        await session.loadProject(filePath);
        const summary = session.getProjectSummary();
        return {
          success: true,
          message: success(`Opened: ${summary?.name || filePath}`),
        };
      } catch (e) {
        return { success: false, message: error(`Failed to open: ${e}`) };
      }
    }

    case "save": {
      if (!session.hasProject()) {
        return { success: false, message: error("No project to save. Use 'new' first.") };
      }
      try {
        const filePath = args.length > 0 ? args.join(" ") : undefined;
        const savedPath = await session.saveProject(filePath);
        return { success: true, message: success(`Saved to: ${savedPath}`) };
      } catch (e) {
        return { success: false, message: error(`Failed to save: ${e}`) };
      }
    }

    case "info": {
      const summary = session.getProjectSummary();
      if (!summary) {
        return { success: false, message: error("No project loaded. Use 'new' or 'open' first.") };
      }
      return { success: true, message: formatProjectInfo(summary) };
    }

    case "list": {
      if (!session.hasProject()) {
        return { success: false, message: error("No project loaded. Use 'new' or 'open' first.") };
      }
      const project = session.getProject();
      return { success: true, message: formatTimeline(project) };
    }

    case "add": {
      if (args.length === 0) {
        return { success: false, message: error("Usage: add <media-file>") };
      }
      if (!session.hasProject()) {
        return { success: false, message: error("No project loaded. Use 'new' first.") };
      }

      const mediaPath = args.join(" ");
      const { exists, absPath } = session.checkMediaExists(mediaPath);

      if (!exists) {
        return { success: false, message: error(`File not found: ${mediaPath}`) };
      }

      session.pushHistory("add source");
      const project = session.getProject();

      // Determine media type from extension
      const ext = extname(absPath).toLowerCase();
      const audioExts = [".mp3", ".wav", ".aac", ".ogg", ".m4a", ".flac"];
      const imageExts = [".jpg", ".jpeg", ".png", ".gif", ".webp", ".bmp"];

      let mediaType: "video" | "audio" | "image" = "video";
      if (audioExts.includes(ext)) mediaType = "audio";
      else if (imageExts.includes(ext)) mediaType = "image";

      // Add source
      const source = project.addSource({
        name: absPath.split("/").pop() || "media",
        type: mediaType,
        url: absPath,
        duration: 10, // Placeholder - would need ffprobe for actual duration
        width: 1920,
        height: 1080,
      });

      // Also add a clip to the timeline
      const tracks = project.getTracksByType(mediaType === "audio" ? "audio" : "video");
      const trackId = tracks.length > 0 ? tracks[0].id : project.getTracks()[0]?.id;

      if (trackId) {
        const existingClips = project.getClipsByTrack(trackId);
        const startTime = existingClips.reduce(
          (max, c) => Math.max(max, c.startTime + c.duration),
          0
        );

        project.addClip({
          sourceId: source.id,
          trackId,
          startTime,
          duration: source.duration,
          sourceStartOffset: 0,
          sourceEndOffset: source.duration,
        });
      }

      return { success: true, message: success(`Added: ${source.name}`) };
    }

    case "export": {
      if (!session.hasProject()) {
        return { success: false, message: error("No project loaded.") };
      }

      // Get output path
      const outputPath = args.length > 0
        ? args.join(" ")
        : `${session.getProjectName()?.replace(/\s+/g, "-").toLowerCase() || "output"}.mp4`;

      return {
        success: true,
        message: info(`Export command: vibe export ${session.getProjectPath() || "<project>"} -o ${outputPath}`),
      };
    }

    case "undo": {
      const undone = session.undo();
      if (undone) {
        return { success: true, message: success(`Undone: ${undone}`) };
      }
      return { success: false, message: warn("Nothing to undo") };
    }

    default:
      return { success: false, message: error(`Unknown command: ${cmd}`) };
  }
}

/**
 * Execute a natural language command using AI
 */
async function executeNaturalLanguageCommand(
  input: string,
  session: Session
): Promise<CommandResult> {
  const lowerInput = input.toLowerCase();

  // Check for AI generation commands (these don't require a project)
  const aiCommandResult = await tryExecuteAICommand(input, lowerInput);
  if (aiCommandResult) {
    return aiCommandResult;
  }

  // Check if project exists
  if (!session.hasProject()) {
    // Special case: user might be trying to create a project with natural language
    const createMatch = input.match(/^(?:create|make|new|start)\s+(?:a\s+)?(?:new\s+)?(?:project\s+)?(?:called\s+|named\s+)?["']?([^"']+)["']?$/i);
    if (createMatch) {
      const name = createMatch[1].trim();
      session.createProject(name);
      return { success: true, message: success(`Created project: ${name}`) };
    }

    return {
      success: false,
      message: error("No project loaded. Use 'new <name>' to create one first."),
    };
  }

  // Get configured LLM provider for command parsing
  const config = await loadConfig();
  const llmProviderType: LLMProvider = config?.llm?.provider || "openai";

  // Map provider type to API key name
  const providerKeyMap: Record<LLMProvider, string> = {
    claude: "anthropic",
    openai: "openai",
    gemini: "google",
    ollama: "ollama",
  };

  const apiKeyName = providerKeyMap[llmProviderType];
  const apiKey = await getApiKeyFromConfig(apiKeyName);

  if (!apiKey && llmProviderType !== "ollama") {
    return {
      success: false,
      message: error(
        `${llmProviderType.charAt(0).toUpperCase() + llmProviderType.slice(1)} API key not configured.\n` +
        "   Run 'vibe setup' to configure your API key."
      ),
    };
  }

  // Create the appropriate LLM provider
  let llmProvider: OpenAIProvider | ClaudeProvider | OllamaProvider;

  if (llmProviderType === "claude") {
    llmProvider = new ClaudeProvider();
  } else if (llmProviderType === "ollama") {
    llmProvider = new OllamaProvider();
  } else {
    // Default to OpenAI for other providers (openai, gemini with OpenAI-compatible API, etc.)
    llmProvider = new OpenAIProvider();
  }

  await llmProvider.initialize({ apiKey: apiKey || "" });

  const spinner = ora({ text: "Processing...", spinner: "dots" }).start();

  try {
    const project = session.getProject();
    const clips = project.getClips();
    const tracks = project.getTracks().map((t) => t.id);

    // Parse command using LLM
    const result = await llmProvider.parseCommand(input, { clips, tracks });

    if (!result.success) {
      spinner.fail();
      return { success: false, message: error(result.error || "Failed to parse command") };
    }

    if (result.clarification) {
      spinner.warn();
      return { success: false, message: warn(result.clarification) };
    }

    if (result.commands.length === 0) {
      spinner.warn();
      return { success: false, message: warn("No commands generated") };
    }

    // Save state for undo
    session.pushHistory(input);

    // Execute commands
    let executed = 0;
    for (const cmd of result.commands) {
      const ok = executeCommand(project, cmd);
      if (ok) executed++;
    }

    // Auto-save if enabled
    const config = session.getConfig();
    if (config?.repl.autoSave && session.getProjectPath()) {
      await session.saveProject();
    }

    spinner.succeed();

    // Build result message
    const cmdDescriptions = result.commands
      .map((c) => `  ${chalk.dim("-")} ${c.description}`)
      .join("\n");

    return {
      success: true,
      message: success(`Executed ${executed}/${result.commands.length} command(s)\n${cmdDescriptions}`),
    };
  } catch (e) {
    spinner.fail();
    return { success: false, message: error(`AI command failed: ${e}`) };
  }
}

/**
 * Format timeline for display
 */
function formatTimeline(project: Project): string {
  const tracks = project.getTracks();
  const clips = project.getClips();
  const sources = project.getSources();

  const lines = [
    "",
    chalk.bold.cyan("Timeline"),
    chalk.dim("─".repeat(40)),
    "",
  ];

  // Sources
  lines.push(chalk.bold("Sources:"));
  if (sources.length === 0) {
    lines.push(chalk.dim("  (none)"));
  } else {
    for (const src of sources) {
      lines.push(`  ${chalk.yellow(src.id.slice(0, 8))} ${src.name} ${chalk.dim(`[${src.type}]`)}`);
    }
  }
  lines.push("");

  // Tracks with clips
  lines.push(chalk.bold("Tracks:"));
  for (const track of tracks) {
    const trackClips = clips.filter((c) => c.trackId === track.id);
    lines.push(`  ${chalk.cyan(track.name)} ${chalk.dim(`(${track.type})`)}`);

    if (trackClips.length === 0) {
      lines.push(chalk.dim("    (empty)"));
    } else {
      for (const clip of trackClips.sort((a, b) => a.startTime - b.startTime)) {
        const src = sources.find((s) => s.id === clip.sourceId);
        const srcName = src?.name || "unknown";
        lines.push(
          `    ${chalk.yellow(clip.id.slice(0, 8))} ` +
          `${chalk.dim("@")}${clip.startTime.toFixed(1)}s ` +
          `${chalk.dim("dur:")}${clip.duration.toFixed(1)}s ` +
          `${chalk.dim("src:")}${srcName}`
        );
      }
    }
  }

  lines.push("");
  return lines.join("\n");
}
