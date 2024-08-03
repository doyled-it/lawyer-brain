import json
from datetime import datetime
from pathlib import Path

from rich.progress import track

from ..lb.scraping.fivefour import (
    retry_failed_transcripts,
    scrape_main_page,
    scrape_transcript_page,
)
from ..lb.utils.log import create_logger

log = create_logger(__name__)

# Path to save the extracted data
SAVE_PATH = Path("data/transcripts.json")

# Base URL of the website
base_url = "https://fivefourpod.com"


def main():
    if SAVE_PATH.exists():
        log.info(f"{SAVE_PATH} already exists. Running retry for failed transcripts.")
        retry_failed_transcripts(SAVE_PATH)
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
        SAVE_PATH.parent.mkdir(parents=True, exist_ok=True)

        # Save the extracted data to a JSON file
        with open(SAVE_PATH, "w") as file:
            json.dump(data, file, indent=2)

        log.info(f"Data saved to {SAVE_PATH}")


if __name__ == "__main__":
    main()
