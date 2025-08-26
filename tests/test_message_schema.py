# tests/test_message_schema.py
import xml.etree.ElementTree as ET
import pytest
from pydantic import ValidationError

from app.models.message_schema import MessageCreate
from app.models.send_result_schema import SendResult

""" Default namespace from the XML template (xmlns="urn:example:device-message")"""
NS = {"m": "urn:example:device-message"}


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


def test_payload_must_be_string():
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


def test_send_result_minimal_ok():
    s = SendResult(queue_url="http://localhost/queue", provider_message_id="abc-123")
    assert str(s.queue_url).startswith("http")
    assert s.queue_url.scheme in ("http", "https")
