import os
import json
import logging
from typing import Dict, List, Any, Optional, Union

from utils.knowledge_base_utils import initialize_knowledge_base

logger = logging.getLogger(__name__)

def get_transaction_folder(results_folder: str, transaction_id: str) -> str:
    """
    Get the path to the transaction folder, creating it if it doesn't exist.
    Uses the knowledge base folder structure.
    
    Args:
        results_folder: Base results folder path
        transaction_id: The transaction ID
        
    Returns:
        The path to the transaction folder
    """
    transaction_folder = os.path.join(results_folder, transaction_id)
    
    # Create the transaction folder if it doesn't exist using the knowledge base structure
    if not os.path.exists(transaction_folder):
        logger.info(f"Creating transaction folder with knowledge base structure: {transaction_folder}")
        transaction_folder = initialize_knowledge_base(results_folder, transaction_id)
    
    return transaction_folder

def save_transaction_data(results_folder: str, transaction_id: str, 
                        file_name: str, data: Any, subfolder: Optional[str] = None) -> str:
    """
    Save data to a file in the transaction folder.
    
    Args:
        results_folder: Base results folder path
        transaction_id: The transaction ID
        file_name: The name of the file to save
        data: The data to save (will be JSON serialized)
        subfolder: Optional subfolder within the transaction folder
        
    Returns:
        The path to the saved file
    """
    transaction_folder = get_transaction_folder(results_folder, transaction_id)
    
    # Map common subfolders to knowledge base structure
    kb_subfolder_mapping = {
        "organization_results/opencorporates": "entity_data/organization_results/opencorporates",
        "organization_results/sanctions": "entity_data/organization_results/sanctions",
        "organization_results/wikidata": "entity_data/organization_results/wikidata",
        "organization_results/news": "entity_data/organization_results/news",
        "people_results/pep": "entity_data/people_results/pep",
        "people_results/sanctions": "entity_data/people_results/sanctions",
        "people_results/news": "entity_data/people_results/news",
        "organization_results": "entity_data/organization_results",
        "people_results": "entity_data/people_results"
    }
    
    # Map common root files to knowledge base structure
    kb_file_mapping = {
        "entities.json": "entity_data/entities.json",
        "risk_assessment.json": "risk_assessments/risk_assessment.json",
        "raw_assessment_data.json": "analysis_reports/raw_assessment_data.json",
        "entity_history.json": "analysis_reports/entity_history.json",
        "wikidata_discovered_people.json": "entity_data/wikidata_discovered_people.json"
    }
    
    # If subfolder is specified, check if it has a knowledge base mapping
    if subfolder:
        if subfolder in kb_subfolder_mapping:
            subfolder = kb_subfolder_mapping[subfolder]
        save_folder = os.path.join(transaction_folder, subfolder)
    else:
        # If no subfolder but file has a mapping
        if file_name in kb_file_mapping:
            mapped_path = kb_file_mapping[file_name]
            save_folder = os.path.join(transaction_folder, os.path.dirname(mapped_path))
            file_name = os.path.basename(mapped_path)
        else:
            save_folder = transaction_folder
    
    # Ensure the save folder exists
    os.makedirs(save_folder, exist_ok=True)
    
    file_path = os.path.join(save_folder, file_name)
    
    # Save the data
    with open(file_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2)
    
    logger.info(f"Saved transaction data to: {file_path}")
    
    return file_path

def load_transaction_data(results_folder: str, transaction_id: str, 
                        file_name: str, subfolder: Optional[str] = None) -> Optional[Dict]:
    """
    Load data from a file in the transaction folder.
    
    Args:
        results_folder: Base results folder path
        transaction_id: The transaction ID
        file_name: The name of the file to load
        subfolder: Optional subfolder within the transaction folder
        
    Returns:
        The loaded data, or None if the file doesn't exist
    """
    transaction_folder = os.path.join(results_folder, transaction_id)
    
    # If the transaction folder doesn't exist, return None
    if not os.path.exists(transaction_folder):
        return None
    
    # Map common subfolders to knowledge base structure
    kb_subfolder_mapping = {
        "organization_results/opencorporates": "entity_data/organization_results/opencorporates",
        "organization_results/sanctions": "entity_data/organization_results/sanctions",
        "organization_results/wikidata": "entity_data/organization_results/wikidata",
        "organization_results/news": "entity_data/organization_results/news",
        "people_results/pep": "entity_data/people_results/pep",
        "people_results/sanctions": "entity_data/people_results/sanctions",
        "people_results/news": "entity_data/people_results/news",
        "organization_results": "entity_data/organization_results",
        "people_results": "entity_data/people_results"
    }
    
    # Map common root files to knowledge base structure
    kb_file_mapping = {
        "entities.json": "entity_data/entities.json",
        "risk_assessment.json": "risk_assessments/risk_assessment.json",
        "raw_assessment_data.json": "analysis_reports/raw_assessment_data.json",
        "entity_history.json": "analysis_reports/entity_history.json",
        "wikidata_discovered_people.json": "entity_data/wikidata_discovered_people.json"
    }
    
    # First try with the new structure
    if subfolder:
        if subfolder in kb_subfolder_mapping:
            new_subfolder = kb_subfolder_mapping[subfolder]
            new_load_folder = os.path.join(transaction_folder, new_subfolder)
            new_file_path = os.path.join(new_load_folder, file_name)
            
            if os.path.exists(new_file_path):
                try:
                    with open(new_file_path, 'r', encoding='utf-8') as f:
                        return json.load(f)
                except Exception:
                    pass
    
    # If no subfolder but file might be in new location
    if not subfolder and file_name in kb_file_mapping:
        new_path = os.path.join(transaction_folder, kb_file_mapping[file_name])
        if os.path.exists(new_path):
            try:
                with open(new_path, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception:
                pass
    
    # Fall back to the old structure
    if subfolder:
        load_folder = os.path.join(transaction_folder, subfolder)
    else:
        load_folder = transaction_folder
    
    file_path = os.path.join(load_folder, file_name)
    
    # Check if the file exists
    if not os.path.exists(file_path):
        return None
    
    # Load the data
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        return data
    except Exception as e:
        logger.warning(f"Error loading transaction data from {file_path}: {str(e)}")
        return None

def list_transaction_results(results_folder: str) -> List[str]:
    """
    List all transaction folders in the results folder.
    
    Args:
        results_folder: Base results folder path
        
    Returns:
        List of transaction IDs
    """
    if not os.path.exists(results_folder):
        return []
    
    # Get all subdirectories that could be transaction folders
    transaction_ids = []
    for item in os.listdir(results_folder):
        item_path = os.path.join(results_folder, item)
        if os.path.isdir(item_path) and not item.startswith('.'):
            # Check if it has the expected structure
            if (os.path.exists(os.path.join(item_path, "entity_data")) or
                os.path.exists(os.path.join(item_path, "risk_assessments")) or
                os.path.exists(os.path.join(item_path, "organization_results")) or
                os.path.exists(os.path.join(item_path, "people_results")) or
                any(f.endswith('.json') for f in os.listdir(item_path) if os.path.isfile(os.path.join(item_path, f)))):
                transaction_ids.append(item)
    
    return transaction_ids