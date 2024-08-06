import json
import os
from datetime import datetime
from pathlib import Path
from typing import Optional

import typer
from rich import print
from rich.progress import track
from typing_extensions import Annotated

from lb.rag.db.chroma import (
    VALID_COLLECTION_NAMES,
    Speakers,
    add_transcripts_to_db,
    create_ids,
    list_collections,
    load_transcripts,
    retrieve_five_four,
)
from lb.scraping.fivefour import (
    retry_failed_transcripts,
    scrape_main_page,
    scrape_transcript_page,
)
from lb.utils.log import create_logger

log = create_logger(__name__)

if os.environ.get("LB_DIR", None) is not None:
    lb_dir = Path(os.environ["LB_DIR"]).expanduser()
else:
    homedir = Path.home().expanduser()
    lb_dir = homedir / ".lb"

if not lb_dir.exists():
    lb_dir.mkdir(parents=True)

db_loc = lb_dir / "chroma"


def _version_callback(value: bool) -> None:
    if value:
        from . import __version__ as version

        print(f"Lawyer Brain CLI [blue]v{version}[/blue]")
        raise typer.Exit()


cli = typer.Typer(
    help=(
        "[bold][dark_orange]Lawyer Brain (lb)[/dark_orange] is a CLI for scraping, "
        "vectorizing, and RAG-ing lawyer transcripts from the 5-4 podcast or from "
        "the supreme court.[/bold]"
    ),
    add_completion=False,
    no_args_is_help=True,
    context_settings={"help_option_names": ["-h", "--help"]},
    rich_markup_mode="rich",
)


scrape = typer.Typer(
    help="Scrape from different data sources.",
    add_completion=False,
    no_args_is_help=True,
    context_settings={"help_option_names": ["-h", "--help"]},
    rich_markup_mode="rich",
)


@cli.callback()
def common(
    ctx: typer.Context,
    version: bool = typer.Option(
        None,
        "--version",
        "-v",
        callback=_version_callback,
        help="Print the version and exit.",
    ),
) -> None:
    """A function for getting the app version

    This will call the version_callback function to print the version and exit.

    Arguments:
        ctx: The typer context
        version: A boolean flag for the version
    """
    pass


@scrape.command(
    "fivefour",
    help="Scrape the FiveFour podcast transcripts.",
    context_settings={"help_option_names": ["-h", "--help"]},
)
def fivefour(
    base_url: Annotated[
        str, typer.Option(help="Base URL of the podcast website.")
    ] = "https://fivefourpod.com",
    save_path: Annotated[
        str, typer.Option(help="Path to save the extracted transcript data.")
    ] = "data/transcripts.json",
) -> None:
    """Scrape the FiveFour podcast transcripts.

    Arguments:
        base_url: Base URL of the podcast website.
        save_path: Path to save the extracted transcript
    """
    save_path = Path(save_path)
    if save_path.exists():
        log.warning(f"{save_path} already exists. Running retry for failed transcripts.")
        retry_failed_transcripts(save_path)
    else:
        # Scrape the main page for episode data
        transcript_data = scrape_main_page(base_url)

        # Scrape each transcript page and store the transcript and description
        for entry in track(transcript_data, description="Scraping transcripts"):
            description, metaphor, transcript = scrape_transcript_page(
                entry["transcript_url"]
            )
            entry["description"] = description
            entry["metaphor"] = metaphor
            entry["transcript"] = transcript

        # Determine missing episodes by seeing if transcript is an empty list
        missing_episodes = [
            entry["title"] for entry in transcript_data if not entry["transcript"]
        ]

        # Put into overarching dictionary
        data = {
            "scrape_date": datetime.now().isoformat(),
            "episodes": transcript_data,
            "missing_episodes": missing_episodes,
        }

        # Log the number of episodes scraped
        print(
            f"Scraped {len(transcript_data) - len(missing_episodes)}/"
            f"{len(transcript_data)} episodes"
        )

        # Log the missing episodes
        if missing_episodes:
            log.warning("The following episodes are missing transcripts:")
            for episode in missing_episodes:
                log.warning(f"\t- {episode}")

        # Create the data directory if it doesn't exist
        save_path.parent.mkdir(parents=True, exist_ok=True)

        # Save the extracted data to a JSON file
        with open(save_path, "w") as file:
            json.dump(data, file, indent=2)

        log.info(f"Data saved to {save_path}")


