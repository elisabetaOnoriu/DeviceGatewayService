import pytest
from pydantic import ValidationError
from datetime import datetime, timezone
import xml.etree.ElementTree as ET

from app.models.message_schema import MessageCreate, SendResult


def test_message_create_valid_with_xml():
    xml_payload = """
    <Message>
      <Header>
        <MessageID>123</MessageID>
        <DeviceID>1</DeviceID>
        <ClientID>2</ClientID>
        <Timestamp>2025-08-19T12:34:56Z</Timestamp>
      </Header>
      <Body>
        <Sensor>temp</Sensor>
        <Value>25.5</Value>
        <Unit>C</Unit>
      </Body>
    </Message>
    """
    m = MessageCreate(device_id=1, client_id=2, payload=xml_payload)
    assert m.device_id == 1
    assert m.client_id == 2
    assert isinstance(m.payload, str)

    # Validate XML can be parsed
    root = ET.fromstring(m.payload)
    assert root.tag == "Message"
    assert root.find(".//Sensor").text == "temp"


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
        MessageCreate(device_id=1, client_id=1, payload={"not": "xml"})  # type: ignore


def test_forbid_extra_fields():
    with pytest.raises(ValidationError):
        MessageCreate(
            device_id=1,
            client_id=1,
            payload="<Message/>",
            extra_field="oops",  # forbidden by ConfigDict
        )


def test_send_result_minimal_ok():
    s = SendResult(queue_url="http://localhost/queue", provider_message_id="abc-123")
    # HttpUrl/AnyUrl is not a str → cast or check components:
    assert str(s.queue_url).startswith("http")
    assert s.queue_url.scheme in ("http", "https")

