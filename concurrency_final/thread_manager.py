from concurrent.futures import as_completed
from concurrent.futures import ThreadPoolExecutor
import threading
from concurrency_final.base_worker import BaseWorker

class ThreadManager:
    """Central manager that assigns threads to clients and controls lifecycle."""
    def __init__(self, max_workers=4):
        self.executor = ThreadPoolExecutor(max_workers=max_workers)
        self.clients = []
        self.futures = []
 
    def _client_task(self, client: BaseWorker):

        thread = threading.current_thread()
        client.assign_thread(thread)
        client.start()  # runs until stop() is called
 
    def add_client(self, client: BaseWorker):
        """Submit a client to the pool."""
        self.clients.append(client)
        future = self.executor.submit(self._client_task, client)
        self.futures.append(future)
        print(f"[Manager] Client {client.client_id} assigned to thread pool.")
 
    def wait_for_all(self):
        """Wait until all client threads are complete."""
        for future in as_completed(self.futures):
            future.result()
        print("[Manager] All clients completed.")
 
