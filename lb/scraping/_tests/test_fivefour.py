import json
from pathlib import Path

import pytest
import requests_mock

from lb.scraping.fivefour import (
    retry_failed_transcripts,
    scrape_main_page,
    scrape_transcript_page,
)
from lb.utils.log import create_logger

log = create_logger(__name__)

# Sample HTML content for mocking
sample_transcript_html = """
<header class="masthead bg-primary text-white text-center">
    <p>This is a sample description</p>
    <em>This is a sample metaphor</em>
</header>
<div class="col-md-12 col-lg-12 mb-5">
    <p>00:01:23 Speaker 1: This is a sample transcript entry.</p>
    <p>00:02:34 Speaker 2: This is another sample transcript entry.</p>
</div>
"""

sample_main_page_html = Path("lb/scraping/_tests/test.html").read_text()


@pytest.fixture
def requests_mock_fixture():
    with requests_mock.Mocker() as m:
        yield m


def test_scrape_transcript_page(requests_mock_fixture):
    url = "http://example.com/ep1"
    requests_mock_fixture.get(url, text=sample_transcript_html)

    description, metaphor, transcript = scrape_transcript_page(url)

    assert description == "This is a sample description"
    assert metaphor == "This is a sample metaphor"
    assert len(transcript) == 2
    assert transcript[0]["timestamp"] == "1:23"
    assert transcript[0]["speaker"] == "Speaker 1"
    assert transcript[0]["text"] == "This is a sample transcript entry."
    assert transcript[1]["timestamp"] == "2:34"
    assert transcript[1]["speaker"] == "Speaker 2"
    assert transcript[1]["text"] == "This is another sample transcript entry."


def test_retry_failed_transcripts(tmp_path, requests_mock_fixture):
    save_path = tmp_path / "transcripts.json"
    data = {
        "episodes": [
            {
                "title": "Episode 1",
                "transcript_url": "http://example.com/ep1",
                "transcript": [],
            },
            {
                "title": "Episode 2",
                "transcript_url": "http://example.com/ep2",
                "transcript": ["Some transcript"],
            },
        ],
        "missing_episodes": ["Episode 1"],
    }
    with open(save_path, "w") as file:
        json.dump(data, file)

    requests_mock_fixture.get("http://example.com/ep1", text=sample_transcript_html)

    retry_failed_transcripts(str(save_path))

    with open(save_path, "r") as file:
        updated_data = json.load(file)

    assert len(updated_data["episodes"]) == 2
    assert len(updated_data["episodes"][0]["transcript"]) == 2
    assert updated_data["missing_episodes"] == []


def test_scrape_main_page(requests_mock_fixture):
    url = "http://example.com"
    requests_mock_fixture.get(url, text=sample_main_page_html)

    transcript_data = scrape_main_page(url)

    assert len(transcript_data) == 7
    assert transcript_data[0]["title"] == "Garland v. Cargill"
    assert (
        transcript_data[0]["transcript_url"]
        == "http://example.com/episodes/garland-v-cargill/"
    )
    assert transcript_data[1]["title"] == "Alexander v. South Carolina NAACP"
    assert (
        transcript_data[1]["transcript_url"]
        == "http://example.com/episodes/alexander-v-south-carolina-naacp/"
    )
    assert transcript_data[2]["title"] == "Arizona v. Navajo Nation"
    assert (
        transcript_data[2]["transcript_url"]
        == "http://example.com/episodes/arizona-v-navajo-nation/"
    )
    assert transcript_data[3]["title"] == "Maryland v. King"
    assert (
        transcript_data[3]["transcript_url"]
        == "http://example.com/episodes/maryland-v-king/"
    )
    assert (
        transcript_data[4]["title"]
        == "Free Rhiannon! Campus Protests and the First Amendment"
    )
    assert transcript_data[4]["transcript_url"] == (
        "http://example.com/episodes/free-rhiannon!-campus-protests-and-the-first-"
        "amendment/"
    )
    assert transcript_data[5]["title"] == "Hans v. Louisiana"
    assert (
        transcript_data[5]["transcript_url"]
        == "http://example.com/episodes/hans-v-louisiana/"
    )
    assert transcript_data[6]["title"] == "Holder v. Humanitarian Law Project"
    assert (
        transcript_data[6]["transcript_url"]
        == "http://example.com/episodes/holder-v-humanitarian-law-project/"
    )
