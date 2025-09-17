# Developer Documentation

## Quick Start

### 1. Start LocalStack
```bash
docker compose up -d
````

### 2. Create the SQS queue

```bash
poetry run awslocal sqs create-queue --queue-name device-messages
```

### 3. Run the services

* **Device Gateway (producer)** – generates random XML messages and sends them into SQS:

```bash
poetry run python main.py
```

* **Terminal Data Service (consumer)** – listens to the queue, consumes XML messages, and processes them:

```bash
poetry run python terminal_service.py
```

You should now see XML messages being produced by the Device Gateway and consumed by the Terminal Data Service in real time.

---

## Message Flow

```
+-------------------+       +---------------------+       +------------------------+
| Device Gateway    | --->  |  SQS Queue          | --->  | Terminal Data Service  |
| (Producer)        |       |  "device-messages"  |       | (Consumer)             |
+-------------------+       +---------------------+       +------------------------+
         |                           |                              |
         |   send-message (XML)      |                              |
         |-------------------------->|                              |
         |                           |   receive-message (XML)      |
         |                           |----------------------------->|
         |                           |   delete-message             |
         |                           |<-----------------------------|
```

* The **Device Gateway** uses an XML template (`app/templates/message_template.xml`) and `message_factory.py` to generate valid device messages.
* Messages are sent to the **device-messages** SQS queue in LocalStack.
* The **Terminal Data Service** receives the XML messages, parses them, and acknowledges them (delete from queue).

---

## Testing

### Validate schema locally

Unit tests cover:

* XML payload well-formedness
* `device_id` and `client_id` > 0
* Random message factory producing valid XML

Run tests:

```bash
poetry run pytest
```

### Manually send and receive a message

Send a test message into the queue:

```bash
poetry run awslocal sqs send-message \
  --queue-url http://localhost:4566/000000000000/device-messages \
  --message-body "<Message><Header>...</Header><Body>...</Body></Message>"
```

Receive the message:

```bash
poetry run awslocal sqs receive-message \
  --queue-url http://localhost:4566/000000000000/device-messages
```

## Settings (env)

- `NUM_DEVICES` (default: 3) — how many simulated devices to produce messages for (IDs 1..N).
- `SEND_INTERVAL_SEC` (default: 2) — seconds between message cycles (each cycle produces one message per device).
- `AWS_ACCESS_KEY_ID`, `AWS_SECRET_ACCESS_KEY`, `AWS_REGION`, `LOCALSTACK_ENDPOINT`, `QUEUE_NAME` — AWS/LocalStack configuration.

The service loads settings from `.env` via Pydantic `BaseSettings` (`app/config/settings.py`).

```
