# garmin-connect-mcp

Local MCP server exposing Garmin Connect workout data to AI assistants.

## Setup

**1. Clone and install**

```bash
cd garmin-connect-mcp
uv sync
```

**2. Configure credentials**

```bash
cp .env.example .env
```

Edit `.env`:

```
GARMIN_EMAIL=your@email.com
GARMIN_PASSWORD=yourpassword
```

## Available Tools

| Tool | Description |
|------|-------------|
| `get_last_activity` | Most recent activity with full details |
| `get_activities` | Activities in a date range, optional type filter |
| `get_activity_details` | Full detail for a specific activity ID |

## Client Configuration

### Claude Desktop

Edit `~/Library/Application Support/Claude/claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "garmin": {
      "command": "uv",
      "args": [
        "run",
        "--directory",
        "/path/to/garmin-connect-mcp",
        "garmin-mcp"
      ]
    }
  }
}
```

Restart Claude Desktop after saving.

### Claude Code

```bash
claude mcp add garmin -- uv run --directory /path/to/garmin-connect-mcp garmin-mcp
```

Or add to `.claude/mcp.json` in any project directory:

```json
{
  "mcpServers": {
    "garmin": {
      "command": "uv",
      "args": [
        "run",
        "--directory",
        "/path/to/garmin-connect-mcp",
        "garmin-mcp"
      ]
    }
  }
}
```

### OpenAI Codex CLI

Add to `~/.codex/config.toml`:

```toml
[[mcp_servers]]
name = "garmin"
command = "uv"
args = [
  "run",
  "--directory",
  "/path/to/garmin-connect-mcp",
  "garmin-mcp"
]
```

## Cache

Activities are cached in `~/.garmin_mcp_cache.db`.

- **Activity details** — cached permanently (historical data doesn't change)
- **Activity lists** — cached for 1 hour, then re-fetched

## Example Usage

Ask Claude:

- "Show me my last workout"
- "How has my running pace changed over the last 30 days?"
- "Compare my heart rate zones from this week's runs"
- "What was my longest ride in March?"
