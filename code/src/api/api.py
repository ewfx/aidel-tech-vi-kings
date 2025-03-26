"""
Enhanced FastAPI Backend for AML Risk Assessment with direct Airflow integration
and support for transaction folders
"""

from fastapi import FastAPI, HTTPException, BackgroundTasks, Request, Depends, Query
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Dict, List, Optional, Any, Union
import os
import json
import logging
import time
import asyncio
import traceback
import uuid
import glob
from datetime import datetime, timedelta
import httpx
import fastapi.responses
from dotenv import load_dotenv
from utils.neo4j_utils import Neo4jManager
from utils.knowledge_base_utils import get_knowledge_base_structure
load_dotenv()

# Import transaction folder utilities
from utils.transaction_folder import (
    get_transaction_folder, save_transaction_data, 
    load_transaction_data, list_transaction_results
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Results folder - used for storing transaction data
RESULTS_FOLDER = os.environ.get('RESULTS_FOLDER', '/opt/airflow/data/results')
os.makedirs(RESULTS_FOLDER, exist_ok=True)

# Airflow connection settings
AIRFLOW_HOST = os.environ.get('AIRFLOW_HOST', 'airflow-webserver')
AIRFLOW_PORT = os.environ.get('AIRFLOW_PORT', '8080')
AIRFLOW_USER = os.environ.get('AIRFLOW_USER', 'airflow')
AIRFLOW_PASSWORD = os.environ.get('AIRFLOW_PASSWORD', 'airflow')
AIRFLOW_BASE_URL = f"http://{AIRFLOW_HOST}:{AIRFLOW_PORT}/api/v1"

# Callback URL for Airflow to notify when processing is complete
API_HOST = os.environ.get('API_HOST', 'fastapi')
API_PORT = os.environ.get('API_PORT', '8000')
API_CALLBACK_URL = f"http://{API_HOST}:{API_PORT}/api/callback"

# Create FastAPI app
app = FastAPI(
    title="AML Risk Assessment API", 
    description="Anti-Money Laundering Risk Assessment API for financial transactions",
    version="1.0.0"
)

# Add CORS middleware to allow cross-origin requests
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Adjust in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# In-memory storage for transaction status and metadata
transaction_store = {}

# Models
class AirflowStatus(BaseModel):
    dag_id: str
    run_id: str
    status: str
    transaction_id: Optional[str] = None

class TaskResult(BaseModel):
    task_id: str
    status: str
    start_time: str
    end_time: Optional[str] = None
    result: Optional[Any] = None

class RiskAssessmentResult(BaseModel):
    transaction_id: str
    extracted_entities: List[str]
    entity_types: List[str]
    risk_score: float
    supporting_evidence: List[str]
    confidence_score: float
    reason: str
    status: str = "completed"
    timestamp: Optional[str] = None

class TransactionSummary(BaseModel):
    transaction_id: str
    timestamp: str
    status: str
    risk_score: float
    entities_count: int

class DashboardStats(BaseModel):
    totalTransactions: int
    highRiskTransactions: int
    mediumRiskTransactions: int
    lowRiskTransactions: int
    recentTransactions: List[dict]

class CallbackRequest(BaseModel):
    transaction_id: str
    dag_id: str
    run_id: str
    status: str
    result_path: Optional[str] = None

async def trigger_airflow_dag(transaction_data: str, transaction_id: str) -> AirflowStatus:
    """
    Trigger Airflow DAG directly via the REST API.
    """
    try:
        # Airflow API endpoint for triggering DAGs
        dag_id = "aml_risk_assessment"
        dag_run_id = f"{transaction_id}"
        airflow_api_url = f"{AIRFLOW_BASE_URL}/dags/{dag_id}/dagRuns"
        
        # Authentication credentials
        auth = (AIRFLOW_USER, AIRFLOW_PASSWORD)
        
        # First, save the transaction data to its own folder
        transaction_folder = get_transaction_folder(RESULTS_FOLDER, transaction_id)
        transaction_file_path = os.path.join(transaction_folder, "transaction.txt")
        
        # Save the transaction data
        with open(transaction_file_path, 'w', encoding='utf-8') as f:
            f.write(transaction_data)
        
        # Prepare the payload according to Airflow API spec
        payload = {
            "dag_run_id": dag_run_id,
            "conf": {
                "transaction_data": transaction_data,
                "transaction_id": transaction_id,
                "callback_url": f"{API_CALLBACK_URL}/{transaction_id}"
            }
        }
        
        logger.info(f"Triggering Airflow DAG with payload for transaction: {transaction_id}")
        
        # Make the API request
        async with httpx.AsyncClient() as client:
            response = await client.post(
                airflow_api_url, 
                json=payload, 
                auth=auth,
                timeout=30.0
            )
            
        if response.status_code >= 400:
            logger.error(f"Error from Airflow API: {response.text}")
            raise HTTPException(
                status_code=500, 
                detail=f"Error triggering Airflow workflow: {response.text}"
            )
        
        logger.info(f"Airflow DAG {dag_id} triggered with run_id {dag_run_id}")
        
        # Store transaction metadata in the in-memory store
        transaction_store[transaction_id] = {
            "dag_id": dag_id,
            "run_id": dag_run_id,
            "status": "triggered",
            "timestamp": datetime.now().isoformat(),
            "folder": transaction_folder
        }
        
        # Save transaction metadata to the transaction folder
        metadata = {
            "transaction_id": transaction_id,
            "dag_id": dag_id,
            "run_id": dag_run_id,
            "status": "triggered",
            "timestamp": datetime.now().isoformat()
        }
        save_transaction_data(RESULTS_FOLDER, transaction_id, "metadata.json", metadata)
        
        # Return the Airflow status
        return AirflowStatus(dag_id=dag_id, run_id=dag_run_id, status="triggered", transaction_id=transaction_id)
        
    except httpx.HTTPError as e:
        logger.error(f"HTTP error triggering Airflow DAG: {str(e)}")
        raise HTTPException(
            status_code=500, 
            detail=f"Error triggering Airflow workflow: {str(e)}"
        )
    except Exception as e:
        logger.error(f"Error triggering Airflow DAG: {str(e)}")
        raise HTTPException(
            status_code=500, 
            detail=f"Error triggering Airflow workflow: {str(e)}"
        )
 
async def check_dag_status(dag_id: str, run_id: str) -> Dict:
    """
    Check the status of a DAG run in Airflow
    """
    # Airflow API endpoint for checking DAG run status
    airflow_api_url = f"{AIRFLOW_BASE_URL}/dags/{dag_id}/dagRuns/{run_id}"
    
    # Authentication credentials
    auth = (AIRFLOW_USER, AIRFLOW_PASSWORD)
    
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(airflow_api_url, auth=auth)
        
        if response.status_code == 200:
            return response.json()
        else:
            logger.warning(f"Error getting DAG status: {response.text}")
            return {"state": "unknown"}
    except Exception as e:
        logger.error(f"Error checking DAG status: {str(e)}")
        return {"state": "error"}

@app.post("/api/transaction", response_model=Union[RiskAssessmentResult, AirflowStatus])
async def receive_transaction(request: Request, background_tasks: BackgroundTasks, wait: bool = False):
    """
    Endpoint to receive transaction data in text format.
    - If wait=True: waits for Airflow DAG to complete and returns the risk assessment result
    - If wait=False: returns immediately with the Airflow trigger status
    
    Parameters:
    - wait: Boolean parameter to indicate whether to wait for processing to complete
    """
    try:
        # Get raw bytes from the request body
        data = await request.body()
        
        # Try different encodings to handle potential encoding issues
        try:
            text_data = data.decode('utf-8')
        except UnicodeDecodeError:
            try:
                text_data = data.decode('latin-1')
                logger.info("Decoded request body using latin-1 encoding")
            except UnicodeDecodeError:
                # If all else fails, decode with errors='replace'
                text_data = data.decode('utf-8', errors='replace')
                logger.warning("Decoded request body with replacement characters due to encoding issues")
        
        if not text_data:
            raise HTTPException(status_code=400, detail="No transaction data provided")
        
        # Generate a unique transaction ID
        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
        transaction_id = f"txn_{timestamp}_{uuid.uuid4().hex[:8]}"
        
        # Trigger Airflow DAG directly with the transaction data
        status = await trigger_airflow_dag(text_data, transaction_id)
        
        if wait:
            # Poll for the DAG to complete
            max_wait_time = 600  # 10 minutes
            start_time = time.time()
            
            while time.time() - start_time < max_wait_time:
                # Get the DAG run status
                dag_status = await check_dag_status(status.dag_id, status.run_id)
                
                if dag_status.get('state') == 'success':
                    # Check for the risk assessment result in the transaction folder
                    risk_assessment = load_transaction_data(
                        RESULTS_FOLDER, transaction_id, "risk_assessment.json"
                    )
                    
                    if risk_assessment:
                        return risk_assessment
                    
                    # If the risk assessment is not in the transaction folder, try the old location
                    result_filename = f"result_{status.run_id}.json"
                    result_path = os.path.join(RESULTS_FOLDER, result_filename)
                    
                    if os.path.exists(result_path):
                        with open(result_path, 'r', encoding='utf-8') as f:
                            result = json.load(f)
                            
                        return result
                    
                elif dag_status.get('state') in ['failed', 'error']:
                    raise HTTPException(
                        status_code=500,
                        detail=f"Airflow DAG {status.dag_id} with run_id {status.run_id} failed"
                    )
                
                # Wait before checking again
                await asyncio.sleep(5)
            
            # If we get here, the DAG didn't complete in time
            raise HTTPException(
                status_code=504,
                detail=f"Timeout waiting for Airflow DAG {status.dag_id} with run_id {status.run_id} to complete"
            )
        else:
            # Return immediately with the Airflow trigger status
            return status
    
    except HTTPException:
        raise
    except Exception as e:
        # Log the full exception traceback for debugging
        logger.error(f"Error processing transaction: {traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "timestamp": datetime.now().isoformat()}

@app.post("/api/callback/{transaction_id}")
async def process_callback(transaction_id: str, callback_data: CallbackRequest):
    """
    Callback endpoint for Airflow to notify when a DAG run is complete.
    """
    try:
        logger.info(f"Received callback for transaction {transaction_id}: {callback_data}")
        
        # Validate that the transaction ID matches
        if transaction_id != callback_data.transaction_id:
            logger.warning(f"Transaction ID mismatch: {transaction_id} vs {callback_data.transaction_id}")
            raise HTTPException(status_code=400, detail="Transaction ID mismatch")
        
        # Update the transaction store with the new status
        if transaction_id in transaction_store:
            transaction_store[transaction_id].update({
                "status": callback_data.status,
                "result_path": callback_data.result_path
            })
        else:
            transaction_store[transaction_id] = {
                "dag_id": callback_data.dag_id,
                "run_id": callback_data.run_id,
                "status": callback_data.status,
                "timestamp": datetime.now().isoformat(),
                "result_path": callback_data.result_path
            }
        
        # Update the metadata in the transaction folder
        metadata = {
            "transaction_id": transaction_id,
            "dag_id": callback_data.dag_id,
            "run_id": callback_data.run_id,
            "status": callback_data.status,
            "timestamp": datetime.now().isoformat()
        }
        save_transaction_data(RESULTS_FOLDER, transaction_id, "metadata.json", metadata)
        
        return {"status": "success", "message": f"Callback processed for transaction {transaction_id}"}
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error processing callback: {traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/transaction/{transaction_id}", response_model=RiskAssessmentResult)
async def get_transaction_status(transaction_id: str):
    """
    Get the status or result of a transaction processing.
    """
    try:
        # First check if there's a transaction folder
        transaction_folder = os.path.join(RESULTS_FOLDER, transaction_id)
        if os.path.exists(transaction_folder):
            # Check for risk assessment in the transaction folder
            risk_assessment = load_transaction_data(RESULTS_FOLDER, transaction_id, "risk_assessment.json")
            if risk_assessment:
                # If found, get transaction metadata for additional information
                metadata = load_transaction_data(RESULTS_FOLDER, transaction_id, "metadata.json")
                
                return risk_assessment
            
            # If no risk assessment yet, check for metadata to determine status
            metadata = load_transaction_data(RESULTS_FOLDER, transaction_id, "metadata.json")
            if metadata:
                # If we have metadata, use it to check the DAG status
                if "dag_id" in metadata and "run_id" in metadata:
                    dag_status = await check_dag_status(metadata["dag_id"], metadata["run_id"])
                    
                    # Return a basic structure with what we know
                    airflow_status = dag_status.get("state", "processing")
                    
                    base_result = {
                        "transaction_id": transaction_id,
                        "status": airflow_status,
                        "extracted_entities": [],
                        "entity_types": [],
                        "risk_score": 0.0,
                        "supporting_evidence": [],
                        "confidence_score": 0.0,
                        "reason": f"Transaction is {airflow_status}"
                    }
                                        
                    return base_result
        
        # Next, check the in-memory store
        transaction_info = transaction_store.get(transaction_id)
        if transaction_info and transaction_info.get("status") == "completed":
            # If we have a completed transaction with a result path
            result_path = transaction_info.get("result_path")
            if result_path and os.path.exists(result_path):
                with open(result_path, 'r', encoding='utf-8') as f:
                    result = json.load(f)
                
                return result
            
        # If we have some information but not the full result yet
        if transaction_info:
            # Check the status in Airflow
            if transaction_info.get("dag_id") and transaction_info.get("run_id"):
                dag_status = await check_dag_status(
                    transaction_info["dag_id"], 
                    transaction_info["run_id"]
                )
                
                # If the DAG is complete but we don't have the result, look for it
                if dag_status.get("state") == "success":
                    # Check for results in transaction folder first
                    risk_assessment = load_transaction_data(RESULTS_FOLDER, transaction_id, "risk_assessment.json")
                    if risk_assessment:
                        return risk_assessment
                    
                    # Look for the legacy result file
                    result_filename = f"result_{transaction_info['run_id']}.json"
                    result_path = os.path.join(RESULTS_FOLDER, result_filename)
                    
                    if os.path.exists(result_path):
                        with open(result_path, 'r', encoding='utf-8') as f:
                            result = json.load(f)
                        
                        # Update the transaction store
                        transaction_info["status"] = "completed"
                        transaction_info["result_path"] = result_path
                                                
                        return result
            
            # Return a basic structure with what we know
            airflow_status = transaction_info.get("status", "processing")
            
            base_result = {
                "transaction_id": transaction_id,
                "status": airflow_status,
                "extracted_entities": [],
                "entity_types": [],
                "risk_score": 0.0,
                "supporting_evidence": [],
                "confidence_score": 0.0,
                "reason": f"Transaction is {airflow_status}"
            }
                        
            return base_result
        
        # If we don't have the transaction in our store, check if it's a legacy transaction
        # by looking directly for result files
        result_files = []
        if os.path.exists(RESULTS_FOLDER):
            result_files = [f for f in os.listdir(RESULTS_FOLDER) 
                        if f.startswith(f"result_") and transaction_id in f]
        
        if result_files:
            # Return the latest result
            result_path = os.path.join(RESULTS_FOLDER, result_files[-1])
            with open(result_path, 'r', encoding='utf-8') as f:
                result = json.load(f)
            
            # Extract run ID from the filename if possible
            run_id = None
            if result_files[-1].startswith("result_") and not result_files[-1].startswith("result_aml_run_"):
                run_id = result_files[-1].replace("result_", "").split(".")[0]
            
            # Store the transaction info for future requests
            transaction_store[transaction_id] = {
                "status": "completed",
                "result_path": result_path,
                "timestamp": datetime.now().isoformat(),
                "run_id": run_id
            }
                        
            return result
        
        # Check with Airflow API directly as a last resort
        try:
            # Try with the standard format of run_id
            run_id = transaction_id
            dag_id = "aml_risk_assessment"
            dag_status = await check_dag_status(dag_id, run_id)
            
            if dag_status.get("state"):
                # We found the DAG run, store this info
                transaction_store[transaction_id] = {
                    "dag_id": dag_id,
                    "run_id": run_id,
                    "status": dag_status.get("state"),
                    "timestamp": datetime.now().isoformat()
                }
                
                # Create or update metadata in transaction folder
                metadata = {
                    "transaction_id": transaction_id,
                    "dag_id": dag_id,
                    "run_id": run_id,
                    "status": dag_status.get("state"),
                    "timestamp": datetime.now().isoformat()
                }
                save_transaction_data(RESULTS_FOLDER, transaction_id, "metadata.json", metadata)
                
                # Return a basic result with the status
                base_result = {
                    "transaction_id": transaction_id,
                    "status": "processing" if dag_status.get("state") == "running" else dag_status.get("state"),
                    "extracted_entities": [],
                    "entity_types": [],
                    "risk_score": 0.0,
                    "supporting_evidence": [],
                    "confidence_score": 0.0,
                    "reason": f"Transaction is being processed by Airflow (status: {dag_status.get('state')})"
                }
                                
                return base_result
        except Exception as e:
            logger.warning(f"Could not find DAG run in Airflow: {str(e)}")
        
        # Transaction not found
        raise HTTPException(status_code=404, detail=f"Transaction {transaction_id} not found")
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting transaction status: {traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/dashboard/stats", response_model=DashboardStats)
async def get_dashboard_stats():
    """
    Get statistics for the dashboard.
    """
    try:
        # Find all transaction folders
        all_results = []
        
        # Get all transaction folders
        transaction_folders = list_transaction_results(RESULTS_FOLDER)
        
        # Process each transaction folder
        for transaction_id in transaction_folders:
            risk_assessment = load_transaction_data(RESULTS_FOLDER, transaction_id, "risk_assessment.json")
            metadata = load_transaction_data(RESULTS_FOLDER, transaction_id, "metadata.json")
            
            if risk_assessment:
                # Add timestamp from metadata if not present in risk assessment
                if "timestamp" not in risk_assessment and metadata and "timestamp" in metadata:
                    risk_assessment["timestamp"] = metadata["timestamp"]
                
                all_results.append(risk_assessment)
        
        # Then look for any legacy result files not in transaction folders
        legacy_result_files = glob.glob(os.path.join(RESULTS_FOLDER, "result_*.json"))
        
        for result_file in legacy_result_files:
            # Skip files we've already processed (transaction IDs we've seen)
            file_txn_id = None
            for prefix in ["result_", "result_aml_run_"]:
                if os.path.basename(result_file).startswith(prefix):
                    file_txn_id = os.path.basename(result_file).replace(prefix, "").split(".")[0]
                    break
            
            if file_txn_id and file_txn_id in transaction_folders:
                continue
                
            try:
                with open(result_file, 'r', encoding='utf-8') as f:
                    result = json.load(f)
                
                # Ensure the result has the necessary fields
                if "transaction_id" in result and "risk_score" in result:
                    # Add timestamp based on file creation time if not present
                    if "timestamp" not in result:
                        result["timestamp"] = datetime.fromtimestamp(
                            os.path.getctime(result_file)
                        ).isoformat()
                    
                    all_results.append(result)
            except Exception as e:
                logger.warning(f"Error reading result file {result_file}: {str(e)}")
        
        # Calculate dashboard statistics
        total_transactions = len(all_results)
        high_risk_transactions = sum(1 for r in all_results if r.get("risk_score", 0) >= 0.7)
        medium_risk_transactions = sum(1 for r in all_results if 0.4 <= r.get("risk_score", 0) < 0.7)
        low_risk_transactions = sum(1 for r in all_results if r.get("risk_score", 0) < 0.4)
        
        # Get recent transactions
        recent_transactions = []
        for result in sorted(all_results, key=lambda x: x.get("timestamp", ""), reverse=True)[:5]:
            recent_transactions.append({
                "id": result.get("transaction_id", ""),
                "timestamp": result.get("timestamp", datetime.now().isoformat()),
                "risk": result.get("risk_score", 0),
                "status": "completed"
            })
        
        return {
            "totalTransactions": total_transactions,
            "highRiskTransactions": high_risk_transactions,
            "mediumRiskTransactions": medium_risk_transactions,
            "lowRiskTransactions": low_risk_transactions,
            "recentTransactions": recent_transactions
        }
    
    except Exception as e:
        logger.error(f"Error getting dashboard stats: {traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/transactions")
async def get_transactions(
    limit: int = Query(100, ge=1, le=1000),
    offset: int = Query(0, ge=0),
    status: Optional[str] = None,
    search: Optional[str] = None,
    sort_by: Optional[str] = None,
    sort_order: Optional[str] = None
):
    """
    Get a list of all transactions.
    """
    try:
        all_transactions = []
        
        # Get all transaction folders from the results folder
        transaction_folders = list_transaction_results(RESULTS_FOLDER)
        
        # Process each transaction folder
        for transaction_id in transaction_folders:
            risk_assessment = load_transaction_data(RESULTS_FOLDER, transaction_id, "risk_assessment.json")
            metadata = load_transaction_data(RESULTS_FOLDER, transaction_id, "metadata.json")
            
            # Create transaction summary
            summary = {
                "transaction_id": transaction_id,
                "timestamp": datetime.now().isoformat(),  # Default timestamp
                "status": "processing",  # Default status
                "risk_score": 0.0,  # Default risk score
                "entities_count": 0  # Default entities count
            }
            
            # Update with metadata information if available
            if metadata:
                if "timestamp" in metadata:
                    summary["timestamp"] = metadata["timestamp"]
                if "status" in metadata:
                    summary["status"] = metadata["status"]
            
            # Update with risk assessment information if available
            if risk_assessment:
                summary["status"] = "completed"  # If we have a risk assessment, it's completed
                summary["risk_score"] = risk_assessment.get("risk_score", 0.0)
                summary["entities_count"] = len(risk_assessment.get("extracted_entities", []))
            
            all_transactions.append(summary)
        
        # Also check for legacy transaction records in the store
        for transaction_id, info in transaction_store.items():
            # Skip if already processed from folders
            if transaction_id in transaction_folders:
                continue
                
            summary = {
                "transaction_id": transaction_id,
                "timestamp": info.get("timestamp", datetime.now().isoformat()),
                "status": info.get("status", "processing"),
                "risk_score": 0.0,
                "entities_count": 0
            }
            
            # If it's completed and we have a result path, get more details
            if info.get("status") == "completed" and info.get("result_path"):
                try:
                    with open(info["result_path"], 'r', encoding='utf-8') as f:
                        result = json.load(f)
                    
                    summary["risk_score"] = result.get("risk_score", 0.0)
                    summary["entities_count"] = len(result.get("extracted_entities", []))
                except Exception as e:
                    logger.warning(f"Error reading result file {info['result_path']}: {str(e)}")
            
            all_transactions.append(summary)
        
        # Look for any legacy result files not covered by folders or store
        legacy_result_files = glob.glob(os.path.join(RESULTS_FOLDER, "result_*.json"))
        
        for result_file in legacy_result_files:
            # Extract transaction ID from filename
            file_txn_id = None
            for prefix in ["result_", "result_aml_run_"]:
                if os.path.basename(result_file).startswith(prefix):
                    file_txn_id = os.path.basename(result_file).replace(prefix, "").split(".")[0]
                    break
            
            # Skip if already processed
            if file_txn_id and (file_txn_id in transaction_folders or 
                              any(t["transaction_id"] == file_txn_id for t in all_transactions)):
                continue
                
            try:
                with open(result_file, 'r', encoding='utf-8') as f:
                    result = json.load(f)
                
                transaction_id = result.get("transaction_id", os.path.basename(result_file).split('.')[0])
                
                # Skip if we already have this transaction
                if any(t["transaction_id"] == transaction_id for t in all_transactions):
                    continue
                
                # Get file creation time as a timestamp
                file_timestamp = datetime.fromtimestamp(os.path.getctime(result_file)).isoformat()
                
                summary = {
                    "transaction_id": transaction_id,
                    "timestamp": result.get("timestamp", file_timestamp),
                    "status": "completed",
                    "risk_score": result.get("risk_score", 0.0),
                    "entities_count": len(result.get("extracted_entities", []))
                }
                
                all_transactions.append(summary)
            except Exception as e:
                logger.warning(f"Error reading result file {result_file}: {str(e)}")
        
        # Apply filters
        filtered_transactions = all_transactions
        
        if status:
            filtered_transactions = [t for t in filtered_transactions if t["status"] == status]
        
        if search:
            filtered_transactions = [t for t in filtered_transactions if search.lower() in t["transaction_id"].lower()]
        
        # Apply sorting
        if sort_by:
            reverse = sort_order == "desc"
            filtered_transactions.sort(key=lambda x: x.get(sort_by, ""), reverse=reverse)
        else:
            # Default sort by timestamp, newest first
            filtered_transactions.sort(key=lambda x: x.get("timestamp", ""), reverse=True)
        
        # Apply pagination
        paginated_transactions = filtered_transactions[offset:offset + limit]
        
        return paginated_transactions
    except Exception as e:
        logger.error(f"Error getting transactions: {traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=str(e))
    
# Add this to your api.py file, inside the FastAPI app

@app.get("/api/transaction/{transaction_id}/files")
@app.get("/api/transaction/{transaction_id}/files")
async def get_transaction_files(transaction_id: str):
    """
    Get all files and directories in the transaction folder with user-friendly names.
    """
    try:
        # Get the transaction folder path
        transaction_folder = os.path.join(RESULTS_FOLDER, transaction_id)
        
        if not os.path.exists(transaction_folder):
            raise HTTPException(status_code=404, detail=f"Transaction folder for {transaction_id} not found")
        
        # Use the knowledge base utility to get a structured view with display names
        file_tree = get_knowledge_base_structure(RESULTS_FOLDER, transaction_id)
        
        return file_tree
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting transaction files: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error getting transaction files: {str(e)}")
    
@app.get("/api/transaction/{transaction_id}/files/{file_path:path}")
async def get_transaction_file_content(transaction_id: str, file_path: str, download: bool = False):
    """
    Get the content of a specific file in the transaction folder.
    
    Args:
        transaction_id: The ID of the transaction
        file_path: The relative path of the file within the transaction folder
        download: If True, returns the file as a download response
    """
    try:
        # Get the transaction folder path
        transaction_folder = os.path.join(RESULTS_FOLDER, transaction_id)
        file_full_path = os.path.join(transaction_folder, file_path)
        
        if not os.path.exists(file_full_path):
            raise HTTPException(status_code=404, detail=f"File {file_path} not found")
        
        if os.path.isdir(file_full_path):
            raise HTTPException(status_code=400, detail=f"{file_path} is a directory, not a file")
        
        # For download mode, return the file as a download response
        if download:
            return fastapi.responses.FileResponse(
                path=file_full_path,
                filename=os.path.basename(file_path),
                media_type="application/octet-stream"
            )
        
        # Check file size and reject if too large (e.g., > 5MB) for viewing
        if os.path.getsize(file_full_path) > 5 * 1024 * 1024:
            return {"content": "[File too large to display. Use download option instead.]"}
        
        # For view mode, try to read file content as text
        try:
            # First check if it's a JSON file
            if file_path.lower().endswith('.json'):
                with open(file_full_path, 'r', encoding='utf-8') as f:
                    content = json.load(f)
                    return {"content": json.dumps(content, indent=2)}
            
            # Otherwise read as plain text
            with open(file_full_path, 'r', encoding='utf-8') as f:
                content = f.read()
                return {"content": content}
        except UnicodeDecodeError:
            # For binary files, return an appropriate message
            return {"content": "[Binary file content not displayed. Use the download option instead.]"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting file content: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error getting file content: {str(e)}")
    
@app.post("/api/transactions/bulk", response_model=Dict[str, Any])
async def bulk_upload_transactions(
    request: Request,
    file_format: str = Query(..., description="Format of uploaded file (csv or txt)"),
    wait: bool = Query(False, description="Wait for all processing to complete"),
):
    """
    Endpoint to receive multiple transactions in either CSV or TXT format.
    
    - CSV format: structured data with columns
    - TXT format: unstructured data with transactions separated by '---'
    
    Parameters:
    - file_format: Format of the uploaded file ('csv' or 'txt')
    - wait: Boolean parameter to indicate whether to wait for processing to complete
    """
    try:
        # Read the uploaded file content
        data = await request.body()
        
        # Try different encodings to handle potential encoding issues
        try:
            text_data = data.decode('utf-8')
        except UnicodeDecodeError:
            try:
                text_data = data.decode('latin-1')
                logger.info("Decoded request body using latin-1 encoding")
            except UnicodeDecodeError:
                # If all else fails, decode with errors='replace'
                text_data = data.decode('utf-8', errors='replace')
                logger.warning("Decoded request body with replacement characters due to encoding issues")
        
        if not text_data:
            raise HTTPException(status_code=400, detail="No data provided")
        
        # Process based on file format
        transactions = []
        
        if file_format.lower() == 'csv':
            # Process CSV data
            import csv
            import io
            
            csv_file = io.StringIO(text_data)
            csv_reader = csv.DictReader(csv_file)
            
            for row in csv_reader:
                transaction_text = []
                
                # Other transaction details
                for key, value in row.items():
                    if (value):
                        transaction_text.append(f"{key}: {value}")
                
                transactions.append('\n'.join(transaction_text))
        
        elif file_format.lower() == 'txt':
            # Process TXT data with transactions separated by ---
            transactions = [t.strip() for t in text_data.split('---') if t.strip()]
        
        else:
            raise HTTPException(status_code=400, detail=f"Unsupported file format: {file_format}")
        
        if not transactions:
            raise HTTPException(status_code=400, detail="No valid transactions found in the uploaded file")
        
        # Process each transaction
        results = []
        failed = []
        
        for i, transaction_text in enumerate(transactions):
            try:
                # Generate a unique transaction ID with timestamp and index
                timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
                transaction_id = f"bulk_{timestamp}_{i}_{uuid.uuid4().hex[:8]}"
                
                # Trigger Airflow DAG
                status = await trigger_airflow_dag(transaction_text, transaction_id)
                
                if wait:
                    # Start polling for completion if wait=True
                    max_wait_time = 600  # 10 minutes
                    start_time = time.time()
                    
                    while time.time() - start_time < max_wait_time:
                        # Get the DAG run status
                        dag_status = await check_dag_status(status.dag_id, status.run_id)
                        
                        if dag_status.get('state') == 'success':
                            # Check for the risk assessment result
                            risk_assessment = load_transaction_data(
                                RESULTS_FOLDER, transaction_id, "risk_assessment.json"
                            )
                            
                            if risk_assessment:
                                results.append({
                                    "transaction_id": transaction_id,
                                    "status": "completed",
                                    "risk_score": risk_assessment.get("risk_score", 0),
                                    "index": i
                                })
                                break
                        
                        elif dag_status.get('state') in ['failed', 'error']:
                            failed.append({
                                "transaction_id": transaction_id,
                                "status": "failed",
                                "error": f"Airflow DAG {status.dag_id} failed",
                                "index": i
                            })
                            break
                        
                        # Wait before checking again
                        await asyncio.sleep(5)
                    
                    # If we timeout waiting
                    if time.time() - start_time >= max_wait_time:
                        failed.append({
                            "transaction_id": transaction_id,
                            "status": "timeout",
                            "error": "Timeout waiting for processing to complete",
                            "index": i
                        })
                
                else:
                    # Just return the triggered status if not waiting
                    results.append({
                        "transaction_id": transaction_id,
                        "status": "processing",
                        "run_id": status.run_id,
                        "index": i
                    })
                    
            except Exception as e:
                logger.error(f"Error processing transaction {i}: {str(e)}")
                failed.append({
                    "index": i,
                    "error": str(e),
                    "status": "failed"
                })
        
        # Return a summary of processed transactions
        return {
            "total": len(transactions),
            "processed": len(results),
            "failed": len(failed),
            "results": results,
            "failures": failed
        }
    
    except HTTPException:
        raise
    except Exception as e:
        # Log the full exception traceback for debugging
        logger.error(f"Error processing bulk transactions: {traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=str(e))
    
# Add these endpoints to your api.py file

from utils.neo4j_utils import get_entity_history_from_neo4j

@app.get("/api/entity/history/{entity_name}")
async def get_entity_history(entity_name: str, entity_type: str = None):
    """
    Get historical information about an entity from Neo4j.
    
    Args:
        entity_name: Name of the entity
        entity_type: Type of entity ('Organization' or 'Person')
        
    Returns:
        Historical data for the entity
    """
    try:
        history = get_entity_history_from_neo4j(entity_name, entity_type)
        return history
    except Exception as e:
        logger.error(f"Error retrieving entity history: {str(e)}")
        raise HTTPException(
            status_code=500, 
            detail=f"Error retrieving entity history: {str(e)}"
        )

@app.get("/api/transaction/{transaction_id}/history")
async def get_transaction_entity_history(transaction_id: str):
    """
    Get historical information for all entities in a transaction.
    
    Args:
        transaction_id: The ID of the transaction
        
    Returns:
        Dict mapping entity names to their historical data
    """
    try:
        # Load the entities from the transaction folder
        entities = load_transaction_data(RESULTS_FOLDER, transaction_id, "entities.json")
        
        if not entities:
            raise HTTPException(
                status_code=404, 
                detail=f"No entities found for transaction {transaction_id}"
            )
        
        # Load history if it exists
        history = load_transaction_data(RESULTS_FOLDER, transaction_id, "entity_history.json")
        
        if history:
            return history
        
        # If history doesn't exist in the transaction folder, retrieve it from Neo4j
        from utils.neo4j_utils import get_entities_history_from_neo4j
        
        history = get_entities_history_from_neo4j(entities)
        
        # Save the history data to the transaction folder
        save_transaction_data(RESULTS_FOLDER, transaction_id, "entity_history.json", history)
        
        return history
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrieving transaction entity history: {str(e)}")
        raise HTTPException(
            status_code=500, 
            detail=f"Error retrieving transaction entity history: {str(e)}"
        )

@app.get("/api/transaction/{transaction_id}/network")
async def get_transaction_network(transaction_id: str, depth: int = 2):
    """
    Get the network visualization data for a transaction.
    
    Args:
        transaction_id: The ID of the transaction
        depth: How many hops to traverse from the transaction (default: 2)
        
    Returns:
        Network visualization data (nodes and links)
    """
    try:
        # Connect to Neo4j and query the transaction network
        with Neo4jManager() as neo4j:
            if not neo4j.driver:
                raise HTTPException(
                    status_code=500, 
                    detail="Could not connect to Neo4j database"
                )
                
            with neo4j.driver.session(database=neo4j.database) as session:
                # Query to get the transaction network
                result = session.run("""
                    MATCH (t:Transaction {id: $transaction_id})
                    CALL {
                        WITH t
                        MATCH path = (t)-[r1*1..2]-(e)
                        RETURN path
                        UNION
                        WITH t
                        MATCH path = (e1)-[r1]-(t)-[r2]-(e2)
                        RETURN path
                    }
                    WITH DISTINCT relationships(path) AS rels, nodes(path) AS nodes
                    UNWIND nodes AS node
                    UNWIND rels AS rel
                    RETURN COLLECT(DISTINCT node) AS nodes, COLLECT(DISTINCT rel) AS relationships
                """, {"transaction_id": transaction_id})
                
                record = result.single()
                if not record:
                    return {"nodes": [], "links": []}
                
                # Process nodes
                nodes = []
                node_ids = set()
                for node in record["nodes"]:
                    node_data = dict(node)
                    node_id = node_data.get("id", str(node.id))
                    
                    # Skip duplicates
                    if node_id in node_ids:
                        continue
                    
                    node_ids.add(node_id)
                    
                    # Determine node type based on labels
                    node_type = "Unknown"
                    for label in node.labels:
                        if label in ["Organization", "Person", "Transaction"]:
                            node_type = label
                            break
                    
                    # Get node properties
                    node_info = {
                        "id": node_id,
                        "label": node_data.get("name", node_id) if node_type != "Transaction" else node_id,
                        "type": node_type
                    }
                    
                    # Add risk score if available
                    if "risk_score" in node_data:
                        node_info["risk"] = node_data["risk_score"]
                    
                    nodes.append(node_info)
                
                # Process relationships
                links = []
                for rel in record["relationships"]:
                    rel_data = dict(rel)
                    source_id = rel.start_node.get("id", str(rel.start_node.id))
                    target_id = rel.end_node.get("id", str(rel.end_node.id))
                    
                    # Get relationship properties
                    link_info = {
                        "source": source_id,
                        "target": target_id,
                        "label": rel.type
                    }
                    
                    # Add role if available
                    if "role" in rel_data:
                        link_info["label"] = rel_data["role"]
                    
                    links.append(link_info)
                
                return {
                    "nodes": nodes,
                    "links": links
                }
                
    except Exception as e:
        logger.error(f"Error getting transaction network: {str(e)}")
        raise HTTPException(
            status_code=500, 
            detail=f"Error getting transaction network: {str(e)}"
        )