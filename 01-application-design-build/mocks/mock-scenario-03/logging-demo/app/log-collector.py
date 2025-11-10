#!/usr/bin/env python3
import json
import time
import os
import logging
import threading
from datetime import datetime
import glob
from collections import defaultdict

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger('log-collector')

class LogCollector:
    def __init__(self):
        self.log_directory = '/logs'
        self.output_directory = '/collected-logs'
        self.running = True
        self.file_positions = {}
        self.collected_logs = defaultdict(list)
        
        # Ensure output directory exists
        os.makedirs(self.output_directory, exist_ok=True)
    
    def read_log_file(self, file_path):
        """Read new lines from a log file"""
        try:
            # Get current position for this file
            current_position = self.file_positions.get(file_path, 0)
            
            with open(file_path, 'r') as f:
                f.seek(current_position)
                new_lines = f.readlines()
                self.file_positions[file_path] = f.tell()
            
            return new_lines
            
        except Exception as e:
            logger.error(f"Error reading log file {file_path}: {str(e)}")
            return []
    
    def process_log_line(self, line, source_file):
        """Process a single log line and extract metadata"""
        try:
            # Try to parse as JSON first
            if line.strip().startswith('{'):
                log_entry = json.loads(line.strip())
                log_entry['source_file'] = source_file
                log_entry['collected_at'] = datetime.now().isoformat()
                return log_entry
            else:
                # Handle plain text logs
                return {
                    'message': line.strip(),
                    'source_file': source_file,
                    'collected_at': datetime.now().isoformat(),
                    'log_level': 'INFO'  # Default level
                }
                
        except json.JSONDecodeError:
            # Not JSON, treat as plain text
            return {
                'message': line.strip(),
                'source_file': source_file,
                'collected_at': datetime.now().isoformat(),
                'log_level': 'INFO'
            }
        except Exception as e:
            logger.error(f"Error processing log line: {str(e)}")
            return None
    
    def collect_logs(self):
        """Collect logs from all log files"""
        while self.running:
            try:
                # Find all log files
                log_files = glob.glob(os.path.join(self.log_directory, '*.log'))
                
                for log_file in log_files:
                    if not os.path.exists(log_file):
                        continue
                    
                    # Read new lines from the file
                    new_lines = self.read_log_file(log_file)
                    
                    for line in new_lines:
                        if line.strip():  # Skip empty lines
                            processed_log = self.process_log_line(line, os.path.basename(log_file))
                            if processed_log:
                                # Categorize logs by source
                                source = processed_log.get('source_file', 'unknown')
                                self.collected_logs[source].append(processed_log)
                
                time.sleep(1)  # Check for new logs every second
                
            except Exception as e:
                logger.error(f"Log collection error: {str(e)}")
                time.sleep(5)
    
    def write_collected_logs(self):
        """Write collected logs to output files"""
        while self.running:
            try:
                for source, logs in self.collected_logs.items():
                    if logs:
                        # Write logs to source-specific file
                        output_file = os.path.join(self.output_directory, f"collected_{source}")
                        
                        with open(output_file, 'a') as f:
                            for log_entry in logs:
                                f.write(json.dumps(log_entry) + '\n')
                        
                        # Clear processed logs
                        self.collected_logs[source] = []
                        
                        logger.debug(f"Wrote {len(logs)} logs to {output_file}")
                
                time.sleep(5)  # Write collected logs every 5 seconds
                
            except Exception as e:
                logger.error(f"Log writing error: {str(e)}")
                time.sleep(10)
    
    def generate_collection_stats(self):
        """Generate statistics about log collection"""
        while self.running:
            try:
                stats = {
                    'timestamp': datetime.now().isoformat(),
                    'monitored_files': len(self.file_positions),
                    'file_positions': self.file_positions.copy(),
                    'pending_logs': {source: len(logs) for source, logs in self.collected_logs.items()},
                    'total_pending': sum(len(logs) for logs in self.collected_logs.values())
                }
                
                stats_file = os.path.join(self.output_directory, 'collection_stats.json')
                with open(stats_file, 'w') as f:
                    json.dump(stats, f, indent=2)
                
                logger.info(f"Collection stats: {stats['total_pending']} pending logs from {stats['monitored_files']} files")
                
                time.sleep(30)  # Update stats every 30 seconds
                
            except Exception as e:
                logger.error(f"Stats generation error: {str(e)}")
                time.sleep(60)
    
    def run(self):
        """Start the log collector"""
        logger.info("Log collector starting up")
        
        # Start collection threads
        threads = []
        
        collection_thread = threading.Thread(target=self.collect_logs, daemon=True)
        collection_thread.start()
        threads.append(collection_thread)
        
        writing_thread = threading.Thread(target=self.write_collected_logs, daemon=True)
        writing_thread.start()
        threads.append(writing_thread)
        
        stats_thread = threading.Thread(target=self.generate_collection_stats, daemon=True)
        stats_thread.start()
        threads.append(stats_thread)
        
        logger.info("Log collector started")
        
        # Keep main thread alive
        try:
            while self.running:
                time.sleep(1)
        except KeyboardInterrupt:
            logger.info("Received shutdown signal")
        finally:
            self.running = False
            logger.info("Log collector shutting down")

if __name__ == '__main__':
    collector = LogCollector()
    collector.run()