import logging
import subprocess
from glob import glob
from os import rename
import typer
from rich.console import Console
from rich.logging import RichHandler
from typer import Typer

from audiobook_cli.audible import app as audible_app
from audiobook_cli.utils import ffmpeg, ffprobe

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
            "-codec",
            "copy",
            output,
        ]
    )
