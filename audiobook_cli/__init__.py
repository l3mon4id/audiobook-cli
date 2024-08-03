from os import link
from glob import glob
from re import sub
import audible
import logging
import typer
from typer import Typer
from audiobook_cli.utils import audible_auth_file, get_audible_auth_from_file
from rich.console import Console
from rich.logging import RichHandler
from audiobook_cli.audible import app as audible_app
import subprocess

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
    merge_file_glob: str = typer.Argument(
        ..., help="Glob which matches all files to merge."
    ),
):
    file_list = glob(merge_file_glob)
    command = [
        "ffmpeg",
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
        output,
    ]
    with open("files.txt", "w") as fh:
        for file in file_list:
            fh.write(f"file '{file}'\n")
    if not run:
        Console().print(f"Would execute: {' '.join(command)}")
    else:
        subprocess.run(command)


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
            "ffmpeg",
            "-i",
            audiobook,
            "-i",
            meta,
            "-map_metadata",
            "1",
            "-codec",
            "copy",
            output,
        ]
    )
