#!/usr/bin/env python3
import requests
import json
import csv
import os
import time
import logging
from datetime import datetime, timedelta

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class DataIngestion:
    def __init__(self, config_path="/config/ingestion-config.json"):
        with open(config_path, 'r') as f:
            self.config = json.load(f)
        
        self.output_dir = "/data/raw"
        os.makedirs(self.output_dir, exist_ok=True)
    
    def download_dataset(self, source_config):
        """Download dataset from external source"""
        source_name = source_config['name']
        url = source_config['url']
        data_format = source_config.get('format', 'json')
        
        logger.info(f"Downloading dataset: {source_name}")
        
        try:
            headers = source_config.get('headers', {})
            params = source_config.get('params', {})
            
            response = requests.get(url, headers=headers, params=params, timeout=30)
            response.raise_for_status()
            
            # Handle different data formats
            if data_format == 'json':
                data = response.json()
                output_file = os.path.join(self.output_dir, f"{source_name}.json")
                with open(output_file, 'w') as f:
                    json.dump(data, f, indent=2)
            
            elif data_format == 'csv':
                output_file = os.path.join(self.output_dir, f"{source_name}.csv")
                with open(output_file, 'w') as f:
                    f.write(response.text)
            
            else:
                output_file = os.path.join(self.output_dir, f"{source_name}.{data_format}")
                with open(output_file, 'wb') as f:
                    f.write(response.content)
            
            logger.info(f"Downloaded {source_name} to {output_file}")
            
            # Add metadata
            metadata = {
                'source': source_name,
                'url': url,
                'downloaded_at': datetime.now().isoformat(),
                'file_size': os.path.getsize(output_file),
                'format': data_format
            }
            
            metadata_file = os.path.join(self.output_dir, f"{source_name}_metadata.json")
            with open(metadata_file, 'w') as f:
                json.dump(metadata, f, indent=2)
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to download {source_name}: {str(e)}")
            return False
    
    def generate_sample_data(self, source_config):
        """Generate sample data if external source is unavailable"""
        source_name = source_config['name']
        sample_size = source_config.get('sample_size', 1000)
        
        logger.info(f"Generating sample data for: {source_name}")
        
        # Generate sample user data
        if 'users' in source_name:
            data = []
            for i in range(sample_size):
                user = {
                    'id': i + 1,
                    'name': f'User_{i+1}',
                    'email': f'user{i+1}@example.com',
                    'age': 18 + (i % 50),
                    'created_at': (datetime.now() - timedelta(days=i % 365)).isoformat(),
                    'active': i % 3 != 0
                }
                data.append(user)
        
        # Generate sample transaction data
        elif 'transactions' in source_name:
            data = []
            for i in range(sample_size):
                transaction = {
                    'id': i + 1,
                    'user_id': (i % 100) + 1,
                    'amount': round(10.0 + (i % 1000), 2),
                    'currency': 'USD',
                    'timestamp': (datetime.now() - timedelta(hours=i % 24)).isoformat(),
                    'status': 'completed' if i % 10 != 0 else 'failed'
                }
                data.append(transaction)
        
        # Default sample data
        else:
            data = [{'id': i, 'value': f'sample_{i}'} for i in range(sample_size)]
        
        output_file = os.path.join(self.output_dir, f"{source_name}.json")
        with open(output_file, 'w') as f:
            json.dump(data, f, indent=2)
        
        logger.info(f"Generated sample data: {output_file}")
        return True
    
    def run(self):
        """Execute data ingestion process"""
        logger.info("Starting data ingestion process")
        
        sources = self.config.get('sources', [])
        success_count = 0
        
        for source in sources:
            try:
                # Try to download from external source first
                if self.download_dataset(source):
                    success_count += 1
                else:
                    # Fallback to sample data generation
                    if source.get('fallback_to_sample', True):
                        if self.generate_sample_data(source):
                            success_count += 1
            
            except Exception as e:
                logger.error(f"Error processing source {source.get('name', 'unknown')}: {str(e)}")
        
        logger.info(f"Data ingestion completed. {success_count}/{len(sources)} sources processed successfully")
        
        # Create ingestion summary
        summary = {
            'timestamp': datetime.now().isoformat(),
            'total_sources': len(sources),
            'successful_sources': success_count,
            'status': 'completed' if success_count > 0 else 'failed'
        }
        
        with open('/data/ingestion-summary.json', 'w') as f:
            json.dump(summary, f, indent=2)
        
        return success_count > 0

if __name__ == "__main__":
    ingestion = DataIngestion()
    success = ingestion.run()
    exit(0 if success else 1)