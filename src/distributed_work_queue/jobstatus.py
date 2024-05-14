"""
jobstatus.py - JobStatus class definition
"""

import uuid
import json
import os
from typing import Dict, Optional
from dotenv import load_dotenv
from falconlogger.flogger import FalconLogger
from abc import ABC, abstractmethod
import redis
from pymongo import MongoClient

load_dotenv()
DEBUG = os.getenv('DEBUG', 'false').lower() == 'true'
DATASTORE = os.getenv('JOBSTATUS_DATASTORE', 'redis').lower()

class DataStore(ABC):
    @abstractmethod
    def set(self, key: str, value: str, ttl: int):
        pass

    @abstractmethod
    def get(self, key: str) -> Optional[str]:
        pass

    @abstractmethod
    def delete(self, key: str):
        pass

class RedisDataStore(DataStore):
    def __init__(self):
        redis_host = os.getenv('JOBSTATUS_REDIS_HOST', 'localhost')
        redis_port = int(os.getenv('JOBSTATUS_REDIS_PORT', '6379'))
        redis_db = int(os.getenv('JOBSTATUS_REDIS_DB', '0'))
        self.redis = redis.Redis(host=redis_host, port=redis_port, db=redis_db, decode_responses=True)

    def set(self, key: str, value: str, ttl: int = 300):
        self.redis.setex(key, ttl, value)

    def get(self, key: str) -> Optional[str]:
        return self.redis.get(key)

    def delete(self, key: str):
        self.redis.delete(key)

class MongoDataStore(DataStore):
    def __init__(self):
        mongo_host = os.getenv('JOBSTATUS_MONGO_HOST', 'localhost')
        mongo_port = int(os.getenv('JOBSTATUS_MONGO_PORT', '27017'))
        mongo_db = os.getenv('JOBSTATUS_MONGO_DB', 'falcon')
        mongo_collection = os.getenv('JOBSTATUS_MONGO_COLLECTION', 'jobstatus')
        self.client = MongoClient(mongo_host, mongo_port)
        self.db = self.client[mongo_db]
        self.collection = self.db[mongo_collection]
        # create and index on the _id field
        self.collection.create_index('_id', unique=True)

    def set(self, key: str, value: str, ttl: int = 300):
        data = {'_id': key, 'value': value}
        self.collection.update_one({'_id': key}, {'$set': data}, upsert=True)

    def get(self, key: str) -> Optional[str]:
        result = self.collection.find_one({'_id': key})
        return result['value'] if result else None

    def delete(self, key: str):
        self.collection.delete_one({'_id': key})

class JobStatus:
    def __init__(self, ttl: int = 600, name_space='STATUS'):
        """Initialize the datastore based on the environment variable."""
        self.logger = FalconLogger(f'job_status:{name_space}')
        self.name_space = name_space
        self.ttl = ttl

        if DATASTORE == 'redis':
            self.datastore = RedisDataStore()
        elif DATASTORE == 'mongodb':
            self.datastore = MongoDataStore()
        else:
            raise ValueError(f"Unsupported datastore: {DATASTORE}")

        self.logger.info('Using datastore: %s', DATASTORE)

    def add_job(self, request_id: str = None) -> str:
        request_id = request_id or str(uuid.uuid4())
        job_status = {'request_id': request_id, 'status': 'QUEUED'}
        self.datastore.set(self.make_key(request_id), json.dumps(job_status, default=str), self.ttl)
        return request_id

    def get_status(self, request_id: str) -> Optional[Dict]:
        request_data = self.datastore.get(self.make_key(request_id))
        if request_data:
            try:
                return json.loads(request_data)
            except json.JSONDecodeError:
                self.logger.error('Failed to decode JSON data for request ID: %s', request_id)
                self.datastore.delete(self.make_key(request_id))
                return None
        return None

    def update_status(self, request_id: str, status: str, message: Optional[str] = None):
        request_data = self.get_status(request_id)
        if request_data:
            request_data['status'] = status
            if message:
                request_data['message'] = message
            self.datastore.set(self.make_key(request_id), json.dumps(request_data, default=str), self.ttl)

    def poll_status(self, request_id: str) -> Optional[Dict]:
        request_data = self.get_status(request_id)
        if request_data:
            if request_data.get('status', '') in ['SUCCESS', 'FAIL']:
                self.datastore.delete(request_id)
            return request_data
        return None
    
    def make_key(self, request_id: str) -> str:
        return f'{self.name_space}::{request_id}'
    

# Example usage:
if __name__ == "__main__":
    queue = JobStatus()
    request_id = queue.add_job()  # In reality, you'll probably pass in a request ID
    print(f"Queued request with ID: {request_id}")
    status = queue.poll_status(request_id)
    print(f"Polled request status: {status}")
    status = queue.update_status(request_id, 'SUCCESS', 'Work completed successfully')
    status = queue.poll_status(request_id)
    print(f"Polled request status: {status}")
    status = queue.poll_status(request_id)
    print(f"Polled request status: {status}")  # Should return None