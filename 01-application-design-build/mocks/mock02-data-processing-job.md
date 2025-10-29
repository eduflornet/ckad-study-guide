# Mock Scenario 2: Create a Data Processing Job

**Objective**: Design and implement a comprehensive data processing pipeline using Kubernetes Jobs
**Time**: 50 minutes
**Difficulty**: Advanced

---

## Scenario Overview

You work for a data analytics company that processes large datasets daily. The company needs a robust data processing pipeline that can:

- Download data from multiple external sources
- Validate and clean the data
- Transform data into different formats
- Generate analytics reports
- Handle failures gracefully with retry logic
- Process data in parallel for performance
- Store results in different storage systems

## Pipeline Requirements

The data processing pipeline must include:

1. **Data Ingestion**: Download datasets from external APIs
2. **Data Validation**: Verify data integrity and format
3. **Data Transformation**: Convert data formats and apply business logic
4. **Analytics Processing**: Generate statistical reports
5. **Data Export**: Store processed data in multiple formats
6. **Cleanup**: Remove temporary files and optimize storage

## Implementation Tasks

### Task 1: Create Data Processing Scripts (15 minutes)

Create the data processing scripts and configurations:

```bash
mkdir /tmp/data-pipeline
cd /tmp/data-pipeline
mkdir scripts configs data
```

Create `scripts/data-ingestion.py`:
```python
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
```

Create `scripts/data-validation.py`:
```python
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
```

Create `scripts/data-transformation.py`:
```python
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
```

### Task 2: Create Configuration Files (10 minutes)

Create `configs/ingestion-config.json`:
```json
{
  "sources": [
    {
      "name": "users",
      "url": "https://jsonplaceholder.typicode.com/users",
      "format": "json",
      "fallback_to_sample": true,
      "sample_size": 1000,
      "headers": {
        "User-Agent": "DataPipeline/1.0"
      }
    },
    {
      "name": "transactions",
      "url": "https://api.example.com/transactions",
      "format": "json",
      "fallback_to_sample": true,
      "sample_size": 5000,
      "headers": {
        "Authorization": "Bearer fake-token"
      },
      "params": {
        "limit": 5000
      }
    },
    {
      "name": "products",
      "url": "https://fakestoreapi.com/products",
      "format": "json",
      "fallback_to_sample": true,
      "sample_size": 100
    }
  ]
}
```

Create `configs/validation-config.json`:
```json
{
  "files": [
    {
      "name": "users",
      "schema": {
        "type": "array",
        "items": {
          "type": "object",
          "required": ["id", "name", "email"],
          "properties": {
            "id": {"type": "integer"},
            "name": {"type": "string"},
            "email": {"type": "string", "format": "email"}
          }
        }
      },
      "rules": {
        "min_records": 10,
        "required_fields": ["id", "name", "email"],
        "check_duplicates": true,
        "unique_field": "id"
      },
      "cleaning": {
        "remove_nulls": true,
        "standardize_fields": true,
        "transformations": {
          "name": "trim",
          "email": "lowercase"
        }
      }
    },
    {
      "name": "transactions",
      "rules": {
        "min_records": 100,
        "required_fields": ["id", "user_id", "amount"],
        "check_duplicates": true,
        "unique_field": "id"
      },
      "cleaning": {
        "remove_nulls": false,
        "standardize_fields": true
      }
    },
    {
      "name": "products",
      "rules": {
        "min_records": 10,
        "required_fields": ["id", "title"],
        "check_duplicates": true,
        "unique_field": "id"
      },
      "cleaning": {
        "remove_nulls": true,
        "standardize_fields": true,
        "transformations": {
          "title": "trim"
        }
      }
    }
  ]
}
```

