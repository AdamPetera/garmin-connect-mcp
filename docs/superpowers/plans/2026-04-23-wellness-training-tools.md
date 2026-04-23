# Wellness & Training Tools Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add four new MCP tools — daily wellness snapshot, training status, race predictions, and personal records — backed by new cache tables.

**Architecture:** New client methods in `garmin.py` bundle multiple Garmin API calls into single coherent responses. New cache tables (`daily_data` with 1-hour TTL, `static_data` with 4-hour TTL) mirror the existing pattern. Four new `@mcp.tool()` functions in `server.py` delegate to the client and cache.

**Tech Stack:** garminconnect, sqlite3, FastMCP, pytest, uv

---

### Task 1: Add `daily_data` and `static_data` cache tables

**Files:**
- Modify: `src/garmin_mcp/cache.py`
- Test: `tests/test_cache.py`

- [ ] **Step 1: Write the failing tests**

Append to `tests/test_cache.py`:

```python
def test_get_daily_data_returns_none_when_missing():
    assert cache.get_daily_data("wellness:2026-04-23") is None


def test_set_and_get_daily_data():
    data = {"steps": 10000, "sleep_score": 85}
    cache.set_daily_data("wellness:2026-04-23", data)
    assert cache.get_daily_data("wellness:2026-04-23") == data


def test_daily_data_expires_after_one_hour():
    cache.set_daily_data("wellness:2026-04-01", {"steps": 5000})
    two_hours_ago = (datetime.now(UTC) - timedelta(hours=2)).isoformat()
    with sqlite3.connect(cache._db_path) as conn:
        conn.execute(
            "UPDATE daily_data SET fetched_at = ? WHERE cache_key = ?",
            (two_hours_ago, "wellness:2026-04-01"),
        )
    assert cache.get_daily_data("wellness:2026-04-01") is None


def test_daily_data_still_valid_within_one_hour():
    cache.set_daily_data("wellness:2026-04-01", {"steps": 5000})
    thirty_min_ago = (datetime.now(UTC) - timedelta(minutes=30)).isoformat()
    with sqlite3.connect(cache._db_path) as conn:
        conn.execute(
            "UPDATE daily_data SET fetched_at = ? WHERE cache_key = ?",
            (thirty_min_ago, "wellness:2026-04-01"),
        )
    assert cache.get_daily_data("wellness:2026-04-01") is not None


def test_get_static_data_returns_none_when_missing():
    assert cache.get_static_data("race_predictions") is None


def test_set_and_get_static_data():
    data = {"5K": "25:00", "10K": "52:00"}
    cache.set_static_data("race_predictions", data)
    assert cache.get_static_data("race_predictions") == data


def test_static_data_expires_after_four_hours():
    cache.set_static_data("personal_records", [{"type": "running", "pr": 120}])
    five_hours_ago = (datetime.now(UTC) - timedelta(hours=5)).isoformat()
    with sqlite3.connect(cache._db_path) as conn:
        conn.execute(
            "UPDATE static_data SET fetched_at = ? WHERE cache_key = ?",
            (five_hours_ago, "personal_records"),
        )
    assert cache.get_static_data("personal_records") is None


def test_static_data_still_valid_within_four_hours():
    cache.set_static_data("personal_records", [{"type": "running", "pr": 120}])
    two_hours_ago = (datetime.now(UTC) - timedelta(hours=2)).isoformat()
    with sqlite3.connect(cache._db_path) as conn:
        conn.execute(
            "UPDATE static_data SET fetched_at = ? WHERE cache_key = ?",
            (two_hours_ago, "personal_records"),
        )
    assert cache.get_static_data("personal_records") is not None
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
uv run pytest tests/test_cache.py -k "daily_data or static_data" -v
```

Expected: FAIL — `get_daily_data` not defined.

- [ ] **Step 3: Add tables and functions to `cache.py`**

In `_connect()`, add two new `CREATE TABLE IF NOT EXISTS` statements after the existing `activity_list` one:

```python
    conn.execute("""
        CREATE TABLE IF NOT EXISTS daily_data (
            cache_key  TEXT PRIMARY KEY,
            data       TEXT NOT NULL,
            fetched_at TEXT NOT NULL
        )
    """)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS static_data (
            cache_key  TEXT PRIMARY KEY,
            data       TEXT NOT NULL,
            fetched_at TEXT NOT NULL
        )
    """)
```

