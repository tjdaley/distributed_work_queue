# distributed_work_queue
Simple distributed work queue using redis

The DistributedWorkQueue class  connects to a Redis server to enqueue and dequeue work items. Work items are serialized to JSON strings before being stored in Redis, allowing you to queue complex data structures. The worker_process method can spawn worker processes that continuously dequeue and process work items.

Ensure you replace 'your_redis_server_host' with the actual host address of your Redis server. This setup requires Redis to be installed and accessible from all servers that will produce or consume work items.

This approach provides the flexibility needed to distribute work across multiple servers efficiently. It can easily be scaled to accommodate a larger number of producers and consumers by adding more servers.

# Author
Thomas J. Daley is a board-certified family law attorney, practicing throughout the United States, primarily in Texas, who develops technology solutions for use by litigation attorneys.
