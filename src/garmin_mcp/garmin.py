import logging
import os
import time
from pathlib import Path

from dotenv import load_dotenv
from garminconnect import Garmin

load_dotenv()

logger = logging.getLogger(__name__)


def _token_dir() -> str:
    return os.environ.get("GARMIN_TOKEN_DIR", str(Path.home() / ".garth"))


def _with_retry(fn, *args, **kwargs):
    try:
        return fn(*args, **kwargs)
    except Exception as first_err:
        time.sleep(2)
        try:
            return fn(*args, **kwargs)
        except Exception as second_err:
            raise RuntimeError(str(second_err)) from first_err


class GarminClient:
    def __init__(self) -> None:
        token_dir = _token_dir()

        # 1. Try garth tokens
        try:
            api = Garmin()
            api.garth.load(token_dir)
            api.login()
            self._api = api
            return
        except (FileNotFoundError, OSError):
            pass

        # 2. Fall back to env credentials
        email = os.environ.get("GARMIN_EMAIL")
        password = os.environ.get("GARMIN_PASSWORD")
        if not email or not password:
            raise RuntimeError(
                "Run 'garmin-mcp-setup' to authenticate, "
                "or set GARMIN_EMAIL and GARMIN_PASSWORD in .env"
            )
        api = Garmin(email, password)
        api.login()
        try:
            api.garth.dump(token_dir)
        except Exception as exc:
            logger.warning("Could not save auth tokens to %s: %s", token_dir, exc)
        self._api = api

    def get_last_activity(self) -> dict:
        activities = _with_retry(self._api.get_activities, 0, 1)
        return activities[0] if activities else {}

    def get_activities(
        self, start_date: str, end_date: str, activity_type: str | None = None
    ) -> list:
        return _with_retry(self._api.get_activities_by_date, start_date, end_date, activity_type)

    def get_activity_details(self, activity_id: str) -> dict:
        return _with_retry(self._api.get_activity, str(activity_id))
