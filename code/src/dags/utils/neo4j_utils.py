"""
Neo4j integration utilities for the AML Risk Assessment system.

This module provides functions for connecting to Neo4j, storing transaction data,
and retrieving historical information about entities.
"""
import os
import json
import logging
from typing import Dict, List, Any, Optional, Union
from datetime import datetime
from neo4j import GraphDatabase, basic_auth
from dotenv import load_dotenv
load_dotenv()

# Import transaction folder utilities if needed for your specific implementation
from dags.utils.transaction_folder import (
    get_transaction_folder, save_transaction_data, load_transaction_data
)

# Configure logging
logger = logging.getLogger(__name__)

# Neo4j connection settings from environment variables
NEO4J_URI = os.environ.get('NEO4J_URI', 'bolt://neo4j:7687')
NEO4J_USER = os.environ.get('NEO4J_USER', 'neo4j')
NEO4J_PASSWORD = os.environ.get('NEO4J_PASSWORD', 'password')
NEO4J_DATABASE = os.environ.get('NEO4J_DATABASE', 'neo4j')

class Neo4jManager:
    """
    Manager class for Neo4j database operations.
    """
    def __init__(self, uri=NEO4J_URI, user=NEO4J_USER, password=NEO4J_PASSWORD, database=NEO4J_DATABASE):
        """
        Initialize the Neo4j connection.
        
        Args:
            uri: Neo4j connection URI
            user: Neo4j username
            password: Neo4j password
            database: Neo4j database name
        """
        self.uri = uri
        self.user = user
        self.password = password
        self.database = database
        self.driver = None
        
    def connect(self):
        """
        Connect to Neo4j database.
        
        Returns:
            Success status as boolean
        """
        try:
            self.driver = GraphDatabase.driver(
                self.uri, 
                auth=basic_auth(self.user, self.password)
            )
            # Test the connection
            with self.driver.session(database=self.database) as session:
                result = session.run("RETURN 1 AS test").single()
                if result and result.get("test") == 1:
                    logger.info("Successfully connected to Neo4j database")
                    return True
                else:
                    logger.error("Neo4j connection test failed")
                    return False
        except Exception as e:
            logger.error(f"Error connecting to Neo4j: {str(e)}")
            return False
            
    def close(self):
        """Close the Neo4j connection."""
        if self.driver:
            self.driver.close()
            
    def __enter__(self):
        """Context manager entry."""
        self.connect()
        return self
        
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.close()

    def store_transaction(self, transaction_id: str, risk_assessment: Dict, entities_data: Dict) -> bool:
        """
        Store transaction and entity data in Neo4j.
        
        Args:
            transaction_id: Unique identifier for the transaction
            risk_assessment: Dict containing the risk assessment result
            entities_data: Dict containing extracted entities and their data
            
        Returns:
            Success status as boolean
        """
        try:
            if not self.driver:
                if not self.connect():
                    return False
                    
            with self.driver.session(database=self.database) as session:
                # Create Transaction node
                session.run("""
                    CREATE (t:Transaction {
                        id: $transaction_id,
                        timestamp: $timestamp,
                        risk_score: $risk_score,
                        confidence_score: $confidence_score,
                        reason: $reason
                    })
                """, {
                    "transaction_id": transaction_id,
                    "timestamp": datetime.now().isoformat(),
                    "risk_score": risk_assessment.get("risk_score", 0.0),
                    "confidence_score": risk_assessment.get("confidence_score", 0.0),
                    "reason": risk_assessment.get("reason", "")
                })
                
                # Create entity nodes and relationships
                organizations = entities_data.get("organizations", [])
                people = entities_data.get("people", [])
                
                # Store organizations
                for org in organizations:
                    org_name = org.get("name", "")
                    if not org_name:
                        continue
                        
                    org_type = org.get("entity_type", "Corporation")
                    jurisdiction = org.get("jurisdiction", "")
                    role = org.get("role", "unknown")
                    
                    # Merge the organization node (create if not exists, update if exists)
                    session.run("""
                        MERGE (o:Organization {name: $name})
                        ON CREATE SET 
                            o.type = $type,
                            o.jurisdiction = $jurisdiction,
                            o.first_seen = $timestamp
                        ON MATCH SET 
                            o.last_seen = $timestamp,
                            o.jurisdiction = CASE WHEN $jurisdiction <> '' 
                                                THEN $jurisdiction 
                                                ELSE o.jurisdiction 
                                           END
                        WITH o
                        MATCH (t:Transaction {id: $transaction_id})
                        MERGE (o)-[r:INVOLVED_IN {role: $role}]->(t)
                    """, {
                        "name": org_name,
                        "type": org_type,
                        "jurisdiction": jurisdiction,
                        "timestamp": datetime.now().isoformat(),
                        "transaction_id": transaction_id,
                        "role": role
                    })
                    
                # Store people
                for person in people:
                    person_name = person.get("name", "")
                    if not person_name:
                        continue
                        
                    role = person.get("role", "unknown")
                    country = person.get("country", "")
                    
                    # Merge the person node
                    session.run("""
                        MERGE (p:Person {name: $name})
                        ON CREATE SET 
                            p.country = $country,
                            p.first_seen = $timestamp
                        ON MATCH SET 
                            p.last_seen = $timestamp,
                            p.country = CASE WHEN $country <> '' 
                                            THEN $country 
                                            ELSE p.country 
                                       END
                        WITH p
                        MATCH (t:Transaction {id: $transaction_id})
                        MERGE (p)-[r:INVOLVED_IN {role: $role}]->(t)
                    """, {
                        "name": person_name,
                        "country": country,
                        "timestamp": datetime.now().isoformat(),
                        "transaction_id": transaction_id,
                        "role": role
                    })
                    
                # Add discovered relationships between people and organizations
                for org in organizations:
                    org_name = org.get("name", "")
                    if not org_name:
                        continue
                        
                    # Look for related people in the data
                    org_data = entities_data.get("organizations", {}).get(org_name, {})
                    wikidata_result = org_data.get("wikidata", {})
                    
                    if wikidata_result and "associated_people" in wikidata_result:
                        for related_person in wikidata_result["associated_people"]:
                            person_name = related_person.get("name", "")
                            person_role = related_person.get("role", "associated")
                            
                            if person_name:
                                # Create relationship between person and organization
                                session.run("""
                                    MATCH (p:Person {name: $person_name})
                                    MATCH (o:Organization {name: $org_name})
                                    MERGE (p)-[r:ASSOCIATED_WITH {role: $role}]->(o)
                                    ON CREATE SET r.since = $timestamp
                                """, {
                                    "person_name": person_name,
                                    "org_name": org_name,
                                    "role": person_role,
                                    "timestamp": datetime.now().isoformat()
                                })
                
                logger.info(f"Transaction {transaction_id} successfully stored in Neo4j")
                return True
                
        except Exception as e:
            logger.error(f"Error storing transaction in Neo4j: {str(e)}")
            return False

    def get_entity_history(self, entity_name: str, entity_type: str = None) -> Dict:
        """
        Retrieve historical information about an entity from Neo4j.
        
        Args:
            entity_name: Name of the entity (organization or person)
            entity_type: Type of entity ('Organization' or 'Person'), if None, will check both
            
        Returns:
            Dictionary containing historical data
        """
        try:
            if not self.driver:
                if not self.connect():
                    return {"status": "error", "message": "Could not connect to Neo4j", "data": None}
                    
            with self.driver.session(database=self.database) as session:
                history = {}
                
                if entity_type == "Organization" or entity_type is None:
                    # Get organization history
                    org_result = session.run("""
                        MATCH (o:Organization {name: $name})
                        OPTIONAL MATCH (o)-[r:INVOLVED_IN]->(t:Transaction)
                        RETURN o, 
                               collect(DISTINCT t.id) as transactions,
                               count(DISTINCT t) as transaction_count,
                               avg(t.risk_score) as avg_risk_score,
                               max(t.risk_score) as max_risk_score,
                               min(case when t.risk_score > 0 then t.risk_score else null end) as min_risk_score,
                               o.first_seen as first_seen,
                               o.last_seen as last_seen
                    """, {"name": entity_name})
                    
                    org_record = org_result.single()
                    if org_record and org_record.get("o"):
                        org_node = dict(org_record.get("o"))
                        history["organization"] = {
                            "properties": org_node,
                            "transactions": org_record.get("transactions"),
                            "transaction_count": org_record.get("transaction_count"),
                            "avg_risk_score": org_record.get("avg_risk_score"),
                            "max_risk_score": org_record.get("max_risk_score"),
                            "min_risk_score": org_record.get("min_risk_score"),
                            "first_seen": org_record.get("first_seen"),
                            "last_seen": org_record.get("last_seen")
                        }
                        
                        # Get related people
                        related_people_result = session.run("""
                            MATCH (p:Person)-[r:ASSOCIATED_WITH]->(o:Organization {name: $name})
                            RETURN p.name as name, r.role as role, r.since as since
                        """, {"name": entity_name})
                        
                        history["organization"]["related_people"] = [
                            {"name": record["name"], "role": record["role"], "since": record["since"]}
                            for record in related_people_result
                        ]
                
                if entity_type == "Person" or entity_type is None:
                    # Get person history
                    person_result = session.run("""
                        MATCH (p:Person {name: $name})
                        OPTIONAL MATCH (p)-[r:INVOLVED_IN]->(t:Transaction)
                        RETURN p, 
                               collect(DISTINCT t.id) as transactions,
                               count(DISTINCT t) as transaction_count,
                               avg(t.risk_score) as avg_risk_score,
                               max(t.risk_score) as max_risk_score,
                               min(case when t.risk_score > 0 then t.risk_score else null end) as min_risk_score,
                               p.first_seen as first_seen,
                               p.last_seen as last_seen
                    """, {"name": entity_name})
                    
                    person_record = person_result.single()
                    if person_record and person_record.get("p"):
                        person_node = dict(person_record.get("p"))
                        history["person"] = {
                            "properties": person_node,
                            "transactions": person_record.get("transactions"),
                            "transaction_count": person_record.get("transaction_count"),
                            "avg_risk_score": person_record.get("avg_risk_score"),
                            "max_risk_score": person_record.get("max_risk_score"),
                            "min_risk_score": person_record.get("min_risk_score"),
                            "first_seen": person_record.get("first_seen"),
                            "last_seen": person_record.get("last_seen")
                        }
                        
                        # Get related organizations
                        related_orgs_result = session.run("""
                            MATCH (p:Person {name: $name})-[r:ASSOCIATED_WITH]->(o:Organization)
                            RETURN o.name as name, r.role as role, r.since as since
                        """, {"name": entity_name})
                        
                        history["person"]["related_organizations"] = [
                            {"name": record["name"], "role": record["role"], "since": record["since"]}
                            for record in related_orgs_result
                        ]
                
                if not history:
                    return {
                        "status": "not_found",
                        "message": f"Entity '{entity_name}' not found in database",
                        "data": None
                    }
                    
                return {
                    "status": "success",
                    "data": history
                }
                
        except Exception as e:
            logger.error(f"Error retrieving entity history from Neo4j: {str(e)}")
            return {
                "status": "error",
                "message": f"Error retrieving entity history: {str(e)}",
                "data": None
            }

    def get_entities_history(self, entities_data: Dict) -> Dict[str, Dict]:
        """
        Retrieve historical information for multiple entities.
        
        Args:
            entities_data: Dict containing extracted entities
            
        Returns:
            Dictionary mapping entity names to their historical data
        """
        try:
            history = {}
            
            # Process organizations
            organizations = entities_data.get("organizations", [])
            for org in organizations:
                org_name = org.get("name", "")
                if org_name:
                    org_history = self.get_entity_history(org_name, "Organization")
                    if org_history.get("status") == "success":
                        history[org_name] = org_history.get("data", {})
            
            # Process people
            people = entities_data.get("people", [])
            for person in people:
                person_name = person.get("name", "")
                if person_name:
                    person_history = self.get_entity_history(person_name, "Person")
                    if person_history.get("status") == "success":
                        history[person_name] = person_history.get("data", {})
            
            return history
            
        except Exception as e:
            logger.error(f"Error retrieving entities history from Neo4j: {str(e)}")
            return {}

