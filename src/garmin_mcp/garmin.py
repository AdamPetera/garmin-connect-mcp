import os
import time

from dotenv import load_dotenv
from garminconnect import Garmin

load_dotenv()


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
        email = os.environ.get("GARMIN_EMAIL")
        password = os.environ.get("GARMIN_PASSWORD")
        if not email or not password:
            raise RuntimeError(
                "GARMIN_EMAIL and GARMIN_PASSWORD must be set in .env"
            )
        self._api = Garmin(email, password)
        self._api.login()

    def get_last_activity(self) -> dict:
        activities = _with_retry(self._api.get_activities, 0, 1)
        return activities[0] if activities else {}

    def get_activities(
        self, start_date: str, end_date: str, activity_type: str | None = None
    ) -> list:
        return _with_retry(self._api.get_activities_by_date, start_date, end_date, activity_type)

    def get_activity_details(self, activity_id: str) -> dict:
        return _with_retry(self._api.get_activity, str(activity_id))
