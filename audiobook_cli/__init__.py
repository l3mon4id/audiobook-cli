import logging
from re import sub
import subprocess
from glob import glob
from os import rename
from typing import List

import typer
from rich.console import Console
from rich.logging import RichHandler
from typer import Typer

from audiobook_cli.audible import app as audible_app
from audiobook_cli.utils import (
    ffmpeg,
    ffprobe,
    get_metadata_from_file,
    path_from_metadata,
)

app = Typer(name="audiobook-cli", help="Audiobook python CLI")
app.add_typer(audible_app)

logging.basicConfig(level="INFO", handlers=[RichHandler()])


@app.command(
    name="merge-mp3",
    help="Merges mp3 chapters or snippets into a single m4b file using ffmpeg.",
)
def merge(
    output: str = typer.Option(..., "--output", "-o", help="Output file."),
    run: bool = typer.Option(False, "--run", "-r", help="Actually run the command."),
    chapterize: bool = typer.Option(
        False,
        "--chapterize",
        "-c",
        help="Take timestamps from mp3 files and include them as chapters.",
    ),
    merge_file_glob: str = typer.Argument(
        ..., help="Glob which matches all files to merge."
    ),
):
    c = Console()
    file_list = glob(merge_file_glob)
    file_list = sorted(file_list)
    command = [
        ffmpeg(),
        "-f",
        "concat",
        "-safe",
        "0",
        "-i",
        "files.txt",
        "-vn",
        "-acodec",
        "aac",
        "-ac",
        "2",
        "tmp-" + output,
    ]
    with open("files.txt", "w") as fh:
        for file in file_list:
            fh.write(f"file '{file}'\n")
    if not run:
        c.print(f"Would execute\n    {' '.join(command)}\nfor merging the files.")
    else:
        subprocess.run(command)

    if chapterize:
        if not run:
            c.print("Would grab chapter timestamps via ffprobe now.")
        else:
            current_timestamp = 0
            chapters = ";FFMETADATA1\n"
            for idx, file in enumerate(file_list):
                command = [ffprobe(), "-show_entries", "format=duration", file]
                command_output = subprocess.run(
                    command, capture_output=True, text=True
                ).stdout
                command_output = command_output.splitlines()[1]
                timestamp = int(float(command_output.split("=")[1]) * 1000)
                chapters += "[CHAPTER]\n"
                chapters += "TIMEBASE=1/1000\n"
                chapters += f"START={current_timestamp}\n"
                chapters += f"END={current_timestamp + timestamp}\n"
                chapters += f"title=Chapter {idx + 1}\n\n"
                current_timestamp += timestamp

            with open("chapters.txt", "w") as fh:
                fh.write(chapters)

            subprocess.run(
                [
                    ffmpeg(),
                    "-i",
                    "tmp-" + output,
                    "-i",
                    "chapters.txt",
                    "-map_metadata",
                    "1",
                    "-movflags",
                    "use_metadata_tags",
                    "-codec",
                    "copy",
                    output,
                ]
            )
    else:
        if not run:
            c.print(f"Would rename file to {output} now.")
        else:
            rename("tmp-" + output, output)


@app.command(
    name="add-meta",
    help="Adds previously generated metadata file via ffmpeg to an m4b audiobook file.",
)
def add_meta(
    audiobook: str = typer.Option(..., "--audiobook", "-a", help="Path to audiobook."),
    meta: str = typer.Option(..., "--meta", "-m", help="Path to ffmpeg metadata file."),
    output: str = typer.Option(..., "--output", "-o", help="Path to output file."),
):
    subprocess.run(
        [
            ffmpeg(),
            "-i",
            audiobook,
            "-i",
            meta,
            "-map_metadata",
            "1",
            "-movflags",
            "use_metadata_tags",
            "-codec",
            "copy",
            output,
        ]
    )


@app.command(
    name="get-meta",
    help="Displays typical audiobook metadata information extracted via ffprobe.",
)
def get_meta(
    files: List[str] = typer.Argument(..., help="One or multiple audiobook files."),
):
    c = Console()
    for file in files:
        c.print(f"{file}")
        for k, v in get_metadata_from_file(file).items():
            c.print(f"  {k.capitalize()}: {v}")


@app.command(
    name="get-path", help="Creates and displays a filepath based on audiobook metadata."
)
def get_path(
    include_filename: bool = typer.Option(
        False, "--include-filename", "-f", help="Include filename in the path."
    ),
    series_subdir: bool = typer.Option(
        False,
        "--series-subdir",
        "-s",
        help="Creates multiple subdirs for series and series part.",
    ),
    series_from_subtitle: bool = typer.Option(
        False,
        "--series-from-subtitle",
        "-S",
        help="Use subtitle metadata in case series/part metadata is missing.",
    ),
    file: str = typer.Argument(..., help="File to create a filepath for."),
):
    c = Console()
    try:
        metadata = get_metadata_from_file(file)
        c.print(
            path_from_metadata(
                metadata,
                include_filename=include_filename,
                series_subdir=series_subdir,
                use_subtitle_as_series=series_from_subtitle,
            )
        )
    except KeyError as ke:
        c.print(f"[red]Missing metadata {ke}")
        raise typer.Exit(-1)


@app.command(name="trim", help="Removed non-standard metadata from m4b files.")
def trim(
    remove: bool = typer.Option(
        False, "--remove", "-r", help="Remove the original file after copying the data."
    ),
    file: str = typer.Argument(..., help="File to remove metadata from."),
):
    c = Console()
    tmp = f".tmp-{file}"
    c.print(f"Moving file {file}.")
    rename(file, tmp)
    c.print("Create file copy with trimmed metadata.")
    command = [
        ffmpeg(),
        "-i",
        tmp,
        "-movflags",
        "use_metadata_tags",
        "-map_metadata",
        "0",
        "-c",
        "copy",
        file,
    ]
    subprocess.run(command, capture_output=True, text=True)
    if remove:
        c.print(f"Removing {tmp}")