Create `configs/transformation-config.json`:
```json
{
  "files": [
    {
      "name": "users",
      "transformations": [
        {
          "type": "filter",
          "conditions": [
            {
              "field": "active",
              "operator": "equals",
              "value": true
            }
          ]
        },
        {
          "type": "enrich",
          "calculated_fields": {
            "full_name": {
              "type": "concatenate",
              "fields": ["name"],
              "separator": " "
            },
            "processed_at": {
              "type": "timestamp"
            },
            "user_category": {
              "type": "constant",
              "value": "standard"
            }
          }
        }
      ]
    },
    {
      "name": "transactions",
      "transformations": [
        {
          "type": "filter",
          "conditions": [
            {
              "field": "status",
              "operator": "equals",
              "value": "completed"
            },
            {
              "field": "amount",
              "operator": "greater_than",
              "value": 0
            }
          ]
        },
        {
          "type": "aggregate",
          "group_by": ["user_id"],
          "aggregations": {
            "amount": ["sum", "mean", "count"],
            "id": ["count"]
          }
        },
        {
          "type": "enrich",
          "calculated_fields": {
            "processed_at": {
              "type": "timestamp"
            }
          }
        }
      ]
    },
    {
      "name": "products",
      "transformations": [
        {
          "type": "enrich",
          "calculated_fields": {
            "processed_at": {
              "type": "timestamp"
            },
            "category_normalized": {
              "type": "constant",
              "value": "general"
            }
          }
        }
      ]
    }
  ]
}
```

### Task 3: Create Analytics and Reporting Jobs (10 minutes)

Create `scripts/analytics-processor.py`:
```python
#!/usr/bin/env python3
import json
import os
import logging
from datetime import datetime
import pandas as pd
import numpy as np

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class AnalyticsProcessor:
    def __init__(self):
        self.input_dir = "/data/transformed"
        self.output_dir = "/data/analytics"
        os.makedirs(self.output_dir, exist_ok=True)
    
    def generate_user_analytics(self):
        """Generate user analytics report"""
        logger.info("Generating user analytics")
        
        users_file = os.path.join(self.input_dir, "transformed_users.json")
        if not os.path.exists(users_file):
            logger.warning("Users data not found for analytics")
            return False
        
        try:
            with open(users_file, 'r') as f:
                users_data = json.load(f)
            
            df = pd.DataFrame(users_data)
            
            analytics = {
                'total_users': len(df),
                'active_users': len(df[df.get('active', True) == True]) if 'active' in df.columns else len(df),
                'age_distribution': {},
                'domain_analysis': {},
                'timestamp': datetime.now().isoformat()
            }
            
            # Age distribution analysis
            if 'age' in df.columns:
                age_bins = [0, 25, 35, 45, 55, 100]
                age_labels = ['18-25', '26-35', '36-45', '46-55', '55+']
                df['age_group'] = pd.cut(df['age'], bins=age_bins, labels=age_labels, right=False)
                analytics['age_distribution'] = df['age_group'].value_counts().to_dict()
            
            # Email domain analysis
            if 'email' in df.columns:
                df['email_domain'] = df['email'].str.split('@').str[1]
                analytics['domain_analysis'] = df['email_domain'].value_counts().head(10).to_dict()
            
            # Save analytics
            output_file = os.path.join(self.output_dir, "user_analytics.json")
            with open(output_file, 'w') as f:
                json.dump(analytics, f, indent=2, default=str)
            
            logger.info("User analytics generated successfully")
            return True
            
        except Exception as e:
            logger.error(f"Error generating user analytics: {str(e)}")
            return False
    
    def generate_transaction_analytics(self):
        """Generate transaction analytics report"""
        logger.info("Generating transaction analytics")
        
        transactions_file = os.path.join(self.input_dir, "transformed_transactions.json")
        if not os.path.exists(transactions_file):
            logger.warning("Transactions data not found for analytics")
            return False
        
        try:
            with open(transactions_file, 'r') as f:
                transactions_data = json.load(f)
            
            df = pd.DataFrame(transactions_data)
            
            analytics = {
                'total_transactions': len(df),
                'revenue_metrics': {},
                'user_metrics': {},
                'timestamp': datetime.now().isoformat()
            }
            
            # Revenue analytics
            if 'amount_sum' in df.columns:
                analytics['revenue_metrics'] = {
                    'total_revenue': float(df['amount_sum'].sum()),
                    'average_revenue_per_user': float(df['amount_sum'].mean()),
                    'median_revenue_per_user': float(df['amount_sum'].median()),
                    'top_spending_users': df.nlargest(10, 'amount_sum')[['user_id', 'amount_sum']].to_dict('records')
                }
            
            # User transaction patterns
            if 'id_count' in df.columns:
                analytics['user_metrics'] = {
                    'average_transactions_per_user': float(df['id_count'].mean()),
                    'median_transactions_per_user': float(df['id_count'].median()),
                    'most_active_users': df.nlargest(10, 'id_count')[['user_id', 'id_count']].to_dict('records')
                }
            
            # Save analytics
            output_file = os.path.join(self.output_dir, "transaction_analytics.json")
            with open(output_file, 'w') as f:
                json.dump(analytics, f, indent=2, default=str)
            
            logger.info("Transaction analytics generated successfully")
            return True
            
        except Exception as e:
            logger.error(f"Error generating transaction analytics: {str(e)}")
            return False
    
    def generate_summary_report(self):
        """Generate overall summary report"""
        logger.info("Generating summary report")
        
        try:
            summary = {
                'pipeline_execution': {
                    'timestamp': datetime.now().isoformat(),
                    'status': 'completed'
                },
                'data_summary': {},
                'analytics_summary': {}
            }
            
            # Collect data summaries
            summary_files = [
                '/data/ingestion-summary.json',
                '/data/validation-summary.json',
                '/data/transformation-summary.json'
            ]
            
            for summary_file in summary_files:
                if os.path.exists(summary_file):
                    with open(summary_file, 'r') as f:
                        stage_summary = json.load(f)
                        stage_name = os.path.basename(summary_file).replace('-summary.json', '')
                        summary['data_summary'][stage_name] = stage_summary
            
            # Count processed files
            processed_files = {
                'raw_files': len([f for f in os.listdir('/data/raw') if f.endswith(('.json', '.csv'))]),
                'validated_files': len([f for f in os.listdir('/data/validated') if f.startswith('validated_')]),
                'transformed_files': len([f for f in os.listdir('/data/transformed') if f.startswith('transformed_')]),
                'analytics_files': len([f for f in os.listdir('/data/analytics') if f.endswith('.json')])
            }
            
            summary['data_summary']['file_counts'] = processed_files
            
            # Load analytics summaries
            analytics_files = [
                'user_analytics.json',
                'transaction_analytics.json'
            ]
            
            for analytics_file in analytics_files:
                analytics_path = os.path.join(self.output_dir, analytics_file)
                if os.path.exists(analytics_path):
                    with open(analytics_path, 'r') as f:
                        analytics_data = json.load(f)
                        summary['analytics_summary'][analytics_file.replace('.json', '')] = analytics_data
            
            # Save summary report
            output_file = os.path.join(self.output_dir, "pipeline_summary_report.json")
            with open(output_file, 'w') as f:
                json.dump(summary, f, indent=2, default=str)
            
            logger.info("Summary report generated successfully")
            return True
            
        except Exception as e:
            logger.error(f"Error generating summary report: {str(e)}")
            return False
    
    def run(self):
        """Execute analytics processing"""
        logger.info("Starting analytics processing")
        
        success_count = 0
        
        # Generate individual analytics
        if self.generate_user_analytics():
            success_count += 1
        
        if self.generate_transaction_analytics():
            success_count += 1
        
        # Generate summary report
        if self.generate_summary_report():
            success_count += 1
        
        logger.info(f"Analytics processing completed. {success_count} reports generated")
        return success_count > 0

if __name__ == "__main__":
    processor = AnalyticsProcessor()
    success = processor.run()
    exit(0 if success else 1)
```