# Standalone functions for simpler usage
def store_transaction_in_neo4j(transaction_id: str, risk_assessment: Dict, entities_data: Dict) -> bool:
    """
    Store transaction data in Neo4j.
    
    Args:
        transaction_id: Unique identifier for the transaction
        risk_assessment: Dict containing the risk assessment result
        entities_data: Dict containing extracted entities data
        
    Returns:
        Success status as boolean
    """
    with Neo4jManager() as neo4j:
        return neo4j.store_transaction(transaction_id, risk_assessment, entities_data)

def get_entity_history_from_neo4j(entity_name: str, entity_type: str = None) -> Dict:
    """
    Get historical information about an entity from Neo4j.
    
    Args:
        entity_name: Name of the entity
        entity_type: Type of entity ('Organization' or 'Person')
        
    Returns:
        Dict containing historical data
    """
    with Neo4jManager() as neo4j:
        return neo4j.get_entity_history(entity_name, entity_type)

def get_entities_history_from_neo4j(entities_data: Dict) -> Dict[str, Dict]:
    """
    Get historical information for multiple entities from Neo4j.
    
    Args:
        entities_data: Dict containing extracted entities data
        
    Returns:
        Dict mapping entity names to their historical data
    """
    with Neo4jManager() as neo4j:
        return neo4j.get_entities_history(entities_data)

