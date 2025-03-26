"""
Transaction folder utilities for organizing and managing transaction data.

This module provides functions for creating, reading, and listing transaction folders.
Each transaction is stored in its own folder with a standardized structure.
"""
import os
import json
import logging
from typing import Dict, List, Any, Optional

logger = logging.getLogger(__name__)

def get_transaction_folder(results_folder: str, transaction_id: str) -> str:
    """
    Get the path to the transaction folder, creating it if it doesn't exist.
    
    Args:
        results_folder: Base results folder path
        transaction_id: The transaction ID
        
    Returns:
        The path to the transaction folder
    """
    transaction_folder = os.path.join(results_folder, transaction_id)
    
    # Create the transaction folder if it doesn't exist
    if not os.path.exists(transaction_folder):
        logger.info(f"Creating transaction folder: {transaction_folder}")
        os.makedirs(transaction_folder, exist_ok=True)
        
        # Create subdirectories for organization and people results
        os.makedirs(os.path.join(transaction_folder, "organization_results", "opencorporates"), exist_ok=True)
        os.makedirs(os.path.join(transaction_folder, "organization_results", "sanctions"), exist_ok=True)
        os.makedirs(os.path.join(transaction_folder, "organization_results", "wikidata"), exist_ok=True)
        os.makedirs(os.path.join(transaction_folder, "organization_results", "news"), exist_ok=True)
        
        os.makedirs(os.path.join(transaction_folder, "people_results", "pep"), exist_ok=True)
        os.makedirs(os.path.join(transaction_folder, "people_results", "sanctions"), exist_ok=True)
        os.makedirs(os.path.join(transaction_folder, "people_results", "news"), exist_ok=True)
    
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
    
    # If subfolder is specified, add it to the path
    if subfolder:
        save_folder = os.path.join(transaction_folder, subfolder)
        os.makedirs(save_folder, exist_ok=True)
    else:
        save_folder = transaction_folder
    
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
    
    # If subfolder is specified, add it to the path
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
            if (os.path.exists(os.path.join(item_path, "organization_results")) or
                os.path.exists(os.path.join(item_path, "people_results")) or
                any(f.endswith('.json') for f in os.listdir(item_path) if os.path.isfile(os.path.join(item_path, f)))):
                transaction_ids.append(item)
    
    return transaction_ids