### Task 4: Create Kubernetes Job Manifests (15 minutes)

Create `data-processing-job.yaml`:
```yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: ingestion-config
data:
  ingestion-config.json: |
    {
      "sources": [
        {
          "name": "users",
          "url": "https://jsonplaceholder.typicode.com/users",
          "format": "json",
          "fallback_to_sample": true,
          "sample_size": 1000
        },
        {
          "name": "transactions",
          "url": "https://api.example.com/transactions",
          "format": "json",
          "fallback_to_sample": true,
          "sample_size": 5000
        }
      ]
    }
---
apiVersion: v1
kind: ConfigMap
metadata:
  name: validation-config
data:
  validation-config.json: |
    {
      "files": [
        {
          "name": "users",
          "rules": {
            "min_records": 10,
            "required_fields": ["id", "name", "email"],
            "check_duplicates": true,
            "unique_field": "id"
          },
          "cleaning": {
            "remove_nulls": true,
            "standardize_fields": true
          }
        },
        {
          "name": "transactions", 
          "rules": {
            "min_records": 100,
            "required_fields": ["id", "user_id", "amount"],
            "check_duplicates": true,
            "unique_field": "id"
          }
        }
      ]
    }
---
apiVersion: v1
kind: ConfigMap
metadata:
  name: transformation-config
data:
  transformation-config.json: |
    {
      "files": [
        {
          "name": "users",
          "transformations": [
            {
              "type": "enrich",
              "calculated_fields": {
                "processed_at": {"type": "timestamp"}
              }
            }
          ]
        },
        {
          "name": "transactions",
          "transformations": [
            {
              "type": "filter",
              "conditions": [
                {"field": "status", "operator": "equals", "value": "completed"}
              ]
            },
            {
              "type": "aggregate",
              "group_by": ["user_id"],
              "aggregations": {
                "amount": ["sum", "mean", "count"]
              }
            }
          ]
        }
      ]
    }
---
apiVersion: v1
kind: ConfigMap
metadata:
  name: processing-scripts
data:
  data-ingestion.py: |
    # (Include the data-ingestion.py script content here)
  data-validation.py: |
    # (Include the data-validation.py script content here)  
  data-transformation.py: |
    # (Include the data-transformation.py script content here)
  analytics-processor.py: |
    # (Include the analytics-processor.py script content here)
---
# Data Ingestion Job
apiVersion: batch/v1
kind: Job
metadata:
  name: data-ingestion
  labels:
    pipeline: data-processing
    stage: ingestion
spec:
  backoffLimit: 3
  activeDeadlineSeconds: 600
  template:
    metadata:
      labels:
        pipeline: data-processing
        stage: ingestion
    spec:
      restartPolicy: Never
      containers:
      - name: ingestion
        image: python:3.11-alpine
        command:
        - sh
        - -c
        - |
          pip install requests pandas jsonschema numpy
          python /scripts/data-ingestion.py
        volumeMounts:
        - name: processing-scripts
          mountPath: /scripts
        - name: ingestion-config
          mountPath: /config
        - name: shared-data
          mountPath: /data
        resources:
          requests:
            memory: "256Mi"
            cpu: "200m"
          limits:
            memory: "512Mi"
            cpu: "500m"
      volumes:
      - name: processing-scripts
        configMap:
          name: processing-scripts
          defaultMode: 0755
      - name: ingestion-config
        configMap:
          name: ingestion-config
      - name: shared-data
        emptyDir: {}
---
# Data Validation Job (depends on ingestion)
apiVersion: batch/v1
kind: Job
metadata:
  name: data-validation
  labels:
    pipeline: data-processing
    stage: validation
spec:
  backoffLimit: 2
  activeDeadlineSeconds: 300
  template:
    metadata:
      labels:
        pipeline: data-processing
        stage: validation
    spec:
      restartPolicy: Never
      initContainers:
      - name: wait-for-ingestion
        image: busybox:1.35
        command:
        - sh
        - -c
        - |
          echo "Waiting for ingestion to complete..."
          while [ ! -f /data/ingestion-summary.json ]; do
            echo "Ingestion not complete, waiting..."
            sleep 5
          done
          echo "Ingestion completed, proceeding with validation"
        volumeMounts:
        - name: shared-data
          mountPath: /data
      containers:
      - name: validation
        image: python:3.11-alpine
        command:
        - sh
        - -c
        - |
          pip install requests pandas jsonschema numpy
          python /scripts/data-validation.py
        volumeMounts:
        - name: processing-scripts
          mountPath: /scripts
        - name: validation-config
          mountPath: /config
        - name: shared-data
          mountPath: /data
        resources:
          requests:
            memory: "256Mi"
            cpu: "200m"
          limits:
            memory: "512Mi"
            cpu: "500m"
      volumes:
      - name: processing-scripts
        configMap:
          name: processing-scripts
          defaultMode: 0755
      - name: validation-config
        configMap:
          name: validation-config
      - name: shared-data
        emptyDir: {}
---
# Data Transformation Job (depends on validation)
apiVersion: batch/v1
kind: Job
metadata:
  name: data-transformation
  labels:
    pipeline: data-processing
    stage: transformation
spec:
  backoffLimit: 2
  activeDeadlineSeconds: 300
  template:
    metadata:
      labels:
        pipeline: data-processing
        stage: transformation
    spec:
      restartPolicy: Never
      initContainers:
      - name: wait-for-validation
        image: busybox:1.35
        command:
        - sh
        - -c
        - |
          echo "Waiting for validation to complete..."
          while [ ! -f /data/validation-summary.json ]; do
            echo "Validation not complete, waiting..."
            sleep 5
          done
          echo "Validation completed, proceeding with transformation"
        volumeMounts:
        - name: shared-data
          mountPath: /data
      containers:
      - name: transformation
        image: python:3.11-alpine
        command:
        - sh
        - -c
        - |
          pip install requests pandas jsonschema numpy
          python /scripts/data-transformation.py
        volumeMounts:
        - name: processing-scripts
          mountPath: /scripts
        - name: transformation-config
          mountPath: /config
        - name: shared-data
          mountPath: /data
        resources:
          requests:
            memory: "512Mi"
            cpu: "300m"
          limits:
            memory: "1Gi"
            cpu: "600m"
      volumes:
      - name: processing-scripts
        configMap:
          name: processing-scripts
          defaultMode: 0755
      - name: transformation-config
        configMap:
          name: transformation-config
      - name: shared-data
        emptyDir: {}
---
# Analytics Processing Job (depends on transformation)
apiVersion: batch/v1
kind: Job
metadata:
  name: analytics-processing
  labels:
    pipeline: data-processing
    stage: analytics
spec:
  backoffLimit: 2
  activeDeadlineSeconds: 300
  template:
    metadata:
      labels:
        pipeline: data-processing
        stage: analytics
    spec:
      restartPolicy: Never
      initContainers:
      - name: wait-for-transformation
        image: busybox:1.35
        command:
        - sh
        - -c
        - |
          echo "Waiting for transformation to complete..."
          while [ ! -f /data/transformation-summary.json ]; do
            echo "Transformation not complete, waiting..."
            sleep 5
          done
          echo "Transformation completed, proceeding with analytics"
        volumeMounts:
        - name: shared-data
          mountPath: /data
      containers:
      - name: analytics
        image: python:3.11-alpine
        command:
        - sh
        - -c
        - |
          pip install requests pandas jsonschema numpy
          python /scripts/analytics-processor.py
        volumeMounts:
        - name: processing-scripts
          mountPath: /scripts
        - name: shared-data
          mountPath: /data
        resources:
          requests:
            memory: "512Mi"
            cpu: "300m"
          limits:
            memory: "1Gi"
            cpu: "600m"
      volumes:
      - name: processing-scripts
        configMap:
          name: processing-scripts
          defaultMode: 0755
      - name: shared-data
        emptyDir: {}
```