db = typer.Typer(
    help="Database commands",
    add_completion=False,
    no_args_is_help=True,
    context_settings={"help_option_names": ["-h", "--help"]},
)


@db.command("init", help="Initialize a new database.")
def db_init(
    db_path: Annotated[
        str, typer.Option("--path", "-p", help="The path to the database folder.")
    ] = str(lb_dir / "chroma"),
) -> None:
    """Initialize a new database.

    Arguments:
        db_path: The path to the database foldre.
    """
    global db_loc
    db_loc = Path(db_path)
    if db_loc.exists():
        log.warning(f"Database folder {db_loc} already exists.")
        return

    db_loc.mkdir(parents=True, exist_ok=True)

    print(f"Database initialized at {db_loc}")


@db.command("add", help="Create a database collection from a JSON transcript file.")
def db_add(
    transcript_file: Annotated[
        str, typer.Argument(help="The path to the JSON transcript file.")
    ],
    db_path: Annotated[
        str, typer.Option("--path", "-p", help="The path to the database folder.")
    ] = str(lb_dir / "chroma"),
    collection_name: Annotated[
        str,
        typer.Option(
            "--collection-name",
            "-n",
            help="The name of the collection to create.",
        ),
    ] = "FiveFour",
    embedding_function: Annotated[
        str,
        typer.Option(
            "--embedding-function",
            "-e",
            help="The embedding function to use for the collection.",
        ),
    ] = "OpenAI",
    batch_size: Annotated[
        int,
        typer.Option(
            "--batch-size",
            "-b",
            help="The batch size to use for embedding.",
        ),
    ] = 4096,
    progress: Annotated[
        bool,
        typer.Option(
            "--progress",
            "-p",
            help="Show progress bar.",
        ),
    ] = False,
) -> None:
    """Create a database collection from a JSON transcript file.

    Arguments:
        transcript_file: The path to the JSON transcript file.
        db_path: The path to the database folder.
        url: The URL of the database if the database is running externally.
        collection_name: The name of the collection to create.
        embedding_function: The embedding function to use for the collection.
    """
    db_loc = Path(db_path)
    if not db_loc.exists():
        log.warning(f"Database folder {db_loc} does not exist. Creating new database.")

    transcript_file = Path(transcript_file)
    if not transcript_file.exists():
        message = f"Transcript file {transcript_file} does not exist."
        log.error(message)
        raise ValueError(message)

    transcript_file_data = load_transcripts(transcript_file)
    id_transcripts = create_ids(transcript_file_data)
    add_transcripts_to_db(
        id_transcripts,
        db_loc,
        collection_name,
        embedding_function,
        batch_size,
        progress,
    )


@db.command("search", help="Query the database.")
def db_search(
    query: Annotated[str, typer.Argument(help="The query string.")],
    collection: Annotated[
        str, typer.Option("--collection", "-c", help="The collection to query.")
    ] = "FiveFour",
    k: Annotated[
        int,
        typer.Option(
            "-k",
            help="The number of results to return through similarity search.",
        ),
    ] = 2,
    speaker: Annotated[
        Optional[Speakers],
        typer.Option("--speaker", "-s", help="The speaker to search for."),
    ] = None,
    context: Annotated[
        int,
        typer.Option("--context", "-C", help="The number of context lines to return."),
    ] = 2,
):
    collection = collection.lower()
    if collection not in VALID_COLLECTION_NAMES:
        log.error(f"Collection {collection} not found in database.")
        raise ValueError(f"Collection {collection} not found in database.")
    response = retrieve_five_four(db_loc, query, speaker, k, context)
    print(response)


@db.command("status", help="Print current database location.")
def db_status():
    print(f"\nChroma DB currently pointing to {db_loc}")


@db.command("ls", help="List all collections in the database.")
def db_ls():
    collections = list_collections(db_loc)
    print(f"\nFound {len(collections)} collections:")


@db.command("rm", help="Remove a collection from the database.")
def db_rm(
    collection_name: Annotated[
        str, typer.Argument(help="The name of the collection to remove.")
    ]
):
    pass


cli.add_typer(db, name="db")
cli.add_typer(scrape, name="scrape")

if __name__ == "__main__":
    cli()
