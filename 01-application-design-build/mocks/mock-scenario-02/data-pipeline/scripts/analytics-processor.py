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