import getpass
import logging

from garminconnect import Garmin

from garmin_mcp.garmin import _token_dir


def setup_main() -> None:
    email = input("Garmin email: ")
    password = getpass.getpass("Garmin password: ")
    token_dir = _token_dir()
    print("Logging in... (~20s on first run due to Garmin's bot protection)")
    logging.getLogger("garminconnect").setLevel(logging.ERROR)
    try:
        api = Garmin(email, password)
        api.login(tokenstore=token_dir)
    except Exception as exc:
        print(f"Login failed: {exc}")
        raise SystemExit(1)
    print(f"Authenticated. Tokens saved to {token_dir}.")
    print("Run 'garmin-mcp' to start the server.")
