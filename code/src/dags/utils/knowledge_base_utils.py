import os
import json
import logging
import shutil
from typing import Dict, List
from datetime import datetime

# Configure logging
logger = logging.getLogger(__name__)


class KnowledgeBaseFolderStructure:
    """
    Manages the organization of knowledge base folders for AML risk assessment results.
    """

    # Define the standard folder structure with friendly names
    FOLDER_STRUCTURE = {
        "entity_data": {
            "display_name": "Entity Information",
            "subfolders": {
                "organization_results": {
                    "display_name": "Organizations",
                    "subfolders": {
                        "opencorporates": {"display_name": "Corporate Registry"},
                        "sanctions": {"display_name": "Sanctions Screening"},
                        "wikidata": {"display_name": "Entity Network"},
                        "news": {"display_name": "Adverse Media"},
                    },
                },
                "people_results": {
                    "display_name": "People",
                    "subfolders": {
                        "pep": {"display_name": "Politically Exposed Persons"},
                        "sanctions": {"display_name": "Sanctions Screening"},
                        "news": {"display_name": "Adverse Media"},
                    },
                },
            },
        },
        "analysis_reports": {"display_name": "Analysis Reports", "subfolders": {}},
        "risk_assessments": {"display_name": "Risk Assessments", "subfolders": {}},
    }

    def __init__(self, results_folder: str):
        """
        Initialize with the base results folder path.

        Args:
            results_folder: Base path for transaction results
        """
        self.results_folder = results_folder

    def create_transaction_folder_structure(self, transaction_id: str) -> str:
        """
        Create a well-structured folder hierarchy for a transaction with user-friendly display names.

        Args:
            transaction_id: The ID of the transaction

        Returns:
            The path to the transaction folder
        """
        transaction_folder = os.path.join(self.results_folder, transaction_id)

        # Create the base transaction folder if it doesn't exist
        if not os.path.exists(transaction_folder):
            logger.info(f"Creating transaction folder: {transaction_folder}")
            os.makedirs(transaction_folder, exist_ok=True)

            # Create metadata file with folder descriptions
            self._create_folder_metadata(transaction_folder)

        # Create the structured subfolder hierarchy
        self._create_folder_hierarchy(transaction_folder)

        return transaction_folder

    def _create_folder_hierarchy(
        self, base_folder: str, structure: Dict = None, parent_path: str = ""
    ):
        """
        Recursively create the folder hierarchy based on the defined structure.

        Args:
            base_folder: The base folder where to create the structure
            structure: The structure definition (defaults to FOLDER_STRUCTURE)
            parent_path: Path relative to base_folder for nested calls
        """
        if structure is None:
            structure = self.FOLDER_STRUCTURE

        for folder_name, folder_info in structure.items():
            folder_path = os.path.join(base_folder, parent_path, folder_name)

            # Create folder if it doesn't exist
            if not os.path.exists(folder_path):
                os.makedirs(folder_path, exist_ok=True)

                # Create a .metadata.json file with display information
                metadata_file = os.path.join(folder_path, ".metadata.json")
                with open(metadata_file, "w", encoding="utf-8") as f:
                    json.dump(
                        {
                            "display_name": folder_info.get(
                                "display_name", folder_name
                            ),
                            "description": folder_info.get("description", ""),
                            "created_at": datetime.now().isoformat(),
                        },
                        f,
                        indent=2,
                    )

            # Process subfolders if any
            if "subfolders" in folder_info and folder_info["subfolders"]:
                new_parent = (
                    os.path.join(parent_path, folder_name)
                    if parent_path
                    else folder_name
                )
                self._create_folder_hierarchy(
                    base_folder, folder_info["subfolders"], new_parent
                )

    def _create_folder_metadata(self, folder_path: str) -> None:
        """
        Create a metadata file for the transaction folder with display information.

        Args:
            folder_path: Path to the folder
        """
        metadata_file = os.path.join(folder_path, ".metadata.json")

        # Extract transaction ID from the folder path
        transaction_id = os.path.basename(folder_path)

        metadata = {
            "transaction_id": transaction_id,
            "display_name": f"Transaction {transaction_id}",
            "description": "AML Risk Assessment results and supporting data",
            "created_at": datetime.now().isoformat(),
            "folder_structure": {
                k: {
                    "display_name": v["display_name"],
                    "description": v.get("description", ""),
                }
                for k, v in self.FOLDER_STRUCTURE.items()
            },
        }

        with open(metadata_file, "w", encoding="utf-8") as f:
            json.dump(metadata, f, indent=2)

    def migrate_existing_transaction(self, transaction_id: str) -> bool:
        """
        Migrate an existing transaction folder to the new structure.

        Args:
            transaction_id: The ID of the transaction

        Returns:
            Success status as boolean
        """
        try:
            # Get source and target paths
            source_folder = os.path.join(self.results_folder, transaction_id)

            if not os.path.exists(source_folder):
                logger.warning(f"Transaction folder {transaction_id} not found")
                return False

            # Create the new folder structure
            self.create_transaction_folder_structure(transaction_id)

            # Move files to appropriate locations in the new structure
            self._migrate_files(source_folder, transaction_id)

            logger.info(
                f"Successfully migrated transaction {transaction_id} to new folder structure"
            )
            return True

        except Exception as e:
            logger.error(f"Error migrating transaction {transaction_id}: {str(e)}")
            return False

    def _migrate_files(self, source_folder: str, transaction_id: str) -> None:
        """
        Move existing files to their appropriate locations in the new structure and remove the original files.

        Args:
            source_folder: Original transaction folder
            transaction_id: Transaction ID
        """
        # Map of original paths to new paths
        path_mappings = {
            # Root transaction files
            "transaction.txt": "entity_data/transaction.txt",
            "entities.json": "entity_data/entities.json",
            "risk_assessment.json": "risk_assessments/risk_assessment.json",
            "raw_assessment_data.json": "analysis_reports/raw_assessment_data.json",
            "entity_history.json": "analysis_reports/entity_history.json",
            "wikidata_discovered_people.json": "entity_data/wikidata_discovered_people.json",
            # Keep the original organization and people folders structure
            "organization_results": "entity_data/organization_results",
            "people_results": "entity_data/people_results",
        }

        # Process each mapping
        for orig_path, new_path in path_mappings.items():
            source_path = os.path.join(source_folder, orig_path)
            target_path = os.path.join(source_folder, new_path)

            # Skip if the source doesn't exist
            if not os.path.exists(source_path):
                continue

            # Ensure target directory exists
            os.makedirs(os.path.dirname(target_path), exist_ok=True)

            # If it's a file, move it
            if os.path.isfile(source_path):
                # Copy the file to new location if it doesn't already exist
                if not os.path.exists(target_path):
                    shutil.copy2(source_path, target_path)
                # Remove the original file
                os.remove(source_path)

            # If it's a directory, move its contents
            elif os.path.isdir(source_path) and not os.path.exists(target_path):
                shutil.copytree(source_path, target_path)
                # Remove the original directory
                shutil.rmtree(source_path)


