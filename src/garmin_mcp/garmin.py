import logging
import os
import time
from pathlib import Path

from dotenv import load_dotenv
from garminconnect import Garmin

load_dotenv()

logger = logging.getLogger(__name__)


def _token_dir() -> str:
    return os.environ.get("GARMIN_TOKEN_DIR", str(Path.home() / ".garminconnect"))


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
        email = os.environ.get("GARMIN_EMAIL")
        password = os.environ.get("GARMIN_PASSWORD")
        api = Garmin(email, password) if (email and password) else Garmin()
        try:
            api.login(tokenstore=token_dir)
        except Exception as exc:
            if not email or not password:
                raise RuntimeError(
                    "Run 'garmin-mcp-setup' to authenticate, "
                    "or set GARMIN_EMAIL and GARMIN_PASSWORD in .env"
                ) from exc
            raise
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

    def get_race_predictions(self) -> dict | list:
        return _with_retry(self._api.get_race_predictions)

    def get_personal_records(self) -> dict | list:
        return _with_retry(self._api.get_personal_record)

    def get_workouts(self, start: int = 0, limit: int = 100) -> list:
        return _with_retry(self._api.get_workouts, start, limit)

    def get_workout_by_id(self, workout_id: str) -> dict:
        return _with_retry(self._api.get_workout_by_id, workout_id)

    def upload_workout(self, workout_data: dict | list | str) -> dict:
        return _with_retry(self._api.upload_workout, workout_data)

    def upload_running_workout(self, workout_data: dict) -> dict:
        return _with_retry(self._api.upload_running_workout, workout_data)

    def upload_cycling_workout(self, workout_data: dict) -> dict:
        return _with_retry(self._api.upload_cycling_workout, workout_data)

    def upload_hiking_workout(self, workout_data: dict) -> dict:
        return _with_retry(self._api.upload_hiking_workout, workout_data)

    def upload_swimming_workout(self, workout_data: dict) -> dict:
        return _with_retry(self._api.upload_swimming_workout, workout_data)

    def upload_walking_workout(self, workout_data: dict) -> dict:
        return _with_retry(self._api.upload_walking_workout, workout_data)

    def schedule_workout(self, workout_id: str, date_str: str) -> dict:
        return _with_retry(self._api.schedule_workout, workout_id, date_str)

    def unschedule_workout(self, scheduled_workout_id: str) -> dict:
        return _with_retry(self._api.unschedule_workout, scheduled_workout_id)

    def get_scheduled_workouts(self, year: int | str, month: int | str) -> dict:
        return _with_retry(self._api.get_scheduled_workouts, year, month)

    def get_scheduled_workout_by_id(self, scheduled_workout_id: str) -> dict:
        return _with_retry(self._api.get_scheduled_workout_by_id, scheduled_workout_id)

    def delete_workout(self, workout_id: str) -> dict:
        return _with_retry(self._api.delete_workout, workout_id)
