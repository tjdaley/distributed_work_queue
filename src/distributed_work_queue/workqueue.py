"""
workqueue.py - A distributed work queue using Redis.
"""
from typing import Any, Callable
import json
import multiprocessing
import os
import redis
from dotenv import load_dotenv
from falconlogger.flogger import FalconLogger

load_dotenv()
DEBUG = os.getenv('DEBUG', 'false').lower() == 'true'

class DistributedWorkQueue:
    """A distributed work queue using Redis."""
    def __init__(self, redis_host='localhost', redis_port=6379, redis_db=0, queue_name='work_queue'):
        """Initialize a connection to the Redis server."""
        self.logger = FalconLogger(f'DWQ:{queue_name}')
        self.logger.info('Connecting to %s at %s:%s', queue_name, redis_host, redis_port)
        self.queue_name = queue_name
        self.redis_connection = redis.Redis(host=redis_host, port=redis_port, db=redis_db)

    def enqueue_work(self, work_item: Any):
        """Enqueue a work item to the Redis queue."""
        # Convert the work item to a JSON string to store in Redis
        work_item_str = json.dumps(work_item)
        self.redis_connection.rpush(self.queue_name, work_item_str)

    def dequeue_work(self, timeout: int = 0) -> Any:
        """Dequeue a work item from the Redis queue."""
        # Atomically remove and return the first item of the list
        try:
            _, work_item_str = self.redis_connection.blpop(self.queue_name, timeout=timeout)
        except TypeError:
            return None
        # Convert the JSON string back to a Python object
        try:
            return json.loads(work_item_str)
        except json.JSONDecodeError:
            return work_item_str

    def worker_process(self, worker_function: Callable):
        """Continuously process work items using the provided worker function."""
        while True:
            try:
                # Dequeue a work item
                work_item = self.dequeue_work()
                # Process the work item
                worker_function(work_item)
            except Exception as e:  # pylint: disable=broad-except
                print(f"Error processing work item: {e}")

# Example usage:
if __name__ == '__main__':
    def example_worker(work_item):
        """Example worker function that processes work items."""
        print(f"Processing: {work_item}")

    # Initialize the distributed work queue
    queue = DistributedWorkQueue(redis_host='your_redis_server_host')

    # Example: Enqueue work items (run this on the producer server)
    for i in range(10):
        queue.enqueue_work(f"Item {i}")

    # Start a process to process work items (run this on the consumer server)
    process = multiprocessing.Process(target=queue.worker_process, args=(example_worker,))
    process.start()
    process.join()