Add these constants near `_LIST_TTL`:

```python
_DAILY_TTL = timedelta(hours=1)
_STATIC_TTL = timedelta(hours=4)
```

Append these four functions at the end of `cache.py`:

```python
def get_daily_data(cache_key: str) -> dict | None:
    try:
        with _connect() as conn:
            row = conn.execute(
                "SELECT data, fetched_at FROM daily_data WHERE cache_key = ?",
                (cache_key,),
            ).fetchone()
            if not row:
                return None
            fetched_at = datetime.fromisoformat(row[1])
            if datetime.now(UTC) - fetched_at > _DAILY_TTL:
                return None
            return json.loads(row[0])
    except Exception:
        logger.warning("Cache read failed for daily_data key=%s", cache_key)
        return None


def set_daily_data(cache_key: str, data: dict) -> None:
    try:
        with _connect() as conn:
            conn.execute(
                "INSERT OR REPLACE INTO daily_data VALUES (?, ?, ?)",
                (cache_key, json.dumps(data), datetime.now(UTC).isoformat()),
            )
            conn.commit()
    except Exception:
        logger.warning("Cache write failed for daily_data key=%s", cache_key)


def get_static_data(cache_key: str) -> dict | list | None:
    try:
        with _connect() as conn:
            row = conn.execute(
                "SELECT data, fetched_at FROM static_data WHERE cache_key = ?",
                (cache_key,),
            ).fetchone()
            if not row:
                return None
            fetched_at = datetime.fromisoformat(row[1])
            if datetime.now(UTC) - fetched_at > _STATIC_TTL:
                return None
            return json.loads(row[0])
    except Exception:
        logger.warning("Cache read failed for static_data key=%s", cache_key)
        return None


def set_static_data(cache_key: str, data: dict | list) -> None:
    try:
        with _connect() as conn:
            conn.execute(
                "INSERT OR REPLACE INTO static_data VALUES (?, ?, ?)",
                (cache_key, json.dumps(data), datetime.now(UTC).isoformat()),
            )
            conn.commit()
    except Exception:
        logger.warning("Cache write failed for static_data key=%s", cache_key)
```

- [ ] **Step 4: Run tests to verify they pass**

```bash
uv run pytest tests/test_cache.py -v
```

Expected: all PASS.

- [ ] **Step 5: Commit**

```bash
git add src/garmin_mcp/cache.py tests/test_cache.py
git commit -m "feat: add daily_data and static_data cache tables with TTL"
```

---

### Task 2: Add new GarminClient methods

**Files:**
- Modify: `src/garmin_mcp/garmin.py`
- Test: `tests/test_garmin.py`

- [ ] **Step 1: Write the failing tests**

Append to `tests/test_garmin.py`:

