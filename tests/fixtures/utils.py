import pytest

from rtspbrute.modules import utils


@pytest.fixture
def result_file(tmp_path):
    """Creates `utils.RESULT_FILE` in `tmp_path` and returns it."""
    utils.RESULT_FILE = tmp_path / "result.txt"
    utils.RESULT_FILE.open("w", encoding="utf-8")
    return utils.RESULT_FILE


@pytest.fixture
def html_file(tmp_path):
    """Creates `utils.HTML_FILE` in `tmp_path` and returns it."""
    utils.HTML_FILE = tmp_path / "index.html"
    utils.HTML_FILE.open("w", encoding="utf-8")
    return utils.HTML_FILE
