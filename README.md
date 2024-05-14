# distributed_work_queue
Simple distributed work queue using redis

## Installation

Install this package from my private repository:

```python -m pip install git+https://github.com/tjdaley/distributed_work_queue.git```

# WorkQueue

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

# JobStatus

## Description

JobStatus is a class that can be used to track the status of a job between processs. For example, when a web
server queues a request, it can add the job_id to the JobStatus. As the back-end processes pick up the work from
the distributed work queue, they can update the status of the job through JobStatus. In the meantime, the web server can poll the JobStatus class with the request ID to determine when the job is complete.

This class uses either Redis or MongoDb to keep track of the job's status. It's easy to implement other datastore
options, too.

## Environment variables

| Variable | Description | Default|
|---|---|---|
| JOBSTATUS_DATASTORE | String that indicates which datastore to use, redis or mongodb | redis |
| JOBSTATUS_REDIS_HOST | IP address or name of the Redis host | localhost |
| JOBSTATUS_REDIS_PORT | Integer port number that the Redis host is listening on | 6379 |
| JOBSTATUS_REDIS_DB | Integer designating the Redis DB to use | 0 |
| JOBSTATUS_MONGO_HOST | OP address or name of the mongodb server | localhost |
| JOBSTATUS_MONGO_PORT | Integer port number that MongoDb is listeningn on | 27017 |
| JOBSTATUS_MONGO_DB | String indicating the database name | falcon |
| JOBSTATUS_MONGO_COLLECTION | Collection within the database that we use to track job status | jobstatus |

## Sample Usage

### Service that submits requests and polls for status

```python
job_status = JobStatus()
job_id = job_status.add_job()  # Usually, you'll supply your own job_id as an argument
:
:
status = job_status.poll_status(job_id)
print(status)
```

### Service that does the work

```python
job_status = JobStatus()
job_id = '111'  # obtainined from the code that queues the job
job_status.update_status(job_id, 'WORKING', "Working on your job')
:
: Do work
:
job_status.update_status(job_id, 'SUCCESS', 'normal successful completion')
```

# Author
Thomas J. Daley is a board-certified family law attorney, practicing throughout the United States, primarily in Texas, who develops technology solutions for use by litigation attorneys.
