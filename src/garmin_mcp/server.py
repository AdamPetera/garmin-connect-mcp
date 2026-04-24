import logging
import threading
from datetime import date

from mcp.server.fastmcp import FastMCP

from garmin_mcp import cache, garmin

logger = logging.getLogger(__name__)

mcp = FastMCP("garmin-connect")
_client: garmin.GarminClient | None = None
_client_lock = threading.Lock()


def _get_client() -> garmin.GarminClient:
    global _client
    if _client is None:
        with _client_lock:
            if _client is None:
                _client = garmin.GarminClient()
    return _client


@mcp.tool()
def get_last_activity() -> dict:
    """Get the most recent Garmin activity with full details including laps and HR. Returns {} if no activities found."""
    client = _get_client()
    activity = client.get_last_activity()
    if not activity:
        return {}
    activity_id = str(activity.get("activityId", ""))
    if not activity_id:
        logger.warning("get_last_activity: response missing activityId, returning summary only")
        return {}
    cached = cache.get_activity_details(activity_id)
    if cached is not None:
        return cached
    details = client.get_activity_details(activity_id)
    cache.set_activity_details(activity_id, details)
    return details


@mcp.tool()
def get_activities(
    start_date: str,
    end_date: str = "",
    activity_type: str = "",
) -> list:
    """Get activities in a date range. Dates in YYYY-MM-DD format. activity_type filters by sport e.g. 'running', 'cycling'. Returns list of activity summaries."""
    if not end_date:
        end_date = date.today().isoformat()
    cache_key = f"{start_date}:{end_date}:{activity_type}"
    cached = cache.get_activity_list(cache_key)
    if cached is not None:
        return cached
    client = _get_client()
    activities = client.get_activities(start_date, end_date, activity_type or None)
    cache.set_activity_list(cache_key, activities)
    return activities


@mcp.tool()
def get_activity_details(activity_id: str) -> dict:
    """Get full details for a specific Garmin activity ID, including laps, splits, and HR zones."""
    cached = cache.get_activity_details(activity_id)
    if cached is not None:
        return cached
    client = _get_client()
    details = client.get_activity_details(activity_id)
    cache.set_activity_details(activity_id, details)
    return details


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


@mcp.tool()
def get_workouts(start: int = 0, limit: int = 100) -> list:
    """List saved workouts from Garmin Connect. Returns up to `limit` workouts starting at offset `start`."""
    cache_key = f"workouts:{start}:{limit}"
    cached = cache.get_static_data(cache_key)
    if cached is not None:
        return cached
    client = _get_client()
    data = client.get_workouts(start, limit)
    cache.set_static_data(cache_key, data)
    return data


@mcp.tool()
def get_workout_by_id(workout_id: str) -> dict:
    """Get a saved workout by its ID."""
    cache_key = f"workout:{workout_id}"
    cached = cache.get_static_data(cache_key)
    if cached is not None:
        return cached
    client = _get_client()
    data = client.get_workout_by_id(workout_id)
    cache.set_static_data(cache_key, data)
    return data


@mcp.tool()
def upload_workout(workout_data: dict) -> dict:
    """Create a new workout on Garmin Connect. Pass a workout definition dict with workoutName, sportType, workoutSegments, etc."""
    client = _get_client()
    return client.upload_workout(workout_data)


@mcp.tool()
def upload_running_workout(workout_data: dict) -> dict:
    """Create a running workout on Garmin Connect."""
    client = _get_client()
    return client.upload_running_workout(workout_data)


@mcp.tool()
def upload_cycling_workout(workout_data: dict) -> dict:
    """Create a cycling workout on Garmin Connect."""
    client = _get_client()
    return client.upload_cycling_workout(workout_data)


@mcp.tool()
def upload_hiking_workout(workout_data: dict) -> dict:
    """Create a hiking workout on Garmin Connect."""
    client = _get_client()
    return client.upload_hiking_workout(workout_data)


@mcp.tool()
def upload_swimming_workout(workout_data: dict) -> dict:
    """Create a swimming workout on Garmin Connect."""
    client = _get_client()
    return client.upload_swimming_workout(workout_data)


@mcp.tool()
def upload_walking_workout(workout_data: dict) -> dict:
    """Create a walking workout on Garmin Connect."""
    client = _get_client()
    return client.upload_walking_workout(workout_data)


@mcp.tool()
def schedule_workout(workout_id: str, scheduled_date: str) -> dict:
    """Schedule a saved workout to a calendar date. scheduled_date in YYYY-MM-DD format."""
    client = _get_client()
    return client.schedule_workout(workout_id, scheduled_date)


@mcp.tool()
def unschedule_workout(scheduled_workout_id: str) -> dict:
    """Remove a workout from the calendar by its scheduled workout ID."""
    client = _get_client()
    return client.unschedule_workout(scheduled_workout_id)


@mcp.tool()
def get_scheduled_workouts(year: int, month: int) -> dict:
    """Get all scheduled workouts for a given year and month."""
    cache_key = f"scheduled_workouts:{year}:{month}"
    cached = cache.get_daily_data(cache_key)
    if cached is not None:
        return cached
    client = _get_client()
    data = client.get_scheduled_workouts(year, month)
    cache.set_daily_data(cache_key, data)
    return data


@mcp.tool()
def get_scheduled_workout_by_id(scheduled_workout_id: str) -> dict:
    """Get a specific scheduled workout by its scheduled workout ID."""
    cache_key = f"scheduled_workout:{scheduled_workout_id}"
    cached = cache.get_daily_data(cache_key)
    if cached is not None:
        return cached
    client = _get_client()
    data = client.get_scheduled_workout_by_id(scheduled_workout_id)
    cache.set_daily_data(cache_key, data)
    return data


@mcp.tool()
def delete_workout(workout_id: str) -> dict:
    """Delete a saved workout by its ID."""
    client = _get_client()
    return client.delete_workout(workout_id)


def main() -> None:
    logging.basicConfig(level=logging.WARNING)
    mcp.run()