```python
def test_get_daily_wellness_calls_all_endpoints(client, mock_api):
    mock_api.get_stats.return_value = {"totalSteps": 8000}
    mock_api.get_sleep_data.return_value = {"dailySleepDTO": {"sleepScore": 78}}
    mock_api.get_body_battery.return_value = [{"charged": 85, "drained": 15}]
    mock_api.get_hrv_data.return_value = {"hrvSummary": {"lastNight": 55}}
    mock_api.get_rhr_day.return_value = {"restingHeartRate": 52}

    result = client.get_daily_wellness("2026-04-23")

    assert result["stats"] == {"totalSteps": 8000}
    assert result["sleep"] == {"dailySleepDTO": {"sleepScore": 78}}
    assert result["body_battery"] == [{"charged": 85, "drained": 15}]
    assert result["hrv"] == {"hrvSummary": {"lastNight": 55}}
    assert result["resting_hr"] == {"restingHeartRate": 52}
    mock_api.get_stats.assert_called_once_with("2026-04-23")
    mock_api.get_sleep_data.assert_called_once_with("2026-04-23")
    mock_api.get_body_battery.assert_called_once_with("2026-04-23")
    mock_api.get_hrv_data.assert_called_once_with("2026-04-23")
    mock_api.get_rhr_day.assert_called_once_with("2026-04-23")


def test_get_training_status_calls_both_endpoints(client, mock_api):
    mock_api.get_training_readiness.return_value = {"score": 72, "level": "GOOD"}
    mock_api.get_training_status.return_value = {"trainingStatusDTO": {"latestTrainingStatusVO": {"trainingStatus": "MAINTAINING"}}}

    result = client.get_training_status("2026-04-23")

    assert result["readiness"] == {"score": 72, "level": "GOOD"}
    assert result["status"] == {"trainingStatusDTO": {"latestTrainingStatusVO": {"trainingStatus": "MAINTAINING"}}}
    mock_api.get_training_readiness.assert_called_once_with("2026-04-23")
    mock_api.get_training_status.assert_called_once_with("2026-04-23")


def test_get_race_predictions_returns_result(client, mock_api):
    mock_api.get_race_predictions.return_value = {"racePredictions": [{"raceDistance": "5K", "timePrediction": 1500}]}
    result = client.get_race_predictions()
    assert result == {"racePredictions": [{"raceDistance": "5K", "timePrediction": 1500}]}
    mock_api.get_race_predictions.assert_called_once_with()


def test_get_personal_records_returns_result(client, mock_api):
    mock_api.get_personal_record.return_value = {"personalRecords": [{"typeId": 1, "value": 300}]}
    result = client.get_personal_records()
    assert result == {"personalRecords": [{"typeId": 1, "value": 300}]}
    mock_api.get_personal_record.assert_called_once_with()
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
uv run pytest tests/test_garmin.py -k "wellness or training_status or race or personal" -v
```

Expected: FAIL — `GarminClient` has no attribute `get_daily_wellness`.

- [ ] **Step 3: Add methods to `GarminClient` in `garmin.py`**

Append inside the `GarminClient` class, after `get_activity_details`:

```python
    def get_daily_wellness(self, date: str) -> dict:
        return {
            "stats": _with_retry(self._api.get_stats, date),
            "sleep": _with_retry(self._api.get_sleep_data, date),
            "body_battery": _with_retry(self._api.get_body_battery, date),
            "hrv": _with_retry(self._api.get_hrv_data, date),
            "resting_hr": _with_retry(self._api.get_rhr_day, date),
        }

    def get_training_status(self, date: str) -> dict:
        return {
            "readiness": _with_retry(self._api.get_training_readiness, date),
            "status": _with_retry(self._api.get_training_status, date),
        }

    def get_race_predictions(self) -> dict:
        return _with_retry(self._api.get_race_predictions)

    def get_personal_records(self) -> dict:
        return _with_retry(self._api.get_personal_record)
```

- [ ] **Step 4: Run tests to verify they pass**

```bash
uv run pytest tests/test_garmin.py -v
```

Expected: all PASS.

- [ ] **Step 5: Commit**

```bash
git add src/garmin_mcp/garmin.py tests/test_garmin.py
git commit -m "feat: add get_daily_wellness, get_training_status, get_race_predictions, get_personal_records to GarminClient"
```

---

### Task 3: Add new MCP tools to server

**Files:**
- Modify: `src/garmin_mcp/server.py`
- Test: `tests/test_server.py`

- [ ] **Step 1: Write the failing tests**

Append to `tests/test_server.py`:

