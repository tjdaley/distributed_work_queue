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
MAKE_IT_RIGHT = os.getenv('MAKE_IT_RIGHT', 'false').lower() == 'true'

class DistributedWorkQueue:
    """A distributed work queue using Redis."""
    def __init__(self, redis_host='localhost', redis_port=6379, redis_db=0, queue_name='work_queue'):
        """Initialize a connection to the Redis server."""
        self.logger = FalconLogger(f'DWQ:{queue_name}')
        self.logger.info('Connecting to %s at %s:%s using DB #%s', queue_name, redis_host, redis_port, redis_db)
        self.queue_name = queue_name
        self.redis_connection = redis.Redis(host=redis_host, port=redis_port, db=redis_db)
        self.check_queues()

    def check_queues(self) -> bool:
        """
        Check existing keys to see if any match the key we'll be listening on. It's not necessarily an
        error if the key is not there, but it's a hint that something might be wrong. We scan all keys
        in debug mode to let the operator check for slight spelling errors.
        """
        for key in self.redis_connection.scan_iter('*'):
            self.logger.debug("Found queue/key %s", key)
            if key.decode() == self.queue_name:
                return True
        self.logger.warn("Unable to locate %s in the list of queue/keys", self.queue_name)
        return False

    def enqueue_work(self, work_item: dict):
        """Enqueue a work item to the Redis queue."""
        # Convert the work item to a JSON string to store in Redis
        if isinstance(work_item, str):
            if MAKE_IT_RIGHT:
                work_item = self.attempt_repair(work_item)
        if not isinstance(work_item, dict):
            raise ValueError("work_item must be a dict: %s", work_item)
        work_item_str = json.dumps(work_item)
        self.redis_connection.rpush(self.queue_name, work_item_str)
        self.logger.debug("Queued: %s", work_item_str)

    def dequeue_work(self, timeout: int = 0) -> dict:
        """
        Dequeue a work item from the Redis queue.
        
        Returns a dict if the dequeued item was successfully converted to a dict.
        Otherwise, it returns whatever it dequeued, e.g. a str.
        """
        # Atomically remove and return the first item of the list
        try:
            _, work_item_str = self.redis_connection.blpop(self.queue_name, timeout=timeout)
            self.logger.debug("Dequeued: %s", work_item_str)
        except TypeError as e:
            self.logger.error("Error dequeueing work: %s", e)
            return None
        # Convert the JSON string back to a Python object
        try:
            return json.loads(work_item_str)
        except json.JSONDecodeError as e:
            self.logger.warn("Invalid JSON string: %s, %s", e, work_item_str)
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
                self.logger.error("Error processing work item: %s", e)

    def attempt_repair(self, bad_value):
        """
        Attempt to convert a string to a dict.

        Args:
            bad_value (str): Value that is not a dict

        Returns:
            (dict): Returned if string could be converted to dict otherwise *bad_value* is returned.
        """
        if isinstance(bad_value, str):
            try:
                d = json.loads(bad_value)
                return d
            except:
                pass
        return bad_value

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
