#!/usr/bin/env python3
import json
import time
import random
import logging
import threading
from datetime import datetime
import os
import signal
import sys

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger('database-client')

# Configure database transaction log
db_logger = logging.getLogger('database.transactions')
db_handler = logging.FileHandler('/logs/database-transactions.log')
db_handler.setFormatter(logging.Formatter('%(asctime)s - %(message)s'))
db_logger.addHandler(db_handler)
db_logger.setLevel(logging.INFO)

class DatabaseClient:
    def __init__(self):
        self.running = True
        self.connection_pool_size = 10
        self.active_connections = 0
        self.total_queries = 0
        self.failed_queries = 0
        
    def simulate_database_query(self, query_type, query_id):
        """Simulate a database query"""
        start_time = time.time()
        
        # Log query start
        query_log = {
            'query_id': query_id,
            'query_type': query_type,
            'status': 'started',
            'timestamp': datetime.now().isoformat(),
            'connection_id': random.randint(1, self.connection_pool_size)
        }
        db_logger.info(json.dumps(query_log))
        
        try:
            # Simulate different query types with different execution times
            if query_type == 'SELECT':
                processing_time = random.uniform(0.1, 2.0)
            elif query_type == 'INSERT':
                processing_time = random.uniform(0.5, 3.0)
            elif query_type == 'UPDATE':
                processing_time = random.uniform(1.0, 4.0)
            elif query_type == 'DELETE':
                processing_time = random.uniform(0.8, 2.5)
            else:
                processing_time = random.uniform(0.5, 5.0)
            
            time.sleep(processing_time)
            
            # Simulate query failures
            success = random.random() > 0.05  # 95% success rate
            
            end_time = time.time()
            actual_time = end_time - start_time
            
            # Log query completion
            completion_log = {
                'query_id': query_id,
                'query_type': query_type,
                'status': 'completed' if success else 'failed',
                'execution_time_ms': round(actual_time * 1000, 2),
                'timestamp': datetime.now().isoformat(),
                'error': None if success else 'Connection timeout'
            }
            db_logger.info(json.dumps(completion_log))
            
            if success:
                self.total_queries += 1
                logger.info(f"Query {query_id} ({query_type}) completed successfully")
            else:
                self.failed_queries += 1
                logger.error(f"Query {query_id} ({query_type}) failed")
            
            return success
            
        except Exception as e:
            end_time = time.time()
            actual_time = end_time - start_time
            
            error_log = {
                'query_id': query_id,
                'query_type': query_type,
                'status': 'error',
                'execution_time_ms': round(actual_time * 1000, 2),
                'timestamp': datetime.now().isoformat(),
                'error': str(e)
            }
            db_logger.info(json.dumps(error_log))
            
            self.failed_queries += 1
            logger.error(f"Query {query_id} error: {str(e)}")
            return False
    
    def query_generator(self):
        """Generate database queries continuously"""
        query_types = ['SELECT', 'INSERT', 'UPDATE', 'DELETE', 'ANALYZE']
        
        while self.running:
            try:
                # Generate random queries
                num_queries = random.randint(1, 5)
                
                for i in range(num_queries):
                    query_id = f"query_{int(time.time())}_{random.randint(1000, 9999)}"
                    query_type = random.choice(query_types)
                    
                    self.simulate_database_query(query_type, query_id)
                    
                    # Small delay between queries
                    time.sleep(random.uniform(0.5, 2.0))
                
                # Longer delay before next batch
                time.sleep(random.uniform(5.0, 15.0))
                
            except Exception as e:
                logger.error(f"Query generation error: {str(e)}")
                time.sleep(10)
    
    def connection_monitor(self):
        """Monitor database connections"""
        while self.running:
            try:
                # Simulate connection monitoring
                self.active_connections = random.randint(1, self.connection_pool_size)
                
                connection_stats = {
                    'timestamp': datetime.now().isoformat(),
                    'active_connections': self.active_connections,
                    'pool_size': self.connection_pool_size,
                    'pool_utilization_percent': (self.active_connections / self.connection_pool_size) * 100,
                    'total_queries': self.total_queries,
                    'failed_queries': self.failed_queries,
                    'success_rate': (self.total_queries / max(1, self.total_queries + self.failed_queries)) * 100
                }
                
                db_logger.info(json.dumps(connection_stats))
                
                # Log warnings for connection issues
                if self.active_connections > self.connection_pool_size * 0.8:
                    logger.warning(f"High connection usage: {self.active_connections}/{self.connection_pool_size}")
                
                time.sleep(30)  # Monitor every 30 seconds
                
            except Exception as e:
                logger.error(f"Connection monitor error: {str(e)}")
                time.sleep(60)
    
    def run(self):
        """Start the database client"""
        logger.info("Database client starting up")
        
        # Start threads
        threads = []
        
        # Query generator thread
        query_thread = threading.Thread(target=self.query_generator, daemon=True)
        query_thread.start()
        threads.append(query_thread)
        
        # Connection monitor thread
        monitor_thread = threading.Thread(target=self.connection_monitor, daemon=True)
        monitor_thread.start()
        threads.append(monitor_thread)
        
        logger.info("Database client started")
        
        # Keep main thread alive
        try:
            while self.running:
                time.sleep(1)
        except KeyboardInterrupt:
            logger.info("Received shutdown signal")
        finally:
            self.running = False
            logger.info("Database client shutting down")

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
    
    # Start database client
    client = DatabaseClient()
    client.run()