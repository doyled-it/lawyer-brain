import json
from datetime import datetime
from pathlib import Path

import typer
from rich.progress import track
from typing_extensions import Annotated

from lb.scraping.fivefour import (
    retry_failed_transcripts,
    scrape_main_page,
    scrape_transcript_page,
)
from lb.utils.log import create_logger

log = create_logger(__name__)

scrape = typer.Typer(
    help="Scrape from different data sources.",
    add_completion=False,
    no_args_is_help=True,
    context_settings={"help_option_names": ["-h", "--help"]},
)


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
        log.info(f"{save_path} already exists. Running retry for failed transcripts.")
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
        log.info(
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
