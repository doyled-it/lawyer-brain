import json
from datetime import datetime
from pathlib import Path
from unittest.mock import patch

import pytest
from typer.testing import CliRunner

from lb.cli import scrape

runner = CliRunner()


@pytest.fixture
def mock_datetime_now():
    with patch("lb.cli.datetime") as mock_datetime:
        mock_datetime.now.return_value = datetime(2023, 1, 1)
        yield mock_datetime


@pytest.fixture
def mock_scrape_functions():
    with (
        patch("lb.cli.scrape_main_page") as mock_scrape_main_page,
        patch("lb.cli.scrape_transcript_page") as mock_scrape_transcript_page,
        patch("lb.cli.retry_failed_transcripts") as mock_retry_failed_transcripts,
    ):
        yield (
            mock_scrape_main_page,
            mock_scrape_transcript_page,
            mock_retry_failed_transcripts,
        )


@pytest.fixture
def mock_path_exists():
    with patch.object(Path, "exists") as mock_exists:
        yield mock_exists


@pytest.fixture
def mock_path_mkdir():
    with patch.object(Path, "mkdir") as mock_mkdir:
        yield mock_mkdir


def test_fivefour_new_file(
    mock_scrape_functions, mock_path_exists, mock_path_mkdir, mock_datetime_now
):
    mock_scrape_main_page, mock_scrape_transcript_page, _ = mock_scrape_functions
    mock_path_exists.return_value = False

    transcript_data = [
        {"title": "Episode 1", "transcript_url": "http://example.com/ep1"},
        {"title": "Episode 2", "transcript_url": "http://example.com/ep2"},
    ]
    mock_scrape_main_page.return_value = transcript_data
    mock_scrape_transcript_page.side_effect = [
        (
            "Description 1",
            "Metaphor 1",
            [{"timestamp": "00:01", "speaker": "Speaker 1", "text": "Text 1"}],
        ),
        ("Description 2", "Metaphor 2", []),
    ]

    result = runner.invoke(
        scrape,
        [
            "--base-url",
            "http://example.com",
            "--save-path",
            "test_data/transcripts.json",
        ],
    )

    assert result.exit_code == 0
    data = json.loads(Path("test_data/transcripts.json").read_text())
    assert len(data["episodes"]) == 2
    assert len(data["missing_episodes"]) == 1


def test_fivefour_existing_file(mock_scrape_functions, mock_path_exists, mock_path_mkdir):
    _, _, mock_retry_failed_transcripts = mock_scrape_functions
    mock_path_exists.return_value = True

    result = runner.invoke(
        scrape,
        [
            "--base-url",
            "http://example.com",
            "--save-path",
            "test_data/transcripts.json",
        ],
    )

    assert result.exit_code == 0
    mock_retry_failed_transcripts.assert_called_once_with(
        Path("test_data/transcripts.json")
    )
