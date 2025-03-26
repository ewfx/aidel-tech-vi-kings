from airflow import DAG
from airflow.decorators import task, task_group
from airflow.operators.dummy import DummyOperator
from airflow.utils.dates import days_ago
from airflow.utils.trigger_rule import TriggerRule
import logging
import os
import json
import httpx
from datetime import timedelta

# Import utilities
from dags.utils.entity_extraction import extract_entities_from_text
from dags.utils.data_enrichment import (
    get_open_corporates_data, 
    check_sanctions, 
    query_wikidata, 
    check_pep_list, 
    check_adverse_news
)
from dags.utils.risk_assessment import generate_risk_assessment
from dags.utils.knowledge_base_utils import initialize_knowledge_base, migrate_transaction_to_knowledge_base
from dags.utils.neo4j_utils import retrieve_entity_history, store_transaction_results

# Import settings
from config.settings import RESULTS_FOLDER

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Define default arguments for the DAG
default_args = {
    'owner': 'airflow',
    'depends_on_past': False,
    'email_on_failure': False,
    'email_on_retry': False,
    'retries': 1,
    'retry_delay': timedelta(minutes=1),
}

# Create the DAG
with DAG(
    'aml_risk_assessment',
    default_args=default_args,
    description='AML Risk Assessment DAG with TaskFlow API',
    schedule_interval=None,
    start_date=days_ago(1),
    tags=['aml', 'risk', 'assessment', 'neo4j'],
    catchup=False,
    render_template_as_native_obj=True,  # Enable rendering of templates as Python objects
) as dag:
    
    # ========== INITIAL SETUP TASKS ==========
    
    @task
    def get_transaction_data(**context):
        """Get the transaction data from the DAG run configuration."""
        dag_run = context['dag_run']
        conf = dag_run.conf
        
        transaction_data = conf.get('transaction_data')
        transaction_id = conf.get('transaction_id')
        callback_url = conf.get('callback_url')
        
        if not transaction_data:
            raise ValueError("Transaction data not provided in DAG run configuration")
        
        if not transaction_id:
            raise ValueError("Transaction ID not provided in DAG run configuration")
        
        logger.info(f"Processing transaction: {transaction_id}")
        
        # Initialize knowledge base folder structure
        initialize_knowledge_base(RESULTS_FOLDER, transaction_id)
        
        return {
            "transaction_data": transaction_data,
            "transaction_id": transaction_id,
            "callback_url": callback_url
        }
    
    @task
    def extract_entities(transaction_info):
        """Extract organizations and people from transaction data."""
        transaction_data = transaction_info["transaction_data"]
        transaction_id = transaction_info["transaction_id"]
        
        # Use the function that works with text directly
        entities = extract_entities_from_text(transaction_data, transaction_id)
        logger.info(f"Extracted entities: {entities}")
        return entities
    
    @task
    def get_entity_history(transaction_info, entities):
        """Retrieve historical information for entities from Neo4j."""
        transaction_id = transaction_info["transaction_id"]
        
        # Use the Neo4j utility to get historical data
        history = retrieve_entity_history(transaction_id, entities)
        
        logger.info(f"Retrieved history for entities in transaction: {transaction_id}")
        return history
    
    # ========== ENTITY PROCESSING TASKS ==========
    
    @task_group
    def process_organizations(transaction_info, entities, entity_history):
        """Process all organizations in the transaction."""
        
        @task
        def extract_organizations(entities_dict):
            """Extract the list of organizations from the entities."""
            return entities_dict.get("organizations", [])
        
        @task
        def extract_history_map(history_dict):
            """Extract and flatten the entity history into a usable map."""
            # This helps convert the XCom reference to an actual dictionary
            return history_dict or {}
        
        @task
        def process_organization(organization, history_map, **context):
            """Process a single organization with all relevant checks."""
            org_name = organization.get('name', '')
            logger.info(f"Processing organization: {org_name}")
            
            # Extract the transaction ID from the unpacked transaction_info
            # This avoids nested XCom references
            transaction_id = context['dag_run'].conf.get('transaction_id')
            
            results = {}
            
            # Get OpenCorporates data
            results['opencorporates'] = get_open_corporates_data(
                organization, transaction_id=transaction_id, **context
            )
            
            # Check sanctions
            results['sanctions'] = check_sanctions(
                'Company', org_name, transaction_id=transaction_id, **context
            )
            
            # Query Wikidata
            wikidata_result = query_wikidata(
                org_name, transaction_id=transaction_id, **context
            )
            results['wikidata'] = wikidata_result
            
            # Check adverse news
            results['news'] = check_adverse_news(
                org_name, transaction_id=transaction_id, **context
            )
            
            # Add any discovered people from Wikidata
            results['discovered_people'] = wikidata_result.get('associated_people', [])
            
            # Add historical data if available
            # Use the history_map that was already converted to a dictionary
            if history_map and org_name in history_map:
                results['history'] = history_map.get(org_name, {})
                
            return {
                "name": org_name,
                "results": results
            }
            
        # Get the organizations list
        orgs_list = extract_organizations(entities)
        
        # Extract and flatten the history
        history_map = extract_history_map(entity_history)
        
        # Process each organization and return results
        org_results = process_organization.expand(
            organization=orgs_list,
            history_map=[history_map]  # Pass it as a single list item to ensure it doesn't get expanded
        )
        
        return org_results
    
    @task_group
    def process_people(transaction_info, entities, entity_history):
        """Process all people in the transaction."""
        
        @task
        def extract_people(entities_dict):
            """Extract the list of people from the entities."""
            return entities_dict.get("people", [])
        
        @task
        def extract_history_map(history_dict):
            """Extract and flatten the entity history into a usable map."""
            # This helps convert the XCom reference to an actual dictionary
            return history_dict or {}
        
        @task
        def process_person(person, history_map, **context):
            """Process a single person with all relevant checks."""
            person_name = person.get('name', '')
            logger.info(f"Processing person: {person_name}")
            
            # Extract the transaction ID from the unpacked transaction_info
            # This avoids nested XCom references
            transaction_id = context['dag_run'].conf.get('transaction_id')
            
            results = {}
            
            # Check PEP list
            results['pep'] = check_pep_list(
                person_name, transaction_id=transaction_id, **context
            )
            
            # Check sanctions
            results['sanctions'] = check_sanctions(
                'Person', person_name, transaction_id=transaction_id, **context
            )
            
            # Check adverse news
            results['news'] = check_adverse_news(
                person_name, transaction_id=transaction_id, **context
            )
            
            # Add historical data if available
            # Use the history_map that was already converted to a dictionary
            if history_map and person_name in history_map:
                results['history'] = history_map.get(person_name, {})
                
            return {
                "name": person_name,
                "results": results
            }
            
        # Get the people list
        people_list = extract_people(entities)
        
        # Extract and flatten the history
        history_map = extract_history_map(entity_history)
        
        # Process each person and return results
        people_results = process_person.expand(
            person=people_list,
            history_map=[history_map]  # Pass it as a single list item to ensure it doesn't get expanded
        )
        
        return people_results
    
    @task_group
    def process_discovered_people(transaction_info, org_results, entity_history):
        """Process people discovered from Wikidata that weren't in the original transaction."""
        
        @task
        def extract_discovered_people(org_results_list):
            """Extract people discovered from organizations' Wikidata results."""
            discovered_people = []
            seen_names = set()
            
            for org_result in org_results_list:
                results = org_result.get('results', {})
                if 'discovered_people' in results:
                    for person in results['discovered_people']:
                        name = person.get('name', '').lower()
                        if name and name not in seen_names:
                            discovered_people.append(person)
                            seen_names.add(name)
            
            logger.info(f"Discovered {len(discovered_people)} additional people from Wikidata")
            return discovered_people
            
        @task
        def extract_history_map(history_dict):
            """Extract and flatten the entity history into a usable map."""
            # This helps convert the XCom reference to an actual dictionary
            return history_dict or {}
        
        @task
        def process_discovered_person(person, history_map, **context):
            """Process a single discovered person with all relevant checks."""
            person_name = person.get('name', '')
            logger.info(f"Processing discovered person: {person_name}")
            
            # Extract the transaction ID from the context
            transaction_id = context['dag_run'].conf.get('transaction_id')
            
            results = {}
            
            # Check PEP list
            results['pep'] = check_pep_list(
                person_name, transaction_id=transaction_id, **context
            )
            
            # Check sanctions
            results['sanctions'] = check_sanctions(
                'Person', person_name, transaction_id=transaction_id, **context
            )
            
            # Check adverse news
            results['news'] = check_adverse_news(
                person_name, transaction_id=transaction_id, **context
            )
            
            # Add historical data if available
            if history_map and person_name in history_map:
                results['history'] = history_map.get(person_name, {})
                
            # Include source information
            results['source'] = person.get('source', 'wikidata')
            results['entity_connection'] = person.get('entity_connection', '')
            
            return {
                "name": person_name,
                "results": results
            }
        
        # Extract and flatten the history
        history_map = extract_history_map(entity_history)
            
        # Extract discovered people
        discovered_list = extract_discovered_people(org_results)
        
        # Check if the list is empty using a task to ensure proper task dependencies
        @task
        def check_discovered_list(people_list):
            return len(people_list) > 0
            
        has_discovered = check_discovered_list(discovered_list)
        
        # Process each discovered person if any
        @task
        def empty_discovered_list():
            return []
            
        @task
        def process_all_discovered(people_list, history_map, has_people):
            if not has_people:
                return []
                
            # We need to manually process the list since we can't use dynamic task mapping with conditionals
            results = []
            
            for person in people_list:
                person_name = person.get('name', '')
                transaction_id = context['dag_run'].conf.get('transaction_id')
                
                person_results = {}
                
                # Check PEP list
                person_results['pep'] = check_pep_list(
                    person_name, transaction_id=transaction_id
                )
                
                # Check sanctions
                person_results['sanctions'] = check_sanctions(
                    'Person', person_name, transaction_id=transaction_id
                )
                
                # Check adverse news
                person_results['news'] = check_adverse_news(
                    person_name, transaction_id=transaction_id
                )
                
                # Add historical data if available
                if history_map and person_name in history_map:
                    person_results['history'] = history_map.get(person_name, {})
                    
                # Include source information
                person_results['source'] = person.get('source', 'wikidata')
                person_results['entity_connection'] = person.get('entity_connection', '')
                
                results.append({
                    "name": person_name,
                    "results": person_results
                })
                
            return results
            
        discovered_results = process_all_discovered(
            discovered_list, 
            history_map,
            has_discovered
        )
            
        return discovered_results
    
    # ========== FINAL ASSESSMENT TASKS ==========
    
    @task(trigger_rule=TriggerRule.ALL_DONE)
    def combine_results(
        transaction_info, 
        entities, 
        entity_history,
        org_results, 
        people_results, 
        discovered_people_results
    ):
        """Combine all processing results into a single structure for risk assessment."""
        # Extract transaction info values
        transaction_id = None
        transaction_data = None
        
        # Handle the transaction_info object
        if isinstance(transaction_info, dict):
            transaction_id = transaction_info.get("transaction_id")
            transaction_data = transaction_info.get("transaction_data")
        else:
            # Fallback to getting directly from context
            from airflow.operators.python import get_current_context
            context = get_current_context()
            dag_run_conf = context['dag_run'].conf
            transaction_id = dag_run_conf.get('transaction_id')
            transaction_data = dag_run_conf.get('transaction_data')
        
        # Build the complete results structure
        all_results = {
            "transaction_id": transaction_id,
            "transaction_data": transaction_data,
            "entities": entities,
            "entity_history": entity_history,
            "organizations": {},
            "people": {},
            "discovered_people": {}
        }
        
        # Process organization results - safely handle if results are None or empty
        if org_results:
            # Handle both list and non-list cases
            org_results_list = org_results if isinstance(org_results, list) else [org_results]
            for org_result in org_results_list:
                if isinstance(org_result, dict):
                    name = org_result.get('name', '')
                    if name:
                        all_results["organizations"][name] = org_result.get('results', {})
        
        # Process people results - safely handle if results are None or empty
        if people_results:
            # Handle both list and non-list cases
            people_results_list = people_results if isinstance(people_results, list) else [people_results]
            for person_result in people_results_list:
                if isinstance(person_result, dict):
                    name = person_result.get('name', '')
                    if name:
                        all_results["people"][name] = person_result.get('results', {})
        
        # Process discovered people results - safely handle if results are None or empty
        if discovered_people_results:
            # Handle both list and non-list cases
            discovered_list = discovered_people_results if isinstance(discovered_people_results, list) else [discovered_people_results]
            for person_result in discovered_list:
                if isinstance(person_result, dict):
                    name = person_result.get('name', '')
                    if name:
                        all_results["discovered_people"][name] = person_result.get('results', {})
        
        return all_results
    
    @task
    def assess_risk(transaction_info, all_results):
        """Generate the final risk assessment."""
        transaction_id = transaction_info["transaction_id"]
        transaction_data = transaction_info["transaction_data"]
        
        risk_assessment = generate_risk_assessment(
            transaction_data=transaction_data,
            transaction_id=transaction_id,
            all_results=all_results
        )
        return risk_assessment
    
    @task
    def organize_knowledge_base(transaction_info, risk_assessment):
        """Organize the transaction data into a structured knowledge base."""
        transaction_id = transaction_info["transaction_id"]
        
        try:
            # Migrate the transaction folder to a structured knowledge base
            success = migrate_transaction_to_knowledge_base(RESULTS_FOLDER, transaction_id)
            
            if success:
                logger.info(f"Successfully organized knowledge base for transaction {transaction_id}")
            else:
                logger.warning(f"Failed to organize knowledge base for transaction {transaction_id}")
                
            return {"knowledge_base_organized": success}
        
        except Exception as e:
            logger.error(f"Error organizing knowledge base: {str(e)}")
            return {"knowledge_base_organized": False, "error": str(e)}
    
    @task
    def store_in_neo4j(transaction_info, entities, risk_assessment):
        """Store transaction results in Neo4j."""
        transaction_id = transaction_info["transaction_id"]
        
        # Use the Neo4j utility to store the results
        result = store_transaction_results(transaction_id, risk_assessment, entities)
        
        logger.info(f"Stored transaction results in Neo4j: {result}")
        return result
    
    @task(trigger_rule=TriggerRule.ALL_DONE)
    def send_callback(transaction_info, risk_assessment, **context):
        """Send callback to API with the results."""
        transaction_id = transaction_info["transaction_id"]
        callback_url = transaction_info.get("callback_url")
        
        if not callback_url:
            logger.warning(f"No callback URL provided for transaction {transaction_id}")
            return {"callback_sent": False, "reason": "No callback URL provided"}
        
        dag_id = context['dag'].dag_id
        run_id = context['run_id']
        
        # Prepare the callback data
        callback_data = {
            "transaction_id": transaction_id,
            "dag_id": dag_id,
            "run_id": run_id,
            "status": "completed",
            "risk_assessment": risk_assessment
        }
        
        # Send the callback
        try:
            logger.info(f"Sending callback to {callback_url}")
            
            # Use httpx for better async support
            with httpx.Client(timeout=30.0) as client:
                response = client.post(callback_url, json=callback_data)
                response.raise_for_status()
                
            logger.info(f"Callback sent successfully: {response.text}")
            return {"callback_sent": True}
        except Exception as e:
            logger.error(f"Error sending callback: {str(e)}")
            # Continue even if callback fails
            return {"callback_sent": False, "error": str(e)}
    
    # ========== DAG WORKFLOW DEFINITION ==========
    
    # Initial setup
    transaction_info = get_transaction_data()
    entities = extract_entities(transaction_info)
    entity_history = get_entity_history(transaction_info, entities)
    
    # Process entities
    org_results = process_organizations(transaction_info, entities, entity_history)
    people_results = process_people(transaction_info, entities, entity_history)
    discovered_people_results = process_discovered_people(transaction_info, org_results, entity_history)
    
    # Combine results and assess risk
    all_results = combine_results(
        transaction_info,
        entities,
        entity_history,
        org_results,
        people_results,
        discovered_people_results
    )
    
    risk_assessment = assess_risk(transaction_info, all_results)
    
    # Final tasks - these can run in parallel
    kb_result = organize_knowledge_base(transaction_info, risk_assessment)
    neo4j_result = store_in_neo4j(transaction_info, entities, risk_assessment)
    
    # Send callback should be the last task
    callback_result = send_callback(transaction_info, risk_assessment)
    
    # Define the final task dependencies - ensure callback is the last step
    [kb_result, neo4j_result] >> callback_result
    
    # End task to mark completion
    end_task = DummyOperator(
        task_id='end_task',
        trigger_rule=TriggerRule.ALL_DONE,  # Run even if some tasks fail
    )
    
    callback_result >> end_task