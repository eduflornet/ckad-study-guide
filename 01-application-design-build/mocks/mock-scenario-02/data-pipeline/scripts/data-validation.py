#!/usr/bin/env python3
import json
import csv
import os
import logging
from datetime import datetime
import pandas as pd
from jsonschema import validate, ValidationError

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class DataValidator:
    def __init__(self, config_path="/config/validation-config.json"):
        with open(config_path, 'r') as f:
            self.config = json.load(f)
        
        self.input_dir = "/data/raw"
        self.output_dir = "/data/validated"
        os.makedirs(self.output_dir, exist_ok=True)
    
    def validate_json_schema(self, data, schema):
        """Validate JSON data against schema"""
        try:
            validate(instance=data, schema=schema)
            return True, []
        except ValidationError as e:
            return False, [str(e)]
    
    def validate_data_quality(self, data, rules):
        """Validate data quality based on rules"""
        errors = []
        
        if not isinstance(data, list):
            errors.append("Data must be a list of records")
            return False, errors
        
        if len(data) == 0:
            errors.append("Dataset is empty")
            return False, errors
        
        # Check minimum record count
        min_records = rules.get('min_records', 1)
        if len(data) < min_records:
            errors.append(f"Dataset has {len(data)} records, minimum required: {min_records}")
        
        # Validate individual records
        required_fields = rules.get('required_fields', [])
        for i, record in enumerate(data[:100]):  # Check first 100 records
            for field in required_fields:
                if field not in record or record[field] is None:
                    errors.append(f"Record {i}: Missing required field '{field}'")
        
        # Check for duplicates if specified
        if rules.get('check_duplicates', False):
            unique_field = rules.get('unique_field', 'id')
            seen_values = set()
            for i, record in enumerate(data):
                if unique_field in record:
                    value = record[unique_field]
                    if value in seen_values:
                        errors.append(f"Record {i}: Duplicate value '{value}' for field '{unique_field}'")
                    seen_values.add(value)
        
        return len(errors) == 0, errors
    
    def clean_data(self, data, cleaning_rules):
        """Clean data based on cleaning rules"""
        if not isinstance(data, list):
            return data
        
        cleaned_data = []
        
        for record in data:
            cleaned_record = record.copy()
            
            # Remove null values if specified
            if cleaning_rules.get('remove_nulls', False):
                cleaned_record = {k: v for k, v in cleaned_record.items() if v is not None}
            
            # Standardize field names
            if cleaning_rules.get('standardize_fields', False):
                standardized = {}
                for k, v in cleaned_record.items():
                    new_key = k.lower().replace(' ', '_').replace('-', '_')
                    standardized[new_key] = v
                cleaned_record = standardized
            
            # Apply field transformations
            transformations = cleaning_rules.get('transformations', {})
            for field, transform in transformations.items():
                if field in cleaned_record:
                    if transform == 'trim':
                        if isinstance(cleaned_record[field], str):
                            cleaned_record[field] = cleaned_record[field].strip()
                    elif transform == 'uppercase':
                        if isinstance(cleaned_record[field], str):
                            cleaned_record[field] = cleaned_record[field].upper()
                    elif transform == 'lowercase':
                        if isinstance(cleaned_record[field], str):
                            cleaned_record[field] = cleaned_record[field].lower()
            
            cleaned_data.append(cleaned_record)
        
        return cleaned_data
    
    def validate_file(self, filename):
        """Validate a single data file"""
        logger.info(f"Validating file: {filename}")
        
        input_path = os.path.join(self.input_dir, filename)
        
        if not os.path.exists(input_path):
            logger.error(f"Input file not found: {input_path}")
            return False
        
        # Find validation config for this file
        file_config = None
        for config in self.config.get('files', []):
            if config['name'] in filename:
                file_config = config
                break
        
        if not file_config:
            logger.warning(f"No validation config found for {filename}, using default")
            file_config = {'name': filename, 'rules': {}}
        
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
            
            # Validate schema if provided
            schema = file_config.get('schema')
            if schema:
                is_valid, schema_errors = self.validate_json_schema(data, schema)
                if not is_valid:
                    logger.error(f"Schema validation failed for {filename}: {schema_errors}")
                    return False
            
            # Validate data quality
            rules = file_config.get('rules', {})
            is_valid, quality_errors = self.validate_data_quality(data, rules)
            if not is_valid:
                logger.warning(f"Data quality issues in {filename}: {quality_errors}")
            
            # Clean data
            cleaning_rules = file_config.get('cleaning', {})
            cleaned_data = self.clean_data(data, cleaning_rules)
            
            # Save validated and cleaned data
            output_filename = f"validated_{filename}"
            output_path = os.path.join(self.output_dir, output_filename)
            
            if filename.endswith('.json'):
                with open(output_path, 'w') as f:
                    json.dump(cleaned_data, f, indent=2)
            elif filename.endswith('.csv'):
                df = pd.DataFrame(cleaned_data)
                df.to_csv(output_path, index=False)
            
            logger.info(f"Validation completed for {filename} -> {output_filename}")
            
            # Create validation report
            report = {
                'file': filename,
                'original_records': len(data) if isinstance(data, list) else 1,
                'validated_records': len(cleaned_data) if isinstance(cleaned_data, list) else 1,
                'schema_valid': schema is None or is_valid,
                'quality_errors': quality_errors,
                'timestamp': datetime.now().isoformat()
            }
            
            report_path = os.path.join(self.output_dir, f"{filename}_validation_report.json")
            with open(report_path, 'w') as f:
                json.dump(report, f, indent=2)
            
            return True
            
        except Exception as e:
            logger.error(f"Error validating {filename}: {str(e)}")
            return False
    
    def run(self):
        """Execute data validation process"""
        logger.info("Starting data validation process")
        
        if not os.path.exists(self.input_dir):
            logger.error(f"Input directory not found: {self.input_dir}")
            return False
        
        # Get all data files
        data_files = [f for f in os.listdir(self.input_dir) 
                     if f.endswith(('.json', '.csv')) and not f.endswith('_metadata.json')]
        
        if not data_files:
            logger.error("No data files found for validation")
            return False
        
        success_count = 0
        for filename in data_files:
            if self.validate_file(filename):
                success_count += 1
        
        logger.info(f"Data validation completed. {success_count}/{len(data_files)} files validated successfully")
        
        # Create validation summary
        summary = {
            'timestamp': datetime.now().isoformat(),
            'total_files': len(data_files),
            'successful_validations': success_count,
            'status': 'completed' if success_count > 0 else 'failed'
        }
        
        with open('/data/validation-summary.json', 'w') as f:
            json.dump(summary, f, indent=2)
        
        return success_count > 0

if __name__ == "__main__":
    validator = DataValidator()
    success = validator.run()
    exit(0 if success else 1)