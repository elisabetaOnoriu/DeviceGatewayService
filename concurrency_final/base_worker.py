import threading
 
class BaseWorker:
    """Base class for clients that use a thread assigned by ThreadPoolManager."""
    def __init__(self, client_id, kwargs=None):
        self.client_id = client_id
        self.thread = None
        self.running = threading.Event()
        self.running.clear()
 
    def assign_thread(self, thread: threading.Thread):
        """Called by the manager to assign this client to a specific thread."""
        self.thread = thread
 
    def run(self):
        raise NotImplementedError("Client subclass must implement 'run()'")
   
    def start(self):
        """Called by the ThreadPoolManager to start the client."""
        self.running.set()
        print(f"[Client {self.client_id}] Starting in {self.thread.name}")
        self.run()
