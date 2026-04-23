# garmin-connect-mcp

Local MCP server exposing Garmin Connect workout data to AI assistants.

## Prerequisite: Install `uv`

This MCP is installed with `uv sync` and launched with `uv run`, so you need `uv` installed locally before continuing.

### macOS

Install with Homebrew:

```bash
brew install uv
```

Or use the official installer:

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

## Setup

**1. Clone and install**

```bash
cd garmin-connect-mcp
uv sync
```

**2. Authenticate**

Run the interactive setup command:

```bash
uv run garmin-mcp-setup
```

This prompts for your Garmin email and password, logs in, and saves OAuth tokens to `~/.garminconnect`. You only need to do this once — the server loads the saved tokens automatically on startup.

If your account has MFA enabled, you will be prompted for the code during setup.

**Alternative: environment variables**

If you prefer not to use the token store, set credentials in `.env` instead:

```bash
cp .env.example .env
```

Edit `.env`:

```
GARMIN_EMAIL=your@email.com
GARMIN_PASSWORD=yourpassword
```

The server tries saved tokens first; `.env` credentials are used as a fallback.

## Available Tools

### Activity Tools

| Tool | Parameters | Description |
|------|-----------|-------------|
| `get_last_activity` | — | Most recent activity with full details including laps and HR zones |
| `get_activities` | `start_date`, `end_date?`, `activity_type?` | Activities in a date range, optional type filter (e.g. `running`, `cycling`) |
| `get_activity_details` | `activity_id` | Full detail for a specific activity ID |

### Wellness Tools

| Tool | Parameters | Description |
|------|-----------|-------------|
| `get_daily_wellness` | `for_date?` (YYYY-MM-DD, default today) | Daily snapshot: steps, calories, sleep stages/score, body battery, HRV, resting HR |
| `get_training_status` | `for_date?` (YYYY-MM-DD, default today) | Training readiness score + training load/status |

### Performance Tools

| Tool | Parameters | Description |
|------|-----------|-------------|
| `get_race_predictions` | — | Predicted race times for 5K, 10K, half marathon, marathon |
| `get_personal_records` | — | Personal records across all activity types |

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
[mcp_servers.garmin]
command = "uv"
args = [
  "run",
  "--directory",
  "/path/to/garmin-connect-mcp",
  "garmin-mcp"
]
```

## Cache

All data is cached in `~/.garmin_mcp_cache.db`.

| Data type | TTL | Reason |
|-----------|-----|--------|
| Activity details | permanent | Historical data never changes |
| Activity lists | 1 hour | Newly completed activities appear |
| Daily wellness / training status | 1 hour | Syncs throughout the day |
| Race predictions / personal records | 4 hours | Changes slowly with fitness |

## Example Usage

**Activities:**
- "Show me my last workout"
- "How has my running pace changed over the last 30 days?"
- "Compare my heart rate zones from this week's runs"
- "What was my longest ride in March?"

**Wellness & recovery:**
- "How did I sleep last night?"
- "What's my body battery and HRV looking like today?"
- "Am I recovered enough to train hard today?"

**Performance:**
- "What are my predicted race times right now?"
- "What's my 5K PR and when did I set it?"
