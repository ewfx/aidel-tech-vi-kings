import os
from airflow.models import Variable
from dotenv import load_dotenv
import random
load_dotenv()

# Path configurations
TRANSACTION_FOLDER = os.environ.get('TRANSACTION_FOLDER', '/opt/airflow/data/transactions')
PROCESSED_FOLDER = os.environ.get('PROCESSED_FOLDER', '/opt/airflow/data/processed')
FAILED_FOLDER = os.environ.get('FAILED_FOLDER', '/opt/airflow/data/failed')
RESULTS_FOLDER = os.environ.get('RESULTS_FOLDER', '/opt/airflow/data/results')
SANCTION_DATA_FOLDER = os.environ.get('SANCTION_DATA_FOLDER', '/opt/airflow/data/sanctions')
PEP_DATA_FILE = os.environ.get('PEP_DATA_FILE', '/opt/airflow/data/pep/pep_data.csv')

# Create folders if they don't exist
for folder in [TRANSACTION_FOLDER, PROCESSED_FOLDER, FAILED_FOLDER, RESULTS_FOLDER, SANCTION_DATA_FOLDER]:
    os.makedirs(folder, exist_ok=True)

# API configurations
OPENCORPORATES_API_KEY = os.environ.get('OPENCORPORATES_API_KEY', 
                                        Variable.get("OPENCORPORATES_API_KEY", default_var=""))
OPENSANCTIONS_API_KEY = os.environ.get('OPENSANCTIONS_API_KEY', 
                                       Variable.get("OPENSANCTIONS_API_KEY", default_var=""))

class GeminiKeyRotator:
    """
    Manages rotation of Gemini API keys with multiple fallback options
    """
    def __init__(self):
        # Get keys from environment variable or Airflow variable
        keys_str = (
            os.environ.get('GEMINI_API_KEYS') or 
            Variable.get("GEMINI_API_KEYS", default_var="") or 
            ""
        )
        
        # Split keys, removing any whitespace
        self.keys = [key.strip() for key in keys_str.split(',') if key.strip()]
        
        # Fallback to single key method if no list provided
        if not self.keys:
            single_key = (
                os.environ.get('GEMINI_API_KEY') or 
                Variable.get("GEMINI_API_KEY", default_var="")
            )
            if single_key:
                self.keys = [single_key]
        
        if not self.keys:
            raise ValueError("No Gemini API keys found. Please set GEMINI_API_KEYS or GEMINI_API_KEY.")
        
        # Track key usage to help with load balancing
        self.key_usage = {key: 0 for key in self.keys}
        
    def get_key(self):
        """
        Select a key using a weighted random approach that favors less-used keys
        
        :return: A Gemini API key
        """
        if len(self.keys) == 1:
            return self.keys[0]
        
        # Find keys with minimum usage
        min_usage = min(self.key_usage.values())
        least_used_keys = [
            key for key, usage in self.key_usage.items() 
            if usage == min_usage
        ]
        
        # Randomly select from least-used keys
        selected_key = random.choice(least_used_keys)
        
        # Increment usage count
        self.key_usage[selected_key] += 1
        
        return selected_key
    
    def mark_key_failed(self, key):
        """
        Mark a key as potentially problematic
        
        :param key: The API key that failed
        """
        if key in self.key_usage:
            # Increase usage count to reduce future selection probability
            self.key_usage[key] += 10
    
    def get_key_count(self):
        """
        Get the number of available keys
        
        :return: Number of API keys
        """
        return len(self.keys)

# Global key rotator instance
gemini_key_rotator = GeminiKeyRotator()

GEMINI_MODEL = "gemini-1.5-pro"
GEMINI_TEMPERATURE = 0.3
GEMINI_TOP_P = 1
GEMINI_TOP_K = 1
GEMINI_MAX_OUTPUT_TOKENS = 8192