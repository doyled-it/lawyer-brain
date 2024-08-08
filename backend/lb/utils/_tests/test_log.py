import logging
import os
from io import StringIO

import pytest

from lb.utils.log import LogFilter, LoggerWriter, create_logger


@pytest.fixture
def clean_env():
    original_env = dict(os.environ)
    yield
    os.environ.clear()
    os.environ.update(original_env)


def test_logger_creation(clean_env):
    os.environ["LOGLEVEL"] = "DEBUG"
    logger = create_logger("test_logger")

    assert logger.name == "test_logger"
    assert logger.level == logging.DEBUG

    log_stream = StringIO()
    handler = logging.StreamHandler(log_stream)
    handler.addFilter(LogFilter())
    logger.addHandler(handler)

    logger.debug("This is a debug message")
    log_contents = log_stream.getvalue().strip()
    assert "This is a debug message" in log_contents
    assert LogFilter().__repr__() == "LogFilter"


def test_log_filter():
    log_filter = LogFilter()

    record = logging.LogRecord(
        "name", logging.INFO, "path", 0, "message without", None, None
    )
    assert log_filter.filter(record)

    record = logging.LogRecord(
        "name", logging.INFO, "path", 0, "message with dealloc", None, None
    )
    assert not log_filter.filter(record)


def test_logger_writer():
    logger = logging.getLogger("test_logger_writer")
    logger.setLevel(logging.INFO)
    log_stream = StringIO()
    handler = logging.StreamHandler(log_stream)
    logger.addHandler(handler)

    writer = LoggerWriter(logger, logging.INFO)
    writer.write("This is a test message")

    log_contents = log_stream.getvalue().strip()
    assert "This is a test message" in log_contents


def test_logger_writer_ignores_newline():
    logger = logging.getLogger("test_logger_writer_newline")
    logger.setLevel(logging.INFO)
    log_stream = StringIO()
    handler = logging.StreamHandler(log_stream)
    logger.addHandler(handler)

    writer = LoggerWriter(logger, logging.INFO)
    writer.write("\n")

    log_contents = log_stream.getvalue().strip()
    assert log_contents == ""


def test_logger_writer_flush_and_close():
    logger = logging.getLogger("test_logger_writer_flush_close")
    writer = LoggerWriter(logger, logging.INFO)

    writer.flush()
    writer.close()

    # These methods do not have any functional implementation, but we call them to ensure
    # they do not raise exceptions.
    assert True  # If no exceptions are raised, the test passes
