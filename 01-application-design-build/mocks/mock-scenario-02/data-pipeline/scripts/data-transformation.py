#!/usr/bin/env python3
import json
import csv
import os
import logging
from datetime import datetime
import pandas as pd
import numpy as np

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class DataTransformer:
    def __init__(self, config_path="/config/transformation-config.json"):
        with open(config_path, 'r') as f:
            self.config = json.load(f)
        
        self.input_dir = "/data/validated"
        self.output_dir = "/data/transformed"
        os.makedirs(self.output_dir, exist_ok=True)
    
    def aggregate_data(self, data, aggregation_config):
        """Aggregate data based on configuration"""
        if not isinstance(data, list) or not data:
            return []
        
        df = pd.DataFrame(data)
        
        group_by = aggregation_config.get('group_by', [])
        if not group_by:
            return data
        
        aggregations = aggregation_config.get('aggregations', {})
        
        try:
            grouped = df.groupby(group_by)
            result = grouped.agg(aggregations).reset_index()
            
            # Flatten column names if needed
            if isinstance(result.columns, pd.MultiIndex):
                result.columns = ['_'.join(col).strip() if col[1] else col[0] for col in result.columns]
            
            return result.to_dict('records')
        
        except Exception as e:
            logger.error(f"Aggregation failed: {str(e)}")
            return data
    
    def filter_data(self, data, filter_config):
        """Filter data based on conditions"""
        if not isinstance(data, list) or not data:
            return []
        
        df = pd.DataFrame(data)
        
        conditions = filter_config.get('conditions', [])
        for condition in conditions:
            field = condition.get('field')
            operator = condition.get('operator')
            value = condition.get('value')
            
            if field not in df.columns:
                continue
            
            try:
                if operator == 'equals':
                    df = df[df[field] == value]
                elif operator == 'not_equals':
                    df = df[df[field] != value]
                elif operator == 'greater_than':
                    df = df[df[field] > value]
                elif operator == 'less_than':
                    df = df[df[field] < value]
                elif operator == 'contains':
                    df = df[df[field].astype(str).str.contains(str(value), na=False)]
                elif operator == 'in':
                    df = df[df[field].isin(value)]
                elif operator == 'not_null':
                    df = df[df[field].notna()]
            
            except Exception as e:
                logger.warning(f"Filter condition failed: {condition}, error: {str(e)}")
        
        return df.to_dict('records')
    
    def enrich_data(self, data, enrichment_config):
        """Enrich data with calculated fields"""
        if not isinstance(data, list) or not data:
            return []
        
        enriched_data = []
        
        for record in data:
            enriched_record = record.copy()
            
            # Add calculated fields
            calculated_fields = enrichment_config.get('calculated_fields', {})
            for field_name, calculation in calculated_fields.items():
                try:
                    if calculation['type'] == 'concatenate':
                        fields = calculation['fields']
                        separator = calculation.get('separator', ' ')
                        values = [str(record.get(f, '')) for f in fields]
                        enriched_record[field_name] = separator.join(values)
                    
                    elif calculation['type'] == 'arithmetic':
                        field1 = record.get(calculation['field1'], 0)
                        field2 = record.get(calculation['field2'], 0)
                        operation = calculation['operation']
                        
                        if operation == 'add':
                            enriched_record[field_name] = field1 + field2
                        elif operation == 'subtract':
                            enriched_record[field_name] = field1 - field2
                        elif operation == 'multiply':
                            enriched_record[field_name] = field1 * field2
                        elif operation == 'divide' and field2 != 0:
                            enriched_record[field_name] = field1 / field2
                    
                    elif calculation['type'] == 'timestamp':
                        enriched_record[field_name] = datetime.now().isoformat()
                    
                    elif calculation['type'] == 'constant':
                        enriched_record[field_name] = calculation['value']
                
                except Exception as e:
                    logger.warning(f"Enrichment calculation failed for {field_name}: {str(e)}")
            
            enriched_data.append(enriched_record)
        
        return enriched_data
    
    def transform_file(self, filename):
        """Transform a single data file"""
        logger.info(f"Transforming file: {filename}")
        
        input_path = os.path.join(self.input_dir, filename)
        
        if not os.path.exists(input_path):
            logger.error(f"Input file not found: {input_path}")
            return False
        
        # Find transformation config for this file
        file_config = None
        for config in self.config.get('files', []):
            if config['name'] in filename:
                file_config = config
                break
        
        if not file_config:
            logger.warning(f"No transformation config found for {filename}, using default")
            file_config = {'name': filename, 'transformations': []}
        
        try:
            # Load data
            if filename.endswith('.json'):
                with open(input_path, 'r') as f:
                    data = json.load(f)
            elif filename.endswith('.csv'):
                df = pd.read_csv(input_path)
                data = df.to_dict('records')
            else:
                logger.warning(f"Unsupported file format: {filename}")
                return False
            
            # Apply transformations
            transformations = file_config.get('transformations', [])
            for transformation in transformations:
                transform_type = transformation.get('type')
                
                if transform_type == 'filter':
                    data = self.filter_data(data, transformation)
                elif transform_type == 'aggregate':
                    data = self.aggregate_data(data, transformation)
                elif transform_type == 'enrich':
                    data = self.enrich_data(data, transformation)
            
            # Save transformed data in multiple formats
            base_name = filename.replace('validated_', '').replace('.json', '').replace('.csv', '')
            
            # JSON format
            json_output = os.path.join(self.output_dir, f"transformed_{base_name}.json")
            with open(json_output, 'w') as f:
                json.dump(data, f, indent=2)
            
            # CSV format
            if data:
                df = pd.DataFrame(data)
                csv_output = os.path.join(self.output_dir, f"transformed_{base_name}.csv")
                df.to_csv(csv_output, index=False)
            
            logger.info(f"Transformation completed for {filename}")
            
            # Create transformation report
            report = {
                'file': filename,
                'input_records': len(data) if isinstance(data, list) else 1,
                'output_records': len(data) if isinstance(data, list) else 1,
                'transformations_applied': len(transformations),
                'timestamp': datetime.now().isoformat()
            }
            
            report_path = os.path.join(self.output_dir, f"{base_name}_transformation_report.json")
            with open(report_path, 'w') as f:
                json.dump(report, f, indent=2)
            
            return True
            
        except Exception as e:
            logger.error(f"Error transforming {filename}: {str(e)}")
            return False
    
    def run(self):
        """Execute data transformation process"""
        logger.info("Starting data transformation process")
        
        if not os.path.exists(self.input_dir):
            logger.error(f"Input directory not found: {self.input_dir}")
            return False
        
        # Get all validated data files
        data_files = [f for f in os.listdir(self.input_dir) 
                     if f.startswith('validated_') and f.endswith(('.json', '.csv'))]
        
        if not data_files:
            logger.error("No validated data files found for transformation")
            return False
        
        success_count = 0
        for filename in data_files:
            if self.transform_file(filename):
                success_count += 1
        
        logger.info(f"Data transformation completed. {success_count}/{len(data_files)} files transformed successfully")
        
        # Create transformation summary
        summary = {
            'timestamp': datetime.now().isoformat(),
            'total_files': len(data_files),
            'successful_transformations': success_count,
            'status': 'completed' if success_count > 0 else 'failed'
        }
        
        with open('/data/transformation-summary.json', 'w') as f:
            json.dump(summary, f, indent=2)
        
        return success_count > 0

if __name__ == "__main__":
    transformer = DataTransformer()
    success = transformer.run()
    exit(0 if success else 1)