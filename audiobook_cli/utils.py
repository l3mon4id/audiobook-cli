from os import getenv
from os.path import expanduser
from os.path import join as p_join
from sys import platform

from audible.auth import Authenticator


def config_path() -> str:
    if "linux" in platform or "unix" in platform or "darwin" in platform:
        return p_join(expanduser("~"), ".config", "audiobook-cli")
    else:
        appdata = getenv("APPDATA")
        if not appdata:
            raise ValueError("Could not grab APPDATA environment variable.")
        return p_join(appdata, "audiobook-cli")


def audible_auth_file() -> str:
    return p_join(config_path(), "audible.auth")


def get_audible_auth_from_file(
    locale: str = "us", password: str | None = None
) -> Authenticator:
    return Authenticator.from_file(
        audible_auth_file(),
        password=password,
        locale=locale,
        encryption="bytes" if password else None,
    )


def ffmpeg():
    if "windows" in platform:
        return "ffmpeg.exe"
    return "ffmpeg"


def ffprobe():
    if "windows" in platform:
        return "ffprobe.exe"
    return "ffprobe"