### Task 5: Deploy and Test the Pipeline (10 minutes)

```bash
# Apply the data processing jobs
kubectl apply -f data-processing-job.yaml

# Monitor job execution
kubectl get jobs -l pipeline=data-processing -w

# Check job details
kubectl describe job data-ingestion
kubectl describe job data-validation
kubectl describe job data-transformation
kubectl describe job analytics-processing

# Check pod logs for each stage
kubectl logs job/data-ingestion
kubectl logs job/data-validation
kubectl logs job/data-transformation
kubectl logs job/analytics-processing

# Verify data processing results
kubectl exec job/analytics-processing -- find /data -name "*.json" -type f

# Check final analytics results
kubectl exec job/analytics-processing -- cat /data/analytics/pipeline_summary_report.json

# Check resource usage
kubectl top pods -l pipeline=data-processing

# Cleanup
kubectl delete -f data-processing-job.yaml
```

## Success Criteria

- [ ] All jobs complete successfully without errors
- [ ] Data ingestion downloads or generates sample data
- [ ] Data validation identifies and cleans data quality issues  
- [ ] Data transformation applies business logic and aggregations
- [ ] Analytics processing generates meaningful reports
- [ ] Pipeline handles failures gracefully with retries
- [ ] Jobs execute in proper dependency order
- [ ] Resource limits are respected
- [ ] Final summary report is generated
- [ ] All intermediate data files are created

## Advanced Extensions

1. **Parallel Processing**: Modify jobs to process multiple data sources in parallel
2. **Error Handling**: Add comprehensive error handling and notification
3. **Data Lineage**: Track data lineage through the pipeline
4. **Monitoring**: Add Prometheus metrics and alerts
5. **Scheduling**: Convert to CronJob for automated execution

## Learning Objectives

- Complex job orchestration and dependencies
- Data processing pipeline design
- Error handling and retry strategies
- Resource management for data workloads
- Configuration management with ConfigMaps
- Job monitoring and debugging techniques