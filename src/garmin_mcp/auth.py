import getpass
import os
from pathlib import Path

from garminconnect import Garmin


def _token_dir() -> str:
    return os.environ.get("GARMIN_TOKEN_DIR", str(Path.home() / ".garth"))


def setup_main() -> None:
    email = input("Garmin email: ")
    password = getpass.getpass("Garmin password: ")
    print("Logging in...")
    api = Garmin(email, password)
    api.login()
    token_dir = _token_dir()
    try:
        api.garth.dump(token_dir)
        print(f"Authenticated. Tokens saved to {token_dir}.")
        print("Run 'garmin-mcp' to start the server.")
    except Exception as exc:
        print(f"Warning: could not save tokens: {exc}")
        print("Authenticated for this session only.")
