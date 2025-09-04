import pytest
from app.models.send_result_schema import SendResult

def test_md5_none_passthrough():
    """Covers 'if v is None: return v'."""
    s = SendResult(queue_url="http://localhost/queue", provider_message_id="abc")
    assert s.md5_of_body is None

@pytest.mark.parametrize("good_md5", [
    "d41d8cd98f00b204e9800998ecf8427e",  # lowercase valid
    "D41D8CD98F00B204E9800998ECF8427E",  # uppercase valid
    "0f343b0931126a20f133d67c2b018a3b",  # another valid
])
def test_md5_valid_hex_accepted(good_md5):
    """Covers the 'fullmatch OK' branch (skip the if; final return v)."""
    s = SendResult(
        queue_url="https://example.com/q",
        provider_message_id="id-123",
        md5_of_body=good_md5,
    )
    assert s.md5_of_body == good_md5  # reached final 'return v'

@pytest.mark.parametrize("bad_md5", [
    "", "   ",                              # empty / spaces
    "d41d8cd98f00b204e9800998ecf8427",      # 31 chars
    "d41d8cd98f00b204e9800998ecf8427ee",    # 33 chars
    "Z41d8cd98f00b204e9800998ecf8427e",     # non-hex
    "g41d8cd98f00b204e9800998ecf8427e",     # non-hex
    "d41d8cd98f00b204e9800998ecf8427G",     # non-hex
])
def test_md5_invalid_rejected(bad_md5):
    """Covers the 'fullmatch fails' branch (enter if; raise)."""
    with pytest.raises(ValueError):
        SendResult(
            queue_url="http://localhost/queue",
            provider_message_id="abc",
            md5_of_body=bad_md5,
        )
