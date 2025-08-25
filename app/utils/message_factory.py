from __future__ import annotations
from pathlib import Path
from string import Template
from datetime import datetime, timezone, timedelta
from typing import Optional
import random
import uuid

from app.models.message_schema import MessageCreate

"""Locate the XML template"""
TEMPLATE_PATH = Path(__file__).resolve().parents[1] / "templates" / "message_template.xml"


def _iso_utc(dt: datetime | None = None) -> str:
    """Return ISO-8601 UTC string, e.g. 2025-08-19T12:34:56Z."""
    dt = dt or datetime.now(timezone.utc)
    return dt.astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def random_timestamp_utc(past_hours: int = 72) -> datetime:
    """Random timezone-aware datetime within the last `past_hours` hours."""
    now = datetime.now(timezone.utc)
    delta = timedelta(seconds=random.randint(0, past_hours * 3600))
    return now - delta


def _random_sensor() -> str:
    return random.choice(["temp", "humidity", "pressure", "battery"])


def _random_value_unit(sensor: str) -> tuple[str, str]:
    if sensor == "temp":
        return f"{random.uniform(15.0, 35.0):.2f}", "C"
    if sensor == "humidity":
        return str(random.randint(20, 90)), "%"
    if sensor == "pressure":
        return str(random.randint(960, 1040)), "hPa"
    if sensor == "battery":
        return str(random.randint(0, 100)), "%"
    return "0", ""


def _render_xml_from_template(
    *,
    device_id: int,
    client_id: int,
    sensor: Optional[str] = None,
    value: Optional[str] = None,
    unit: Optional[str] = None,
    firmware: Optional[str] = None,
    source: str = "gateway",
    timestamp_iso: Optional[str] = None,
) -> str:
    """Fill app/templates/message_template.xml using string.Template."""
    if not TEMPLATE_PATH.exists():
        raise FileNotFoundError(f"XML template not found at {TEMPLATE_PATH}")

    """Choose randoms/defaults"""
    sensor = sensor or _random_sensor()
    if value is None or unit is None:
        v, u = _random_value_unit(sensor)
        value = value or v
        unit = unit or u

    firmware = firmware or f"v{random.randint(1,3)}.{random.randint(0,9)}.{random.randint(0,9)}"
    timestamp_iso = timestamp_iso or _iso_utc()

    xml_tpl = Template(TEMPLATE_PATH.read_text(encoding="utf-8"))
    xml_str = xml_tpl.substitute(
        message_id=str(uuid.uuid4()),
        device_id=device_id,
        client_id=client_id,
        timestamp=timestamp_iso,
        sensor=sensor,
        value=value,
        unit=unit,
        firmware=firmware,
        source=source,
    )
    return xml_str


def make_random_message_xml(
    *,
    device_id: Optional[int] = None,
    client_id: Optional[int] = None,
    with_timestamp: bool = True,
) -> MessageCreate:
    """
    Build a MessageCreate with an XML payload produced from the template.
    - If with_timestamp=False, timestamp is None (DB will set server_default).
    """
    device_id = device_id or random.randint(1, 5)
    client_id = client_id or random.randint(1, 3)

    ts_dt: Optional[datetime] = random_timestamp_utc() if with_timestamp else None
    xml_payload = _render_xml_from_template(
        device_id=device_id,
        client_id=client_id,
        timestamp_iso=_iso_utc(ts_dt) if ts_dt else _iso_utc(),
    )

    return MessageCreate(
        device_id=device_id,
        client_id=client_id,
        timestamp=ts_dt if with_timestamp else None,
        payload=xml_payload,  # NOTE: payload is str (XML), not dict
    )