```python
def test_get_daily_wellness_fetches_and_caches(mock_garmin_client):
    from garmin_mcp.server import get_daily_wellness
    mock_garmin_client.get_daily_wellness.return_value = {"stats": {"totalSteps": 8000}, "sleep": {}, "body_battery": [], "hrv": None, "resting_hr": {}}
    result = get_daily_wellness("2026-04-23")
    assert result["stats"] == {"totalSteps": 8000}
    mock_garmin_client.get_daily_wellness.assert_called_once_with("2026-04-23")


def test_get_daily_wellness_uses_cache(mock_garmin_client):
    from garmin_mcp.server import get_daily_wellness
    cached = {"stats": {"totalSteps": 5000}, "sleep": {}, "body_battery": [], "hrv": None, "resting_hr": {}}
    cache.set_daily_data("wellness:2026-04-23", cached)
    result = get_daily_wellness("2026-04-23")
    assert result["stats"]["totalSteps"] == 5000
    mock_garmin_client.get_daily_wellness.assert_not_called()


def test_get_daily_wellness_defaults_to_today(mock_garmin_client):
    from datetime import date
    from garmin_mcp.server import get_daily_wellness
    mock_garmin_client.get_daily_wellness.return_value = {"stats": {}, "sleep": {}, "body_battery": [], "hrv": None, "resting_hr": {}}
    get_daily_wellness()
    mock_garmin_client.get_daily_wellness.assert_called_once_with(date.today().isoformat())


def test_get_training_status_fetches_and_caches(mock_garmin_client):
    from garmin_mcp.server import get_training_status
    mock_garmin_client.get_training_status.return_value = {"readiness": {"score": 72}, "status": {}}
    result = get_training_status("2026-04-23")
    assert result["readiness"]["score"] == 72
    mock_garmin_client.get_training_status.assert_called_once_with("2026-04-23")


def test_get_training_status_uses_cache(mock_garmin_client):
    from garmin_mcp.server import get_training_status
    cached = {"readiness": {"score": 55}, "status": {}}
    cache.set_daily_data("training:2026-04-23", cached)
    result = get_training_status("2026-04-23")
    assert result["readiness"]["score"] == 55
    mock_garmin_client.get_training_status.assert_not_called()


def test_get_training_status_defaults_to_today(mock_garmin_client):
    from datetime import date
    from garmin_mcp.server import get_training_status
    mock_garmin_client.get_training_status.return_value = {"readiness": {}, "status": {}}
    get_training_status()
    mock_garmin_client.get_training_status.assert_called_once_with(date.today().isoformat())


def test_get_race_predictions_fetches_and_caches(mock_garmin_client):
    from garmin_mcp.server import get_race_predictions
    mock_garmin_client.get_race_predictions.return_value = {"racePredictions": []}
    result = get_race_predictions()
    assert result == {"racePredictions": []}
    mock_garmin_client.get_race_predictions.assert_called_once_with()


def test_get_race_predictions_uses_cache(mock_garmin_client):
    from garmin_mcp.server import get_race_predictions
    cache.set_static_data("race_predictions", {"racePredictions": [{"distance": "5K"}]})
    result = get_race_predictions()
    assert result["racePredictions"][0]["distance"] == "5K"
    mock_garmin_client.get_race_predictions.assert_not_called()


def test_get_personal_records_fetches_and_caches(mock_garmin_client):
    from garmin_mcp.server import get_personal_records
    mock_garmin_client.get_personal_records.return_value = {"personalRecords": []}
    result = get_personal_records()
    assert result == {"personalRecords": []}
    mock_garmin_client.get_personal_records.assert_called_once_with()


def test_get_personal_records_uses_cache(mock_garmin_client):
    from garmin_mcp.server import get_personal_records
    cache.set_static_data("personal_records", {"personalRecords": [{"type": "running"}]})
    result = get_personal_records()
    assert result["personalRecords"][0]["type"] == "running"
    mock_garmin_client.get_personal_records.assert_not_called()
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
uv run pytest tests/test_server.py -k "wellness or training_status or race or personal" -v
```

Expected: FAIL — `get_daily_wellness` not imported.

- [ ] **Step 3: Add tools to `server.py`**

Add import at top of `server.py` (add `date` is already imported; just ensure it is):

```python
from datetime import date
```

Append after the existing `get_activity_details` tool:

```python
@mcp.tool()
def get_daily_wellness(date: str = "") -> dict:
    """Get a daily wellness snapshot for a date (YYYY-MM-DD, defaults to today).
    Returns combined stats (steps, calories), sleep (stages, score, duration),
    body battery, HRV summary, and resting heart rate."""
    if not date:
        date = date.today().isoformat()
    cache_key = f"wellness:{date}"
    cached = cache.get_daily_data(cache_key)
    if cached is not None:
        return cached
    client = _get_client()
    data = client.get_daily_wellness(date)
    cache.set_daily_data(cache_key, data)
    return data


@mcp.tool()
def get_training_status(date: str = "") -> dict:
    """Get training readiness and training status for a date (YYYY-MM-DD, defaults to today).
    Returns readiness score with contributing factors and training load/status."""
    if not date:
        date = date.today().isoformat()
    cache_key = f"training:{date}"
    cached = cache.get_daily_data(cache_key)
    if cached is not None:
        return cached
    client = _get_client()
    data = client.get_training_status(date)
    cache.set_daily_data(cache_key, data)
    return data


@mcp.tool()
def get_race_predictions() -> dict:
    """Get current predicted race times for 5K, 10K, half marathon, and marathon
    based on recent training data."""
    cached = cache.get_static_data("race_predictions")
    if cached is not None:
        return cached
    client = _get_client()
    data = client.get_race_predictions()
    cache.set_static_data("race_predictions", data)
    return data


@mcp.tool()
def get_personal_records() -> dict:
    """Get personal records across all activity types."""
    cached = cache.get_static_data("personal_records")
    if cached is not None:
        return cached
    client = _get_client()
    data = client.get_personal_records()
    cache.set_static_data("personal_records", data)
    return data
```

