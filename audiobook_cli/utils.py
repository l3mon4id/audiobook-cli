import subprocess
from os import getenv
from os.path import expanduser, join
from os.path import join as p_join
from sys import platform
from typing import Dict
import re
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


def get_metadata_from_file(file: str):
    metadata = {}
    command = [
        ffprobe(),
        "-loglevel",
        "error",
        "-show_entries",
        "format_tags=artist,album,title,series,part,series-part,isbn,asin,audible_asin,composer",
        "-print_format",
        "compact",
        file,
    ]
    command_output = subprocess.run(command, capture_output=True, text=True).stdout
    data = command_output.split("|")
    for chunk in data:
        if "tag" in chunk:
            chunk = chunk[4:]
            k, v = chunk.split("=")
            metadata.update({k.lower(): v.strip()})
    return metadata


def path_from_metadata(
    metadata: Dict,
    use_subtitle_as_series: bool = False,
    include_filename: bool = False,
    series_subdir: bool = False,
):
    """Creates a path from the book metadata."""
    series_part = False
    series = ""
    part = ""
    if "series" in metadata and "part" in metadata:
        series_part = True
        series = metadata["series"]
        part = metadata["part"]
    elif (
        "subtitle" in metadata
        and re.match(r".* [0-9]{1,3}$", metadata["subtitle"])
        and use_subtitle_as_series
    ):
        series_part = True
        split_pos = metadata["subtitle"].rfind(" ")
        series = metadata["subtitle"][:split_pos].strip()
        part = metadata["subtitle"][split_pos:].strip()

    path = metadata["artist"]
    if series_part:
        path = join(path, series)

    if series_subdir:
        path = join(path, series + " " + part, metadata["title"])
    else:
        path = join(path, part + " " + metadata["title"])
    if include_filename:
        path = join(path, metadata["artist"] + " - " + metadata["title"] + ".m4b")

    return path
