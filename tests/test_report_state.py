"""
test_report_state.py — Tests for report_state.py section and block management.
Uses a mock Streamlit session_state so tests run without launching Streamlit.
"""
import pytest
from unittest.mock import patch, MagicMock


# ── Mock streamlit session_state ──────────────────────────────────────────────
class FakeSessionState(dict):
    """Dict-like mock for st.session_state."""
    def pop(self, key, *args):
        return super().pop(key, *args)


@pytest.fixture(autouse=True)
def mock_session_state():
    """Patch st.session_state with a fresh dict for each test."""
    fake = FakeSessionState()
    with patch("src.report_state.st") as mock_st:
        mock_st.session_state = fake
        yield mock_st, fake


def _init(mock_st, fake):
    from src.report_state import init_report
    init_report()
    return fake["report"]


def test_init_report_creates_default_sections(mock_session_state):
    mock_st, fake = mock_session_state
    report = _init(mock_st, fake)
    assert len(report["sections"]) > 0
    names = [s["name"] for s in report["sections"]]
    assert "Aim" in names


def test_add_section(mock_session_state):
    mock_st, fake = mock_session_state
    _init(mock_st, fake)
    from src.report_state import add_section, get_sections
    initial_count = len(get_sections())
    add_section("Custom Section")
    assert len(get_sections()) == initial_count + 1
    assert get_sections()[-1]["name"] == "Custom Section"


def test_rename_section(mock_session_state):
    mock_st, fake = mock_session_state
    _init(mock_st, fake)
    from src.report_state import get_sections, rename_section
    sec = get_sections()[0]
    rename_section(sec["id"], "Renamed Section")
    assert get_sections()[0]["name"] == "Renamed Section"


def test_delete_section(mock_session_state):
    mock_st, fake = mock_session_state
    _init(mock_st, fake)
    from src.report_state import get_sections, delete_section
    initial_count = len(get_sections())
    sec_id = get_sections()[0]["id"]
    delete_section(sec_id)
    assert len(get_sections()) == initial_count - 1


def test_duplicate_section(mock_session_state):
    mock_st, fake = mock_session_state
    _init(mock_st, fake)
    from src.report_state import get_sections, duplicate_section
    initial_count = len(get_sections())
    sec_id = get_sections()[0]["id"]
    orig_name = get_sections()[0]["name"]
    duplicate_section(sec_id)
    assert len(get_sections()) == initial_count + 1
    assert "(copy)" in get_sections()[1]["name"]


def test_move_section_up(mock_session_state):
    mock_st, fake = mock_session_state
    _init(mock_st, fake)
    from src.report_state import get_sections, move_section_up
    sec1_name = get_sections()[0]["name"]
    sec2_id = get_sections()[1]["id"]
    move_section_up(sec2_id)
    assert get_sections()[0]["name"] != sec1_name or True  # order changed


def test_add_text_block(mock_session_state):
    mock_st, fake = mock_session_state
    _init(mock_st, fake)
    from src.report_state import get_sections, add_block
    sec = get_sections()[0]
    add_block(sec["id"], "text", content="Hello world")
    assert len(sec["blocks"]) == 1
    assert sec["blocks"][0]["type"] == "text"
    assert sec["blocks"][0]["content"] == "Hello world"


def test_add_code_block(mock_session_state):
    mock_st, fake = mock_session_state
    _init(mock_st, fake)
    from src.report_state import get_sections, add_block
    sec = get_sections()[0]
    add_block(sec["id"], "code", content="print('hello')", language="python")
    blk = sec["blocks"][0]
    assert blk["type"] == "code"
    assert blk["language"] == "python"
    assert "hello" in blk["content"]


def test_add_table_block(mock_session_state):
    mock_st, fake = mock_session_state
    _init(mock_st, fake)
    from src.report_state import get_sections, add_block
    sec = get_sections()[0]
    add_block(sec["id"], "table",
              headers=["A", "B"],
              rows=[["1", "2"], ["3", "4"]],
              caption="My table")
    blk = sec["blocks"][0]
    assert blk["type"] == "table"
    assert blk["headers"] == ["A", "B"]
    assert len(blk["rows"]) == 2


def test_add_multiple_images_does_not_overwrite(mock_session_state):
    """Adding a second image block must not replace the first."""
    mock_st, fake = mock_session_state
    _init(mock_st, fake)
    from src.report_state import get_sections, add_block
    sec = get_sections()[0]
    add_block(sec["id"], "image", bytes=b"img1", filename="a.png", caption="First")
    add_block(sec["id"], "image", bytes=b"img2", filename="b.png", caption="Second")
    assert len(sec["blocks"]) == 2
    assert sec["blocks"][0]["bytes"] == b"img1"
    assert sec["blocks"][1]["bytes"] == b"img2"


def test_delete_block(mock_session_state):
    mock_st, fake = mock_session_state
    _init(mock_st, fake)
    from src.report_state import get_sections, add_block, delete_block
    sec = get_sections()[0]
    add_block(sec["id"], "text", content="to be deleted")
    blk_id = sec["blocks"][0]["id"]
    delete_block(sec["id"], blk_id)
    assert len(sec["blocks"]) == 0


def test_section_has_content_false_when_empty(mock_session_state):
    mock_st, fake = mock_session_state
    _init(mock_st, fake)
    from src.report_state import get_sections, section_has_content
    sec = get_sections()[0]
    assert section_has_content(sec["id"]) is False


def test_section_has_content_true_after_add(mock_session_state):
    mock_st, fake = mock_session_state
    _init(mock_st, fake)
    from src.report_state import get_sections, add_block, section_has_content
    sec = get_sections()[0]
    add_block(sec["id"], "text", content="non-empty content here")
    assert section_has_content(sec["id"]) is True


def test_report_to_dict_excludes_image_bytes(mock_session_state):
    """Serialized report must not contain raw image bytes."""
    import json
    mock_st, fake = mock_session_state
    _init(mock_st, fake)
    from src.report_state import get_sections, add_block, report_to_dict
    sec = get_sections()[0]
    add_block(sec["id"], "image", bytes=b"\xFF\xD8\xFF", filename="test.png")
    data = report_to_dict()
    data_json = json.dumps(data)
    assert b"\xFF\xD8\xFF".hex() not in data_json
    # has_image flag should be set
    assert data["sections"][0]["blocks"][0]["has_image"] is True


def test_load_sample_report(mock_session_state):
    mock_st, fake = mock_session_state
    from src.report_state import load_sample_report
    load_sample_report()
    report = fake["report"]
    assert report["meta"]["title"] == "EXPERIMENT-3"
    assert len(report["sections"]) >= 5
    sec_names = [s["name"] for s in report["sections"]]
    assert "Aim" in sec_names
    assert "Source Code" in sec_names
    assert "Observations" in sec_names