def get_display_name_from_path(path: str) -> str:
    """
    Get a user-friendly display name from a folder path or filename.

    Args:
        path: The folder path or filename

    Returns:
        A user-friendly display name
    """
    # Check if it's a folder with metadata
    metadata_path = os.path.join(path, ".metadata.json")
    if os.path.isdir(path) and os.path.exists(metadata_path):
        try:
            with open(metadata_path, "r", encoding="utf-8") as f:
                metadata = json.load(f)
                if "display_name" in metadata:
                    return metadata["display_name"]
        except Exception:
            pass

    # Extract the base name
    base_name = os.path.basename(path)

    # Handle special cases
    if base_name == "organization_results":
        return "Organizations"
    elif base_name == "people_results":
        return "People"
    elif base_name == "opencorporates":
        return "Corporate Registry"
    elif base_name == "sanctions":
        return "Sanctions Screening"
    elif base_name == "wikidata":
        return "Entity Network"
    elif base_name == "news":
        return "Adverse Media"
    elif base_name == "pep":
        return "Politically Exposed Persons"

    # For files, remove extension and transform to title case
    if os.path.isfile(path):
        name_parts = os.path.splitext(base_name)[0].split("_")
        return " ".join(part.capitalize() for part in name_parts)

    # For folders, transform underscores to spaces and capitalize
    return " ".join(word.capitalize() for word in base_name.split("_"))


