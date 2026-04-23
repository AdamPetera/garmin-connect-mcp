import getpass

from garminconnect import Garmin

from garmin_mcp.garmin import _token_dir


def setup_main() -> None:
    email = input("Garmin email: ")
    password = getpass.getpass("Garmin password: ")
    print("Logging in...")
    try:
        api = Garmin(email, password)
        api.login()
    except Exception as exc:
        print(f"Login failed: {exc}")
        raise SystemExit(1)
    token_dir = _token_dir()
    try:
        api.client.dump(token_dir)
        print(f"Authenticated. Tokens saved to {token_dir}.")
        print("Run 'garmin-mcp' to start the server.")
    except Exception as exc:
        print(f"Warning: could not save tokens: {exc}")
        print("Authenticated for this session only.")
