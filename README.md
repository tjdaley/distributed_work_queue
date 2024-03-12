# distributed_work_queue
Simple distributed work queue using redis

## Installation

Install this package from my private repository:

```python -m pip install git+https://github.com/tjdaley/distributed_work_queue.git```

## Description

The DistributedWorkQueue class  connects to a Redis server to enqueue and dequeue work items. Work items are serialized to JSON strings before being stored in Redis, allowing you to queue complex data structures. The worker_process method can spawn worker processes that continuously dequeue and process work items.

Ensure you replace 'your_redis_server_host' with the actual host address of your Redis server. This setup requires Redis to be installed and accessible from all servers that will produce or consume work items.

This approach provides the flexibility needed to distribute work across multiple servers efficiently. It can easily be scaled to accommodate a larger number of producers and consumers by adding more servers.

## Sample Usage

```python
import multiprocessing
import redis

# Sample work function
def example_worker(work_item):
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
```

# Author
Thomas J. Daley is a board-certified family law attorney, practicing throughout the United States, primarily in Texas, who develops technology solutions for use by litigation attorneys.