def retrieve_entity_history(transaction_id: str, entities_data: Dict, **context) -> Dict:
    """
    Airflow task function to retrieve historical information for entities.
    
    Args:
        transaction_id: The ID of the transaction
        entities_data: Dict containing extracted entities data
        context: Airflow task context
        
    Returns:
        Dict containing historical data for all entities
    """
    try:
        logger.info(f"Retrieving entity history for transaction: {transaction_id}")
        
        # Get history for all entities
        history = get_entities_history_from_neo4j(entities_data)
        
        # Save the history data to the transaction folder
        from config.settings import RESULTS_FOLDER
        save_transaction_data(RESULTS_FOLDER, transaction_id, "entity_history.json", history)
        
        logger.info(f"Successfully retrieved history for {len(history)} entities")
        return history
        
    except Exception as e:
        logger.error(f"Error retrieving entity history: {str(e)}")
        return {}

def store_transaction_results(transaction_id: str, risk_assessment: Dict, entities_data: Dict, **context) -> Dict:
    """
    Airflow task function to store transaction results in Neo4j.
    
    Args:
        transaction_id: The ID of the transaction
        risk_assessment: Dict containing the risk assessment result
        entities_data: Dict containing extracted entities data
        context: Airflow task context
        
    Returns:
        Dict containing the status of the operation
    """
    try:
        logger.info(f"Storing transaction results in Neo4j for transaction: {transaction_id}")
        
        # Store the transaction data
        success = store_transaction_in_neo4j(transaction_id, risk_assessment, entities_data)
        
        if success:
            logger.info(f"Successfully stored transaction {transaction_id} in Neo4j")
            return {"status": "success", "message": "Transaction stored in Neo4j"}
        else:
            logger.error(f"Failed to store transaction {transaction_id} in Neo4j")
            return {"status": "error", "message": "Failed to store transaction in Neo4j"}
            
    except Exception as e:
        logger.error(f"Error storing transaction results in Neo4j: {str(e)}")
        return {"status": "error", "message": f"Error storing transaction results: {str(e)}"}