# Developer Documentation

## 🚀 Quick Start

1. **Start LocalStack**

   ```bash
   docker compose up -d
   ```

2. **Create the queue**

   ```bash
   poetry run awslocal sqs create-queue --queue-name device-messages
   ```

3. **Run the services**

   * Device Gateway (producer):

     ```bash
     poetry run python gateway.py
     ```
   * Terminal Data Service (consumer):

     ```bash
     poetry run python terminal_service.py
     ```

👉 You should now see messages being **sent by the gateway** and **received by the terminal service** in real time.

---

## 🔄 Message Flow

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

The **Device Gateway** generates and sends XML messages into the `device-messages` queue.
The **Terminal Data Service** listens to the same queue, consumes messages, displays them, and removes them from the queue once processed.