**Note:** `date` is used both as a parameter name and `date.today()` — rename the parameter to `for_date` in the function signatures to avoid the shadowing bug. Update both the parameter and all references inside the function bodies:

```python
@mcp.tool()
def get_daily_wellness(for_date: str = "") -> dict:
    """Get a daily wellness snapshot for a date (YYYY-MM-DD, defaults to today).
    Returns combined stats (steps, calories), sleep (stages, score, duration),
    body battery, HRV summary, and resting heart rate."""
    if not for_date:
        for_date = date.today().isoformat()
    cache_key = f"wellness:{for_date}"
    cached = cache.get_daily_data(cache_key)
    if cached is not None:
        return cached
    client = _get_client()
    data = client.get_daily_wellness(for_date)
    cache.set_daily_data(cache_key, data)
    return data


@mcp.tool()
def get_training_status(for_date: str = "") -> dict:
    """Get training readiness and training status for a date (YYYY-MM-DD, defaults to today).
    Returns readiness score with contributing factors and training load/status."""
    if not for_date:
        for_date = date.today().isoformat()
    cache_key = f"training:{for_date}"
    cached = cache.get_daily_data(cache_key)
    if cached is not None:
        return cached
    client = _get_client()
    data = client.get_training_status(for_date)
    cache.set_daily_data(cache_key, data)
    return data
```

Also update the corresponding tests to use `for_date` parameter name where needed (the server tests call `get_daily_wellness("2026-04-23")` positionally, so they're fine).

- [ ] **Step 4: Run tests to verify they pass**

```bash
uv run pytest tests/test_server.py -v
```

Expected: all PASS.

- [ ] **Step 5: Commit**

```bash
git add src/garmin_mcp/server.py tests/test_server.py
git commit -m "feat: add get_daily_wellness, get_training_status, get_race_predictions, get_personal_records MCP tools"
```

---

### Task 4: Update README

**Files:**
- Modify: `README.md`

- [ ] **Step 1: Replace the Available Tools table**

Replace:

```markdown
## Available Tools

| Tool | Description |
|------|-------------|
| `get_last_activity` | Most recent activity with full details |
| `get_activities` | Activities in a date range, optional type filter |
| `get_activity_details` | Full detail for a specific activity ID |
```

With:

```markdown
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
```

- [ ] **Step 2: Replace the Example Usage section**

Replace:

```markdown
## Example Usage

Ask Claude:

- "Show me my last workout"
- "How has my running pace changed over the last 30 days?"
- "Compare my heart rate zones from this week's runs"
- "What was my longest ride in March?"
```

With:

```markdown
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
```

- [ ] **Step 3: Update the Cache section**

Replace:

```markdown
## Cache

Activities are cached in `~/.garmin_mcp_cache.db`.

- **Activity details** — cached permanently (historical data doesn't change)
- **Activity lists** — cached for 1 hour, then re-fetched
```

With:

```markdown
## Cache

Activities are cached in `~/.garmin_mcp_cache.db`.

| Data type | TTL | Reason |
|-----------|-----|--------|
| Activity details | permanent | Historical data never changes |
| Activity lists | 1 hour | Newly completed activities appear |
| Daily wellness / training status | 1 hour | Syncs throughout the day |
| Race predictions / personal records | 4 hours | Changes slowly with fitness |
```

- [ ] **Step 4: Commit**

```bash
git add README.md
git commit -m "docs: update README with new wellness and performance tools"
```

---

### Task 5: Full test suite verification

- [ ] **Step 1: Run all tests**

```bash
uv run pytest -v
```

Expected: all tests PASS, no warnings about missing fixtures or imports.