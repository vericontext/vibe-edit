import { Command } from "commander";
import { readFile, writeFile } from "node:fs/promises";
import { resolve } from "node:path";
import chalk from "chalk";
import ora from "ora";
import {
  providerRegistry,
  WhisperProvider,
  GeminiProvider,
  whisperProvider,
  geminiProvider,
  runwayProvider,
  klingProvider,
} from "@vibe-edit/ai-providers";
import { Project, type ProjectFile } from "../engine/index.js";

export const aiCommand = new Command("ai")
  .description("AI provider commands");

aiCommand
  .command("transcribe")
  .description("Transcribe audio using Whisper")
  .argument("<audio>", "Audio file path")
  .option("-k, --api-key <key>", "OpenAI API key (or set OPENAI_API_KEY env)")
  .option("-l, --language <lang>", "Language code (e.g., en, ko)")
  .option("-o, --output <path>", "Output JSON file path")
  .action(async (audioPath: string, options) => {
    const spinner = ora("Initializing Whisper...").start();

    try {
      const apiKey = options.apiKey || process.env.OPENAI_API_KEY;
      if (!apiKey) {
        spinner.fail(chalk.red("OpenAI API key required. Use --api-key or set OPENAI_API_KEY"));
        process.exit(1);
      }

      const whisper = new WhisperProvider();
      await whisper.initialize({ apiKey });

      spinner.text = "Reading audio file...";
      const absPath = resolve(process.cwd(), audioPath);
      const audioBuffer = await readFile(absPath);
      const audioBlob = new Blob([audioBuffer]);

      spinner.text = "Transcribing...";
      const result = await whisper.transcribe(audioBlob, options.language);

      if (result.status === "failed") {
        spinner.fail(chalk.red(`Transcription failed: ${result.error}`));
        process.exit(1);
      }

      spinner.succeed(chalk.green("Transcription complete"));

      console.log();
      console.log(chalk.bold.cyan("Transcript"));
      console.log(chalk.dim("─".repeat(60)));
      console.log(result.fullText);
      console.log();

      if (result.segments && result.segments.length > 0) {
        console.log(chalk.bold.cyan("Segments"));
        console.log(chalk.dim("─".repeat(60)));
        for (const seg of result.segments) {
          const time = `[${formatTime(seg.startTime)} - ${formatTime(seg.endTime)}]`;
          console.log(`${chalk.dim(time)} ${seg.text}`);
        }
        console.log();
      }

      if (options.output) {
        const outputPath = resolve(process.cwd(), options.output);
        await writeFile(outputPath, JSON.stringify(result, null, 2), "utf-8");
        console.log(chalk.green(`Saved to: ${outputPath}`));
      }
    } catch (error) {
      spinner.fail(chalk.red("Transcription failed"));
      console.error(error);
      process.exit(1);
    }
  });

aiCommand
  .command("suggest")
  .description("Get AI edit suggestions using Gemini")
  .argument("<project>", "Project file path")
  .argument("<instruction>", "Natural language instruction")
  .option("-k, --api-key <key>", "Google API key (or set GOOGLE_API_KEY env)")
  .option("--apply", "Apply the first suggestion automatically")
  .action(async (projectPath: string, instruction: string, options) => {
    const spinner = ora("Initializing Gemini...").start();

    try {
      const apiKey = options.apiKey || process.env.GOOGLE_API_KEY;
      if (!apiKey) {
        spinner.fail(chalk.red("Google API key required. Use --api-key or set GOOGLE_API_KEY"));
        process.exit(1);
      }

      const filePath = resolve(process.cwd(), projectPath);
      const content = await readFile(filePath, "utf-8");
      const data: ProjectFile = JSON.parse(content);
      const project = Project.fromJSON(data);

      const gemini = new GeminiProvider();
      await gemini.initialize({ apiKey });

      spinner.text = "Analyzing...";
      const clips = project.getClips();
      const suggestions = await gemini.autoEdit(clips, instruction);

      spinner.succeed(chalk.green(`Found ${suggestions.length} suggestion(s)`));

      console.log();
      console.log(chalk.bold.cyan("Edit Suggestions"));
      console.log(chalk.dim("─".repeat(60)));

      for (let i = 0; i < suggestions.length; i++) {
        const sug = suggestions[i];
        console.log();
        console.log(chalk.yellow(`[${i + 1}] ${sug.type.toUpperCase()}`));
        console.log(`    ${sug.description}`);
        console.log(chalk.dim(`    Confidence: ${(sug.confidence * 100).toFixed(0)}%`));
        console.log(chalk.dim(`    Clips: ${sug.clipIds.join(", ")}`));
        console.log(chalk.dim(`    Params: ${JSON.stringify(sug.params)}`));
      }

      if (options.apply && suggestions.length > 0) {
        console.log();
        spinner.start("Applying first suggestion...");

        const sug = suggestions[0];
        const applied = applySuggestion(project, sug);

        if (applied) {
          await writeFile(filePath, JSON.stringify(project.toJSON(), null, 2), "utf-8");
          spinner.succeed(chalk.green("Suggestion applied"));
        } else {
          spinner.warn(chalk.yellow("Could not apply suggestion automatically"));
        }
      }

      console.log();
    } catch (error) {
      spinner.fail(chalk.red("AI suggestion failed"));
      console.error(error);
      process.exit(1);
    }
  });

aiCommand
  .command("providers")
  .description("List available AI providers")
  .action(async () => {
    // Register default providers
    providerRegistry.register(whisperProvider);
    providerRegistry.register(geminiProvider);
    providerRegistry.register(runwayProvider);
    providerRegistry.register(klingProvider);

    console.log();
    console.log(chalk.bold.cyan("Available AI Providers"));
    console.log(chalk.dim("─".repeat(60)));

    const providers = providerRegistry.getAll();
    for (const provider of providers) {
      const status = provider.isAvailable ? chalk.green("●") : chalk.red("○");
      console.log();
      console.log(`${status} ${chalk.bold(provider.name)} ${chalk.dim(`(${provider.id})`)}`);
      console.log(`  ${provider.description}`);
      console.log(`  ${chalk.dim("Capabilities:")} ${provider.capabilities.join(", ")}`);
    }

    console.log();
  });

function formatTime(seconds: number): string {
  const mins = Math.floor(seconds / 60);
  const secs = (seconds % 60).toFixed(1);
  return `${mins}:${secs.padStart(4, "0")}`;
}

function applySuggestion(project: Project, suggestion: any): boolean {
  const { type, clipIds, params } = suggestion;

  if (clipIds.length === 0) return false;
  const clipId = clipIds[0];

  switch (type) {
    case "trim":
      if (params.newDuration) {
        return project.trimClipEnd(clipId, params.newDuration);
      }
      break;
    case "add-effect":
      if (params.effectType) {
        const effect = project.addEffect(clipId, {
          type: params.effectType,
          startTime: params.startTime || 0,
          duration: params.duration || 1,
          params: params.effectParams || {},
        });
        return effect !== null;
      }
      break;
    case "delete":
      return project.removeClip(clipId);
  }

  return false;
}
