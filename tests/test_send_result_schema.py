import pytest
from pydantic import ValidationError
from app.models.send_result_schema import SendResult

@pytest.mark.parametrize("url", [
    "http://localhost:4566/000000000000/device-messages",
    "http://localstack:4566/000000000000/device-messages",
    "https://example.com/q",
    "http://127.0.0.1:4566/device-messages",
])
def test_send_result_accepts_various_valid_urls(url):
    s = SendResult(queue_url=url, provider_message_id="abc-123")
    u = s.queue_url
    assert u.scheme in {"http", "https"}

    assert u.host                          # are host
    assert isinstance(u.port, (int, type(None)))
    assert str(u).endswith(u.path)         # final string is consistent

def test_send_result_fields_and_md5():
    s = SendResult(
        queue_url="http://local/queue",
        provider_message_id="abc-123",
        md5_of_body="d41d8cd98f00b204e9800998ecf8427e",
    )
    assert s.provider_message_id == "abc-123"
    assert s.md5_of_body == "d41d8cd98f00b204e9800998ecf8427e"

def test_send_result_rejects_bad_md5():
    with pytest.raises(ValueError):
        SendResult(queue_url="http://local/queue", provider_message_id="x", md5_of_body="zzz")

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

def test_extra_fields_forbidden():
    """Make extra='forbid' funcționează."""
    with pytest.raises(ValidationError):
        SendResult(
            queue_url="http://localhost/queue",
            provider_message_id="abc",
            extra_field="nope",
        )
