import json
import re
from pathlib import Path

import requests
from bs4 import BeautifulSoup
from rich.progress import track

from lb.utils.log import create_logger

log = create_logger(__name__)


# Function to scrape the transcript page
def scrape_transcript_page(url: str) -> tuple[str, str, list[dict[str, str]]]:
    """Scrape the transcript page for the description, metaphor, and transcript.

    Arguments:
        url: URL of the webpage to scrape.

    Returns:
        Tuple containing the description, metaphor, and transcript data.
    """
    response = requests.get(url)
    response.raise_for_status()
    page_soup = BeautifulSoup(response.text, "html.parser")

    # Extract the description
    description = ""
    description_container = page_soup.find(
        "header", class_="masthead bg-primary text-white text-center"
    )
    if description_container:
        description_p = description_container.find("p")
        if description_p:
            description = description_p.get_text(strip=True)

    # Extract the metaphor
    metaphor = ""
    metaphor_container = page_soup.find(
        "header", class_="masthead bg-primary text-white text-center"
    )
    if metaphor_container:
        metaphor_em = metaphor_container.find("em")
        if metaphor_em:
            metaphor = metaphor_em.get_text(strip=True)

    # Extract the transcript
    transcript = []
    transcript_container = page_soup.find("div", class_="col-md-12 col-lg-12 mb-5")
    if transcript_container:
        paragraphs = transcript_container.find_all("p")
        for p in paragraphs:
            text = p.get_text(strip=True)
            if text:  # Ensure text is not empty
                # Split the text at each timestamp
                segments = re.split(
                    r"(?=\d{1,2}:\d{2}(?::\d{2})?(?:\.\d{1,2})?\s*[^:]*:)", text
                )
                for segment in segments:
                    match = re.match(
                        r"^(\d{1,2}:\d{2}(?::\d{2})?(?:\.\d{1,2})?)\s*([^:]+):\s*(.*)$",
                        segment,
                    )
                    if match:
                        timestamp, speaker, speech_text = match.groups()
                        transcript.append(
                            {
                                "timestamp": timestamp,
                                "speaker": speaker,
                                "text": speech_text,
                            }
                        )

    # Filter out entries that don't have a valid timestamp
    transcript = [
        entry
        for entry in transcript
        if re.match(r"\d{1,2}:\d{2}(?::\d{2})?(?:\.\d{1,2})?", entry["timestamp"])
    ]

    return description, metaphor, transcript


def retry_failed_transcripts(save_path: str = "data/transcripts.json") -> None:
    """Retry scraping for missing transcripts.

    Arguments:
        save_path: Path to the JSON file containing the scraped data.
    """
    save_path = Path(save_path)
    # Load the previously saved data
    if save_path.exists():
        try:
            with open(save_path, "r") as file:
                data = json.load(file)
        except json.JSONDecodeError:
            log.error(f"Failed to load data from {save_path}.")
            save_path.unlink()  # Delete the file
            return
    else:
        log.error(f"{save_path} does not exist. Run the main script first.")
        return

    # Retry scraping for missing episodes
    missing_episodes = data.get("missing_episodes", [])
    if not missing_episodes:
        log.info("No missing episodes to retry.")
        return

    for entry in track(data["episodes"], description="Retrying missing transcripts"):
        if entry["title"] in missing_episodes:
            description, metaphor, transcript = scrape_transcript_page(
                entry["transcript_url"]
            )
            entry["description"] = description
            entry["metaphor"] = metaphor
            entry["transcript"] = transcript

    # Update missing episodes
    missing_episodes = [
        entry["title"] for entry in data["episodes"] if not entry["transcript"]
    ]
    data["missing_episodes"] = missing_episodes

    # Log the number of episodes scraped
    log.info(
        f"Scraped {len(data['episodes']) - len(missing_episodes)}/"
        f"{len(data['episodes'])} episodes"
    )

    # Log the missing episodes
    if missing_episodes:
        log.warning("The following episodes are missing transcripts:")
        for episode in missing_episodes:
            log.warning(f"\t- {episode}")

    # Save the updated data to the JSON file
    with open(save_path, "w") as file:
        json.dump(data, file, indent=2)

    log.info(f"Updated data saved to {save_path}")


def scrape_main_page(url: str = "https://fivefourpod.com") -> list[dict[str, str]]:
    """Scrape the main page for episode data.

    Arguments:
        url: URL of the webpage to scrape. Is built for https://fivefourpod.com.

    Returns:
        List of dictionaries containing the episode title and transcript URL.
    """
    response = requests.get(url)
    response.raise_for_status()  # Check that the request was successful

    # Parse the HTML content
    soup = BeautifulSoup(response.text, "html.parser")

    # Find all the episode containers
    episode_containers = soup.find_all("div", class_="content")

    # List to hold the extracted data
    transcript_data = []

    # Loop through each episode container and extract the title and transcript URL
    for container in episode_containers:
        title = None
        title_div = container.find_previous_sibling("div", class_="collapsible")
        if title_div:
            # Remove the number at the end using regex
            title = re.sub(r"\d+$", "", title_div.text.strip()).strip()

        transcript_btn = container.find("a", class_="transcript-btn")
        if transcript_btn and title:
            transcript_url = transcript_btn["href"]
            if not transcript_url.startswith("http"):
                transcript_url = f"{url.rstrip('/')}/{transcript_url.lstrip('/')}"
            transcript_data.append({"title": title, "transcript_url": transcript_url})

    return transcript_data
