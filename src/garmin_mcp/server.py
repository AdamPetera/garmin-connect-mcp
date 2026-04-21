import logging
from datetime import date

from mcp.server.fastmcp import FastMCP

from garmin_mcp import cache, garmin

logging.basicConfig(level=logging.WARNING)

mcp = FastMCP("garmin-connect")
_client: garmin.GarminClient | None = None


def _get_client() -> garmin.GarminClient:
    global _client
    if _client is None:
        _client = garmin.GarminClient()
    return _client


@mcp.tool()
def get_last_activity() -> dict:
    """Get the most recent Garmin activity with full details including laps and HR."""
    client = _get_client()
    activity = client.get_last_activity()
    if not activity:
        return {}
    activity_id = str(activity.get("activityId", ""))
    if not activity_id:
        return activity
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
    """Get activities in a date range. Dates in YYYY-MM-DD. activity_type e.g. 'running', 'cycling'."""
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
    """Get full details for a specific activity by ID, including laps, splits, and HR zones."""
    cached = cache.get_activity_details(activity_id)
    if cached is not None:
        return cached
    client = _get_client()
    details = client.get_activity_details(activity_id)
    cache.set_activity_details(activity_id, details)
    return details


def main() -> None:
    mcp.run()
