# @vibeframe/mcp-server

MCP (Model Context Protocol) server for [VibeFrame](https://github.com/vericontext/vibeframe) - AI-native video editing.

Edit video timelines with natural language through Claude Desktop, Cursor, or any MCP client.

## Quick Setup

### Claude Desktop

Add to `~/Library/Application Support/Claude/claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "vibeframe": {
      "command": "npx",
      "args": ["-y", "@vibeframe/mcp-server"]
    }
  }
}
```

### Cursor

Add to `.cursor/mcp.json`:

```json
{
  "mcpServers": {
    "vibeframe": {
      "command": "npx",
      "args": ["-y", "@vibeframe/mcp-server"]
    }
  }
}
```

## What You Can Do

Once connected, ask your AI assistant:

> "Create a new video project called Demo"

> "Add intro.mp4 to the project"

> "Trim the clip to 5 seconds and add a fade in"

> "Split the clip at 3 seconds"

## Available Tools (13)

| Tool | Description |
|------|-------------|
| `project_create` | Create a new `.vibe.json` project |
| `project_info` | Get project metadata |
| `timeline_add_source` | Import media (video/audio/image) |
| `timeline_add_clip` | Add clip to timeline |
| `timeline_split_clip` | Split clip at time |
| `timeline_trim_clip` | Trim clip start/end |
| `timeline_move_clip` | Move clip to new position |
| `timeline_delete_clip` | Remove clip |
| `timeline_duplicate_clip` | Duplicate clip |
| `timeline_add_effect` | Apply effect (fade, blur, etc.) |
| `timeline_add_track` | Add video/audio track |
| `timeline_list` | List all project contents |

## Resources

| URI | Description |
|-----|-------------|
| `vibe://project/current` | Full project state |
| `vibe://project/clips` | All clips |
| `vibe://project/sources` | Media sources |
| `vibe://project/tracks` | Track list |
| `vibe://project/settings` | Project settings |

## Environment Variables

| Variable | Description |
|----------|-------------|
| `VIBE_PROJECT_PATH` | Default project file path for resource access |

## Requirements

- Node.js 18+

## License

MIT
