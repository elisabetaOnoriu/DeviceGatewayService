from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy.orm import Session
from app.models.message_schema import MessageCreate
from app.models.message import Message
from app.templates import get_db  # or deps.get_db

app = FastAPI()

@app.post("/messages", status_code=201)
def create_message(payload: MessageCreate, db: Session = Depends(get_db)):
    msg = Message(
        device_id=payload.device_id,
        client_id=payload.client_id,
        timestamp=payload.timestamp,
        payload=payload.payload,
    )
    db.add(msg)
    db.commit()
    db.refresh(msg)
    return {"id": msg.id, "timestamp": msg.timestamp}

@app.get("/messages/{message_id}")
def get_message(message_id: int, db: Session = Depends(get_db)):
    msg = db.get(Message, message_id)
    if not msg:
        raise HTTPException(status_code=404, detail="Message not found")
    return {
        "id": msg.id,
        "device_id": msg.device_id,
        "client_id": msg.client_id,
        "timestamp": msg.timestamp,
        "payload": msg.payload,
    }

@app.get("/messages")
def list_messages(device_id: int | None = None, client_id: int | None = None, db: Session = Depends(get_db)):
    q = db.query(Message)
    if device_id is not None:
        q = q.filter(Message.device_id == device_id)
    if client_id is not None:
        q = q.filter(Message.client_id == client_id)
    q = q.order_by(Message.device_id, Message.timestamp.desc())
    return [
        {"id": m.id, "device_id": m.device_id, "client_id": m.client_id, "timestamp": m.timestamp}
        for m in q.limit(200).all()
    ]
