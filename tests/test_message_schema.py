import xml.etree.ElementTree as ET
from datetime import datetime, timezone

import pytest
from pydantic import ValidationError

from app.models.message_schema import MessageCreate


def _localname(tag: str) -> str:
    """Return the local (namespace-stripped) part of a Clark-notation tag."""
    return tag.split("}", 1)[1] if tag.startswith("{") else tag


def test_message_create_valid_with_xml(xml_template: str):
    """
    Given a filled XML payload with a default namespace,
    ensure MessageCreate accepts it and that expected fields are present.
    """
    m = MessageCreate(device_id=1, client_id=2, payload=xml_template)
    assert m.device_id == 1
    assert m.client_id == 2
    assert isinstance(m.payload, str)

    root = ET.fromstring(m.payload)
    assert _localname(root.tag) == "Message"

    # No .find(): iterate and match by localname
    sensor_elements = [el for el in root.iter() if _localname(el.tag) == "Sensor"]
    assert sensor_elements, "Sensor element not found in XML"
    assert sensor_elements[0].text == "temp"


@pytest.mark.parametrize("bad_device_id", [0, -1])
def test_invalid_device_id_rejected(bad_device_id):
    with pytest.raises(ValidationError):
        MessageCreate(device_id=bad_device_id, client_id=1, payload="<Message/>")


@pytest.mark.parametrize("bad_client_id", [0, -5])
def test_invalid_client_id_rejected(bad_client_id):
    with pytest.raises(ValidationError):
        MessageCreate(device_id=1, client_id=bad_client_id, payload="<Message/>")


def test_payload_mapping_rejected():
    """Non-string payload (e.g., dict) should be rejected."""
    with pytest.raises(ValidationError):
        MessageCreate(device_id=1, client_id=1, payload={"not": "xml"})


def test_forbid_extra_fields():
    with pytest.raises(ValidationError):
        MessageCreate(
            device_id=1,
            client_id=1,
            payload="<Message/>",
            extra_field="oops",
        )


def test_timestamp_naive_converted_to_utc():
    naive = datetime(2025, 1, 1, 12, 0, 0)  # no tzinfo
    m = MessageCreate(device_id=1, client_id=1, payload="<Message/>", timestamp=naive)
    assert m.timestamp.tzinfo is not None


def test_payload_empty_string_rejected():
    with pytest.raises(ValueError):
        MessageCreate(device_id=1, client_id=1, payload="")


def test_payload_non_string_rejected():
    with pytest.raises(ValueError):
        MessageCreate(device_id=1, client_id=1, payload=123)  # not a str


def test_payload_invalid_xml_raises():
    bad_xml = "<Message><Sensor></Message>"  # broken XML
    with pytest.raises(ValueError):
        MessageCreate(device_id=1, client_id=1, payload=bad_xml)


def test_timestamp_aware_is_kept_as_is():
    """If timestamp already has tzinfo, validator should return it unchanged (covers return v)."""
    aware = datetime(2025, 1, 1, 12, 0, 0, tzinfo=timezone.utc)
    m = MessageCreate(device_id=1, client_id=1, payload="<Message/>", timestamp=aware)
    # same instant, tzinfo preserved
    assert m.timestamp == aware
    assert m.timestamp.tzinfo is timezone.utc


def test_timestamp_explicit_none_passes_through():
    """If timestamp is explicitly None, validator returns None (also covers return v)."""
    m = MessageCreate(device_id=1, client_id=1, payload="<Message/>", timestamp=None)
    assert m.timestamp is None
