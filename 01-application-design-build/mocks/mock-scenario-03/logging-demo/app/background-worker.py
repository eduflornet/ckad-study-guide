#!/usr/bin/env python3
import json
import time
import random
import logging
import threading
from datetime import datetime, timedelta
import os
import signal
import sys
from queue import Queue

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger('background-worker')

# Configure job execution log
job_logger = logging.getLogger('jobs.execution')
job_handler = logging.FileHandler('/logs/job-execution.log')
job_handler.setFormatter(logging.Formatter('%(asctime)s - %(message)s'))
job_logger.addHandler(job_handler)
job_logger.setLevel(logging.INFO)

# Configure job metrics log
metrics_logger = logging.getLogger('jobs.metrics')
metrics_handler = logging.FileHandler('/logs/job-metrics.log')
metrics_handler.setFormatter(logging.Formatter('%(asctime)s - %(message)s'))
metrics_logger.addHandler(metrics_handler)
metrics_logger.setLevel(logging.INFO)

class BackgroundWorker:
    def __init__(self):
        self.job_queue = Queue()
        self.running = True
        self.processed_jobs = 0
        self.failed_jobs = 0
        self.worker_threads = 3
    
    def create_sample_jobs(self):
        """Create sample jobs for processing"""
        job_types = [
            'email_notification',
            'data_backup',
            'report_generation',
            'image_processing',
            'data_sync',
            'cache_cleanup',
            'log_rotation'
        ]
        
        while self.running:
            try:
                # Create random jobs
                for _ in range(random.randint(1, 5)):
                    job = {
                        'id': f"job_{int(time.time())}_{random.randint(1000, 9999)}",
                        'type': random.choice(job_types),
                        'priority': random.choice(['low', 'normal', 'high']),
                        'created_at': datetime.now().isoformat(),
                        'params': {
                            'target': f"target_{random.randint(1, 100)}",
                            'batch_size': random.randint(10, 1000)
                        }
                    }
                    self.job_queue.put(job)
                    
                    job_log_entry = {
                        'job_id': job['id'],
                        'type': job['type'],
                        'priority': job['priority'],
                        'status': 'queued',
                        'timestamp': datetime.now().isoformat()
                    }
                    job_logger.info(json.dumps(job_log_entry))
                
                # Wait before creating more jobs
                time.sleep(random.uniform(5.0, 15.0))
                
            except Exception as e:
                logger.error(f"Job creation error: {str(e)}")
                time.sleep(10)
    
    def process_job(self, job):
        """Process a single job"""
        job_id = job['id']
        job_type = job['type']
        
        start_time = time.time()
        
        # Log job start
        job_log_entry = {
            'job_id': job_id,
            'type': job_type,
            'status': 'started',
            'timestamp': datetime.now().isoformat(),
            'worker_thread': threading.current_thread().name
        }
        job_logger.info(json.dumps(job_log_entry))
        
        try:
            # Simulate job processing
            processing_time = random.uniform(1.0, 10.0)
            
            # Simulate different job types with different processing characteristics
            if job_type == 'email_notification':
                processing_time = random.uniform(0.5, 2.0)
            elif job_type == 'data_backup':
                processing_time = random.uniform(30.0, 120.0)
            elif job_type == 'report_generation':
                processing_time = random.uniform(10.0, 60.0)
            elif job_type == 'image_processing':
                processing_time = random.uniform(5.0, 30.0)
            
            # Simulate processing steps
            steps = ['initializing', 'processing', 'validating', 'finalizing']
            for i, step in enumerate(steps):
                step_log = {
                    'job_id': job_id,
                    'step': step,
                    'progress_percent': ((i + 1) / len(steps)) * 100,
                    'timestamp': datetime.now().isoformat()
                }
                job_logger.info(json.dumps(step_log))
                
                time.sleep(processing_time / len(steps))
            
            # Simulate job failures
            success = random.random() > 0.1  # 90% success rate
            
            end_time = time.time()
            actual_processing_time = end_time - start_time
            
            # Log job completion
            completion_log = {
                'job_id': job_id,
                'type': job_type,
                'status': 'completed' if success else 'failed',
                'processing_time_ms': round(actual_processing_time * 1000, 2),
                'timestamp': datetime.now().isoformat(),
                'error': None if success else 'Processing timeout'
            }
            job_logger.info(json.dumps(completion_log))
            
            # Log metrics
            metrics_log = {
                'timestamp': datetime.now().isoformat(),
                'job_id': job_id,
                'job_type': job_type,
                'processing_time_ms': round(actual_processing_time * 1000, 2),
                'cpu_usage_percent': random.uniform(20, 90),
                'memory_usage_mb': random.uniform(100, 500),
                'disk_usage_mb': random.uniform(10, 100),
                'success': success
            }
            metrics_logger.info(json.dumps(metrics_log))
            
            if success:
                self.processed_jobs += 1
                logger.info(f"Job {job_id} completed successfully")
            else:
                self.failed_jobs += 1
                logger.error(f"Job {job_id} failed")
            
            return success
            
        except Exception as e:
            end_time = time.time()
            actual_processing_time = end_time - start_time
            
            error_log = {
                'job_id': job_id,
                'type': job_type,
                'status': 'error',
                'processing_time_ms': round(actual_processing_time * 1000, 2),
                'timestamp': datetime.now().isoformat(),
                'error': str(e)
            }
            job_logger.info(json.dumps(error_log))
            
            self.failed_jobs += 1
            logger.error(f"Job {job_id} error: {str(e)}")
            return False
    
    def worker_thread(self):
        """Worker thread that processes jobs from the queue"""
        thread_name = threading.current_thread().name
        logger.info(f"Worker thread {thread_name} started")
        
        while self.running:
            try:
                # Get job from queue (with timeout)
                job = self.job_queue.get(timeout=5.0)
                self.process_job(job)
                self.job_queue.task_done()
                
            except Exception as e:
                if self.running:  # Only log errors if we're still running
                    logger.error(f"Worker thread {thread_name} error: {str(e)}")
                time.sleep(1)
        
        logger.info(f"Worker thread {thread_name} stopped")
    
    def metrics_reporter(self):
        """Report worker metrics periodically"""
        while self.running:
            try:
                metrics = {
                    'timestamp': datetime.now().isoformat(),
                    'queue_size': self.job_queue.qsize(),
                    'processed_jobs': self.processed_jobs,
                    'failed_jobs': self.failed_jobs,
                    'success_rate': (self.processed_jobs / max(1, self.processed_jobs + self.failed_jobs)) * 100,
                    'worker_threads': self.worker_threads
                }
                metrics_logger.info(json.dumps(metrics))
                
                # Log warnings for queue buildup
                if self.job_queue.qsize() > 20:
                    logger.warning(f"Job queue buildup detected: {self.job_queue.qsize()} jobs pending")
                
                time.sleep(30)  # Report every 30 seconds
                
            except Exception as e:
                logger.error(f"Metrics reporter error: {str(e)}")
                time.sleep(60)
    
    def run(self):
        """Start the background worker"""
        logger.info("Background worker starting up")
        
        # Start worker threads
        threads = []
        
        # Job creation thread
        job_creator = threading.Thread(target=self.create_sample_jobs, daemon=True)
        job_creator.start()
        threads.append(job_creator)
        
        # Worker threads
        for i in range(self.worker_threads):
            worker = threading.Thread(target=self.worker_thread, daemon=True, name=f"worker-{i+1}")
            worker.start()
            threads.append(worker)
        
        # Metrics reporter thread
        metrics_thread = threading.Thread(target=self.metrics_reporter, daemon=True)
        metrics_thread.start()
        threads.append(metrics_thread)
        
        logger.info(f"Background worker started with {self.worker_threads} worker threads")
        
        # Keep the main thread alive
        try:
            while self.running:
                time.sleep(1)
        except KeyboardInterrupt:
            logger.info("Received shutdown signal")
        finally:
            self.running = False
            logger.info("Background worker shutting down")

def signal_handler(sig, frame):
    """Handle shutdown signals gracefully"""
    logger.info("Received shutdown signal, cleaning up...")
    sys.exit(0)

if __name__ == '__main__':
    # Setup signal handlers
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    # Ensure log directory exists
    os.makedirs('/logs', exist_ok=True)
    
    # Start background worker
    worker = BackgroundWorker()
    worker.run()