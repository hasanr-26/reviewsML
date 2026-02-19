"""
Utility functions for data processing
"""
import json
import logging
import pandas as pd
from typing import List, Dict, Generator
from pathlib import Path

logger = logging.getLogger(__name__)

class DataImporter:
    """Import reviews from various formats"""
    
    @staticmethod
    def import_jsonl(filepath: str) -> Generator[Dict, None, None]:
        """Import reviews from JSONL file"""
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                for line_num, line in enumerate(f, 1):
                    if line.strip():
                        try:
                            yield json.loads(line)
                        except json.JSONDecodeError as e:
                            logger.error(f"JSON error at line {line_num} in {filepath}: {e}")
                            continue
        except Exception as e:
            logger.error(f"Error reading JSONL file {filepath}: {e}")
            raise
    
    @staticmethod
    def import_csv(filepath: str) -> Generator[Dict, None, None]:
        """Import reviews from CSV file"""
        try:
            df = pd.read_csv(filepath)
            for _, row in df.iterrows():
                yield row.to_dict()
        except Exception as e:
            logger.error(f"Error reading CSV file {filepath}: {e}")
            raise
    
    @staticmethod
    def import_json(filepath: str) -> Generator[Dict, None, None]:
        """Import reviews from JSON array file"""
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                data = json.load(f)
                if isinstance(data, list):
                    for item in data:
                        yield item
                else:
                    logger.error(f"JSON file {filepath} should contain an array")
                    raise ValueError("JSON file must contain an array of reviews")
        except Exception as e:
            logger.error(f"Error reading JSON file {filepath}: {e}")
            raise
    
    @staticmethod
    def import_file(filepath: str, file_format: str) -> Generator[Dict, None, None]:
        """Import reviews from file based on format"""
        file_format = file_format.lower()
        
        if file_format == 'jsonl':
            return DataImporter.import_jsonl(filepath)
        elif file_format == 'csv':
            return DataImporter.import_csv(filepath)
        elif file_format == 'json':
            return DataImporter.import_json(filepath)
        else:
            raise ValueError(f"Unsupported format: {file_format}")

class DataExporter:
    """Export analysis results to CSV and other formats"""
    
    @staticmethod
    def export_enriched_csv(reviews_enriched: List[Dict], filepath: str) -> str:
        """Export enriched review data to CSV"""
        try:
            # Flatten the data for CSV export
            rows = []
            for review in reviews_enriched:
                row = {
                    'review_id': review['review_id'],
                    'hotel_id': review['hotel_id'],
                    'rating': review['rating'],
                    'publish_decision': review['publish_decision'],
                    'rejection_reasons': '; '.join(review['rejection_reasons']) if review['rejection_reasons'] else '',
                    'tags': '; '.join(review['tags']) if review['tags'] else '',
                    'sentiment': review['sentiment'],
                    'summary': review['summary'],
                    'review_text': review['review_text'][:500]  # Limit to 500 chars for CSV
                }
                rows.append(row)
            
            df = pd.DataFrame(rows)
            df.to_csv(filepath, index=False, encoding='utf-8')
            logger.info(f"Exported {len(reviews_enriched)} enriched reviews to CSV: {filepath}")
            return filepath
        except Exception as e:
            logger.error(f"Failed to export enriched CSV: {e}")
            raise
    
    @staticmethod
    def export_summary_json(summary_data: Dict, filepath: str) -> str:
        """Export summary report to JSON"""
        try:
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(summary_data, f, indent=2, ensure_ascii=False)
            logger.info(f"Exported summary report to JSON: {filepath}")
            return filepath
        except Exception as e:
            logger.error(f"Failed to export summary JSON: {e}")
            raise

class FileManager:
    """Manage file operations"""
    
    @staticmethod
    def ensure_data_dir():
        """Ensure data directory exists"""
        Path("data").mkdir(exist_ok=True)
    
    @staticmethod
    def ensure_exports_dir():
        """Ensure exports directory exists"""
        Path("exports").mkdir(exist_ok=True)
    
    @staticmethod
    def get_export_path(filename: str) -> str:
        """Get full path for export file"""
        FileManager.ensure_exports_dir()
        return f"exports/{filename}"

def validate_review_input(review_dict: Dict) -> bool:
    """Validate review input data"""
    required_fields = ['review_id', 'hotel_id', 'rating', 'review_text']
    
    for field in required_fields:
        if field not in review_dict:
            logger.warning(f"Missing required field: {field}")
            return False
    
    if not isinstance(review_dict['rating'], (int, float)):
        logger.warning("Rating must be numeric")
        return False
    
    if not (1 <= review_dict['rating'] <= 5):
        logger.warning("Rating must be between 1 and 5")
        return False
    
    if not review_dict['review_text'] or len(str(review_dict['review_text']).strip()) < 5:
        logger.warning("Review text too short")
        return False
    
    return True
