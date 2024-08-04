from os.path import exists as p_exists

import audible
import typer
from rich.console import Console
from typer import Typer

from audiobook_cli.utils import audible_auth_file, get_audible_auth_from_file

app = Typer(name="audible", help="Audible related subcommands.")


@app.callback()
def audible_callback(
    ctx: typer.Context,
    locale: str = typer.Option("us", "--locale", "-l", help="Audible locale to use"),
    encryption: str = typer.Option(
        None, "--encryption", "-e", help="Encryption password for Audible credentials."
    ),
):
    p = audible_auth_file()
    auth = None
    if p_exists(p):
        auth = get_audible_auth_from_file(locale=locale, password=encryption)

    ctx.obj = {"locale": locale, "auth": auth, "encryption": encryption}


@app.command(name="login", help="Audible login")
def audible_login(
    ctx: typer.Context,
    use_browser: bool = typer.Option(False, "--use-browser"),
    username: str = typer.Option(
        None, "--username", "-u", help="Username (usually your email) to use."
    ),
    password: str = typer.Option(None, "--password", "-p", help="Password to use."),
    otp: str = typer.Option(None, "--otp", "-o", help="OTP to use."),
    with_username: bool = typer.Option(
        False, "--with-username", help="Use very old Audible username login."
    ),
) -> None:
    config = ctx.obj
    if use_browser:
        auth = audible.Authenticator.from_login_external(locale=config["locale"])
    else:
        if not username or not password:
            raise ValueError("Username and password must be given.")
        auth = audible.Authenticator.from_login(
            username=username,
            password=password + otp if otp else password,
            with_username=with_username,
            locale=config["locale"],
        )
    encryption = config["encryption"]
    auth.to_file(
        audible_auth_file(),
        password=encryption,
        encryption="bytes" if encryption else "default",
    )


@app.command(name="dump", help="Dump audible data.")
def audible_dump(
    ctx: typer.Context,
    raw: bool = typer.Option(False, "--raw", "-r", help="Dump raw data."),
):
    config = ctx.obj
    if raw:
        with open(audible_auth_file(), "rb") as data:
            Console().print(data.read())
    auth = get_audible_auth_from_file(
        locale=config["locale"], password=config["encryption"]
    )
    d = auth.to_dict()
    Console().print(d)


@app.command(name="chapters", help="Receive chapters for a book.")
def audible_chapters(
    ctx: typer.Context,
    asin: str = typer.Argument(..., help="Audible book ASIN."),
    raw: bool = typer.Option(False, "--raw", "-r", help="Raw output."),
):
    Console(stderr=True).print(
        "This command is deprecated - please use the metadata command."
    )
    config = ctx.obj
    auth = get_audible_auth_from_file(
        locale=config["locale"], password=config["encryption"]
    )
    with audible.Client(auth=auth) as client:
        data = client.get(
            f"1.0/content/{asin}/metadata",
            response_groups="chapter_info",
            chapter_titles_type="Flat",
        )
    if raw:
        Console().print(data)
    else:
        c = Console()
        for chapter in data["content_metadata"]["chapter_info"]["chapters"]:
            begin = chapter["start_offset_ms"]
            end = begin + chapter["length_ms"]
            title = chapter["title"]
            c.print("[CHAPTER]")
            c.print("TIMEBASE=1/1000")
            c.print(f"START={begin}")
            c.print(f"END={end}")
            c.print(f"title={title}\n")


@app.command(name="metadata", help="Fetch metadata for books.")
def metadata(
    ctx: typer.Context,
    raw: bool = typer.Option(False, "--raw", "-r", help="Raw data output."),
    output: str = typer.Option(None, "--output", "-o", help="Optional output file."),
    skip_chapters: bool = typer.Option(
        False,
        "--skip-chapters",
        "-s",
        help="Skip pulling chapter metadata from Audible.",
    ),
    chapter_offset: int = typer.Option(
        None,
        "--chapter-offset",
        "-c",
        help='Chapter offset in milliseconds to skip a given intro that differs from the usual audible chapter data. This adds an "Intro" chapter to the beginning of the book.',
    ),
    chapter_intro_name: str = typer.Option(
        "Intro",
        "--chapter-intro-name",
        "-C",
        help='Customized name, if not given, "Intro" will be used.',
    ),
    asin: str = typer.Argument(..., help="ASIN of the book to fetch metadata for."),
):
    config = ctx.obj
    auth = get_audible_auth_from_file(
        locale=config["locale"], password=config["encryption"]
    )
    with audible.Client(auth=auth) as client:
        data = client.get(
            f"1.0/catalog/products/{asin}",
            response_groups="product_attrs, product_desc, product_details, product_extended_attrs, product_plan_details, product_plans, series, contributors",
        )
        if not skip_chapters or chapter_offset:
            data_chapters = client.get(
                f"1.0/content/{asin}/metadata",
                response_groups="chapter_info",
                chapter_titles_type="Flat",
            )

    c = Console()
    if raw:
        c.print_json(data=data)
    else:
        metadata = ""
        prod = data["product"]
        title = prod["title"]
        artist = ", ".join(author["name"] for author in prod["authors"])
        composer = ", ".join(n["name"] for n in prod["narrators"])
        series = prod["series"][0]["title"]
        part = prod["series"][0]["sequence"]
        subtitle = series + " " + part
        album = title + ": " + subtitle
        comment = prod["publisher_summary"]
        copy = prod["copyright"]
        publisher = prod["publisher_name"]
        language = prod["language"].capitalize()
        metadata += ";FFMETADATA1\n"
        metadata += "major_brand=isom\n"
        metadata += "minor_version=512\n"
        metadata += f"title={title}\n"
        metadata += f"artist={artist}\n"
        metadata += f"album_artist={artist}\n"
        metadata += f"album={album}\n"
        metadata += f"comment={comment}\n"
        metadata += f"copyright={copy}\n"
        metadata += f"data={prod['release_date']}\n"
        metadata += f"composer={composer}\n"
        metadata += f"SUBTITLE={subtitle}\n"
        metadata += f"PUBLISHER={publisher}\n"
        metadata += f"LANGUAGE={language}\n"
        metadata += f"AUDIBLE_ASIN={asin}\n"
        metadata += f"asin={asin}\n"
        metadata += f"SERIES={series}\n"
        metadata += f"PART={part}\n\n"
        if not skip_chapters or chapter_offset:
            if chapter_offset:
                metadata += "[CHAPTER]\n"
                metadata += "TIMEBASE=1/1000\n"
                metadata += "START=0\n"
                metadata += f"END={chapter_offset}\n"
                metadata += f"title={chapter_intro_name}\n\n"
            for chapter in data_chapters["content_metadata"]["chapter_info"][
                "chapters"
            ]:
                begin = chapter["start_offset_ms"]
                end = begin + chapter["length_ms"]
                if chapter_offset:
                    begin += chapter_offset
                    end += chapter_offset
                title = chapter["title"]
                metadata += "[CHAPTER]\n"
                metadata += "TIMEBASE=1/1000\n"
                metadata += f"START={begin}\n"
                metadata += f"END={end}\n"
                metadata += f"title={title}\n\n"
        if output:
            with open(output, "w") as fh:
                fh.write(metadata)
        else:
            c.print(metadata)
