#!/usr/bin/env python3
import json
import time
import os
import logging
import threading
import re
from datetime import datetime
import glob

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger('log-processor')

class LogProcessor:
    def __init__(self):
        self.input_directory = '/collected-logs'
        self.output_directory = '/processed-logs'
        self.running = True
        self.processed_count = 0
        
        # Ensure output directory exists
        os.makedirs(self.output_directory, exist_ok=True)
        
        # Log processing rules
        self.processing_rules = {
            'access.log': self.process_access_logs,
            'error.log': self.process_error_logs,
            'application.log': self.process_application_logs,
            'database-queries.log': self.process_database_logs,
            'job-execution.log': self.process_job_logs
        }
        
        # Log level mapping
        self.log_levels = {
            'DEBUG': 10,
            'INFO': 20,
            'WARNING': 30,
            'ERROR': 40,
            'CRITICAL': 50
        }
    
    def extract_log_level(self, message):
        """Extract log level from message"""
        level_patterns = {
            'ERROR': r'\b(error|exception|failed|failure)\b',
            'WARNING': r'\b(warn|warning|deprecated)\b',
            'DEBUG': r'\b(debug|trace)\b',
            'INFO': r'\b(info|started|completed|success)\b'
        }
        
        message_lower = message.lower()
        
        for level, pattern in level_patterns.items():
            if re.search(pattern, message_lower):
                return level
        
        return 'INFO'  # Default level
    
    def process_access_logs(self, log_entry):
        """Process access log entries"""
        processed = log_entry.copy()
        
        try:
            # Parse the message if it's JSON
            if 'message' in processed and processed['message'].startswith('{'):
                access_data = json.loads(processed['message'])
                processed.update(access_data)
                del processed['message']
            
            # Add processing metadata
            processed.update({
                'log_category': 'access',
                'log_level': 'INFO',
                'processed_at': datetime.now().isoformat()
            })
            
            # Extract additional fields
            if 'path' in processed:
                processed['endpoint'] = processed['path'].split('?')[0]
            
            if 'status_code' in processed:
                if 200 <= processed['status_code'] < 300:
                    processed['status_category'] = 'success'
                elif 300 <= processed['status_code'] < 400:
                    processed['status_category'] = 'redirect'
                elif 400 <= processed['status_code'] < 500:
                    processed['status_category'] = 'client_error'
                else:
                    processed['status_category'] = 'server_error'
            
        except Exception as e:
            logger.warning(f"Failed to process access log: {str(e)}")
            processed['processing_error'] = str(e)
        
        return processed
    
    def process_error_logs(self, log_entry):
        """Process error log entries"""
        processed = log_entry.copy()
        
        try:
            processed.update({
                'log_category': 'error',
                'log_level': 'ERROR',
                'processed_at': datetime.now().isoformat(),
                'severity': 'high'
            })
            
            # Extract error patterns
            message = processed.get('message', '')
            if 'timeout' in message.lower():
                processed['error_type'] = 'timeout'
            elif 'connection' in message.lower():
                processed['error_type'] = 'connection'
            elif 'validation' in message.lower():
                processed['error_type'] = 'validation'
            else:
                processed['error_type'] = 'unknown'
            
        except Exception as e:
            logger.warning(f"Failed to process error log: {str(e)}")
            processed['processing_error'] = str(e)
        
        return processed
    
    def process_application_logs(self, log_entry):
        """Process application log entries"""
        processed = log_entry.copy()
        
        try:
            message = processed.get('message', '')
            
            # Extract log level from message
            log_level = self.extract_log_level(message)
            
            processed.update({
                'log_category': 'application',
                'log_level': log_level,
                'processed_at': datetime.now().isoformat()
            })
            
            # Extract component name if present
            if 'web-api' in message:
                processed['component'] = 'web-api'
            elif 'background' in message:
                processed['component'] = 'background-task'
            else:
                processed['component'] = 'unknown'
            
        except Exception as e:
            logger.warning(f"Failed to process application log: {str(e)}")
            processed['processing_error'] = str(e)
        
        return processed
    
    def process_database_logs(self, log_entry):
        """Process database log entries"""
        processed = log_entry.copy()
        
        try:
            # Parse JSON message if present
            if 'message' in processed and processed['message'].startswith('{'):
                db_data = json.loads(processed['message'])
                processed.update(db_data)
                del processed['message']
            
            processed.update({
                'log_category': 'database',
                'log_level': 'INFO',
                'processed_at': datetime.now().isoformat()
            })
            
            # Classify query performance
            if 'execution_time_ms' in processed:
                exec_time = processed['execution_time_ms']
                if exec_time > 5000:  # 5 seconds
                    processed['performance_category'] = 'very_slow'
                    processed['log_level'] = 'WARNING'
                elif exec_time > 1000:  # 1 second
                    processed['performance_category'] = 'slow'
                elif exec_time > 100:  # 100ms
                    processed['performance_category'] = 'normal'
                else:
                    processed['performance_category'] = 'fast'
            
        except Exception as e:
            logger.warning(f"Failed to process database log: {str(e)}")
            processed['processing_error'] = str(e)
        
        return processed
    
    def process_job_logs(self, log_entry):
        """Process job execution log entries"""
        processed = log_entry.copy()
        
        try:
            # Parse JSON message if present
            if 'message' in processed and processed['message'].startswith('{'):
                job_data = json.loads(processed['message'])
                processed.update(job_data)
                del processed['message']
            
            processed.update({
                'log_category': 'job',
                'log_level': 'INFO',
                'processed_at': datetime.now().isoformat()
            })
            
            # Set log level based on job status
            status = processed.get('status', 'unknown')
            if status in ['failed', 'error']:
                processed['log_level'] = 'ERROR'
            elif status == 'started':
                processed['log_level'] = 'INFO'
            elif status == 'completed':
                processed['log_level'] = 'INFO'
            
        except Exception as e:
            logger.warning(f"Failed to process job log: {str(e)}")
            processed['processing_error'] = str(e)
        
        return processed
    
    def process_log_file(self, file_path):
        """Process a collected log file"""
        filename = os.path.basename(file_path)
        logger.info(f"Processing log file: {filename}")
        
        try:
            processed_logs = []
            
            with open(file_path, 'r') as f:
                for line_num, line in enumerate(f, 1):
                    if line.strip():
                        try:
                            log_entry = json.loads(line.strip())
                            
                            # Find appropriate processor
                            processor = None
                            for log_type, proc_func in self.processing_rules.items():
                                if log_type in filename:
                                    processor = proc_func
                                    break
                            
                            if processor:
                                processed_log = processor(log_entry)
                            else:
                                # Default processing
                                processed_log = log_entry.copy()
                                processed_log.update({
                                    'log_category': 'unknown',
                                    'log_level': 'INFO',
                                    'processed_at': datetime.now().isoformat()
                                })
                            
                            processed_logs.append(processed_log)
                            
                        except json.JSONDecodeError:
                            logger.warning(f"Invalid JSON on line {line_num} in {filename}")
                        except Exception as e:
                            logger.error(f"Error processing line {line_num} in {filename}: {str(e)}")
            
            # Write processed logs
            output_file = os.path.join(self.output_directory, f"processed_{filename}")
            with open(output_file, 'w') as f:
                for log_entry in processed_logs:
                    f.write(json.dumps(log_entry) + '\n')
            
            logger.info(f"Processed {len(processed_logs)} log entries from {filename}")
            self.processed_count += len(processed_logs)
            
            # Remove processed file
            os.remove(file_path)
            
            return len(processed_logs)
            
        except Exception as e:
            logger.error(f"Error processing file {file_path}: {str(e)}")
            return 0
    
    def process_logs(self):
        """Process collected log files"""
        while self.running:
            try:
                # Find collected log files
                collected_files = glob.glob(os.path.join(self.input_directory, 'collected_*.log'))
                
                if collected_files:
                    for file_path in collected_files:
                        self.process_log_file(file_path)
                else:
                    time.sleep(5)  # Wait if no files to process
                
            except Exception as e:
                logger.error(f"Log processing error: {str(e)}")
                time.sleep(10)
    
    def generate_processing_stats(self):
        """Generate processing statistics"""
        while self.running:
            try:
                stats = {
                    'timestamp': datetime.now().isoformat(),
                    'total_processed': self.processed_count,
                    'processing_rate_per_minute': 0,  # Could be calculated
                    'active_processors': len(self.processing_rules)
                }
                
                stats_file = os.path.join(self.output_directory, 'processing_stats.json')
                with open(stats_file, 'w') as f:
                    json.dump(stats, f, indent=2)
                
                logger.info(f"Processing stats: {self.processed_count} total logs processed")
                
                time.sleep(60)  # Update stats every minute
                
            except Exception as e:
                logger.error(f"Stats generation error: {str(e)}")
                time.sleep(120)
    
    def run(self):
        """Start the log processor"""
        logger.info("Log processor starting up")
        
        # Start processing threads
        processing_thread = threading.Thread(target=self.process_logs, daemon=True)
        processing_thread.start()
        
        stats_thread = threading.Thread(target=self.generate_processing_stats, daemon=True)
        stats_thread.start()
        
        logger.info("Log processor started")
        
        # Keep main thread alive
        try:
            while self.running:
                time.sleep(1)
        except KeyboardInterrupt:
            logger.info("Received shutdown signal")
        finally:
            self.running = False
            logger.info("Log processor shutting down")

if __name__ == '__main__':
    processor = LogProcessor()
    processor.run()