def get_folder_description(path: str) -> str:
    """
    Get a description for a folder if available from metadata.

    Args:
        path: The folder path

    Returns:
        A description string or empty string if not available
    """
    # Check if it's a folder with metadata
    metadata_path = os.path.join(path, ".metadata.json")
    if os.path.isdir(path) and os.path.exists(metadata_path):
        try:
            with open(metadata_path, "r", encoding="utf-8") as f:
                metadata = json.load(f)
                if "description" in metadata:
                    return metadata["description"]
        except Exception:
            pass

    # Default descriptions for common folders
    base_name = os.path.basename(path)

    if base_name == "entity_data":
        return "Detailed information about entities involved in the transaction"
    elif base_name == "organization_results":
        return "Data related to organizations identified in the transaction"
    elif base_name == "people_results":
        return "Data related to individuals identified in the transaction"
    elif base_name == "analysis_reports":
        return "Analytical reports generated during risk assessment"
    elif base_name == "risk_assessments":
        return "Final risk assessment results and supporting evidence"
    elif base_name == "opencorporates":
        return "Corporate registry information from official sources"
    elif base_name == "sanctions":
        return "Sanctions screening results from global sanctions lists"
    elif base_name == "wikidata":
        return "Entity network and relationship information"
    elif base_name == "news":
        return "Adverse media mentions and news articles"
    elif base_name == "pep":
        return "Politically Exposed Persons screening results"

    return ""

def build_folder_tree_with_display_names(base_folder: str, parent_path: str = "") -> List[Dict]:
    """
    Build a tree structure of folders with user-friendly display names.
    
    Args:
        base_folder: The base folder to scan
        parent_path: The parent path to prepend to the current path (for nested structures)
        
    Returns:
        A list of dictionaries representing the folder tree with display names
    """
    tree = []
    
    try:
        for item in sorted(os.listdir(base_folder)):
            # Skip hidden files and metadata
            if item.startswith('.'):
                continue
                
            item_path = os.path.join(base_folder, item)
            current_path = os.path.join(parent_path, item) if parent_path else item
            
            if os.path.isdir(item_path):
                # It's a directory
                display_name = get_display_name_from_path(item_path)
                description = get_folder_description(item_path)
                
                # Recursively get children
                children = build_folder_tree_with_display_names(item_path, current_path)
                
                tree.append({
                    "name": item,
                    "display_name": display_name,
                    "description": description,
                    "type": "directory",
                    "path": current_path,
                    "children": children
                })
            else:
                # It's a file
                display_name = get_display_name_from_path(item_path)
                file_size = os.path.getsize(item_path)
                
                tree.append({
                    "name": item,
                    "display_name": display_name,
                    "type": "file",
                    "path": current_path,
                    "size": file_size
                })
    except Exception as e:
        logger.error(f"Error building folder tree: {str(e)}")
    
    return tree

# Function to initialize the knowledge base folder structure for a transaction
def initialize_knowledge_base(results_folder: str, transaction_id: str) -> str:
    """
    Initialize the knowledge base folder structure for a transaction.

    Args:
        results_folder: Base results folder path
        transaction_id: Transaction ID

    Returns:
        Path to the transaction folder
    """
    kb_structure = KnowledgeBaseFolderStructure(results_folder)
    return kb_structure.create_transaction_folder_structure(transaction_id)


# Function to migrate existing transactions to the new folder structure
def migrate_transaction_to_knowledge_base(
    results_folder: str, transaction_id: str
) -> bool:
    """
    Migrate an existing transaction to the knowledge base folder structure.

    Args:
        results_folder: Base results folder path
        transaction_id: Transaction ID

    Returns:
        Success status as boolean
    """
    kb_structure = KnowledgeBaseFolderStructure(results_folder)
    return kb_structure.migrate_existing_transaction(transaction_id)


# Function to build a friendly folder tree for the API
def get_knowledge_base_structure(
    results_folder: str, transaction_id: str
) -> List[Dict]:
    """
    Get a user-friendly representation of the transaction knowledge base.

    Args:
        results_folder: Base results folder path
        transaction_id: Transaction ID

    Returns:
        A list of dictionaries representing the folder tree with display names
    """
    transaction_folder = os.path.join(results_folder, transaction_id)

    if not os.path.exists(transaction_folder):
        return []

    return build_folder_tree_with_display_names(transaction_folder)
