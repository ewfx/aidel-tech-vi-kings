import os
import json
import logging
import requests
import pycountry
import re
import csv
from SPARQLWrapper import SPARQLWrapper, JSON

from dags.config.settings import (
    RESULTS_FOLDER, OPENCORPORATES_API_KEY, OPENSANCTIONS_API_KEY, 
    PEP_DATA_FILE
)

# Import the transaction folder utilities
from dags.utils.transaction_folder import (
    get_transaction_folder, save_transaction_data, load_transaction_data
)

# Configure logging
logger = logging.getLogger(__name__)

def _get_transaction_id_from_context(context=None, obj=None):
    """
    Extract transaction ID from context, object, or default to 'unknown_transaction'.
    
    Args:
        context: The task context dict
        obj: An organization or person dict that might contain transaction_id
        
    Returns:
        transaction_id: String identifier for the transaction
    """
    # First try to get it from the object passed in
    if obj and isinstance(obj, dict) and 'transaction_id' in obj:
        return obj['transaction_id']
        
    # Then try to get it from the context
    if context:
        dag_run = context.get('dag_run')
        if dag_run and hasattr(dag_run, 'conf'):
            conf = dag_run.conf
            if conf and 'transaction_id' in conf:
                return conf['transaction_id']
    
    return "unknown_transaction"

def get_open_corporates_data(organization_info, **context):
    """
    Get company information from OpenCorporates API.
    """
    try:
        organization_name = organization_info.get('name')
        jurisdiction = organization_info.get('jurisdiction')
        transaction_id = _get_transaction_id_from_context(context, organization_info)
        
        if not organization_name:
            logger.warning("No organization name provided")
            return {"status": "failed", "reason": "No organization name provided", "data": None}
        
        params = {
            "q": organization_name,
            "api_token": OPENCORPORATES_API_KEY
        }
        
        # Add jurisdiction if available
        if jurisdiction:
            # Convert country name to code if needed
            try:
                country = pycountry.countries.get(name=jurisdiction)
                if country:
                    params["country_code"] = country.alpha_2.lower()
            except:
                logger.warning(f"Could not convert jurisdiction {jurisdiction} to country code")
        
        response = requests.get("https://api.opencorporates.com/v0.4/companies/search", params=params)
        response.raise_for_status()
        data = response.json()
        
        # Get first result if available
        if (data 
            and "results" in data 
            and "companies" in data["results"] 
            and len(data["results"]["companies"]) > 0):
            company = data["results"]["companies"][0]["company"]
            
            # Save the OpenCorporates data to the transaction folder
            file_name = f"{organization_name.replace(' ', '_')}.json"
            save_transaction_data(
                RESULTS_FOLDER, 
                transaction_id, 
                file_name, 
                company, 
                subfolder="entity_data/organization_results/opencorporates"
            )
                
            return {"status": "success", "data": company}
        else:
            logger.warning(f"No results found for {organization_name}")
            return {"status": "no_results", "reason": f"No results found for {organization_name}", "data": None}
            
    except requests.exceptions.RequestException as e:
        logger.error(f"Error during OpenCorporates request: {str(e)}")
        return {"status": "failed", "reason": f"API request failed: {str(e)}", "data": None}
    except Exception as e:
        logger.error(f"Error getting OpenCorporates data: {str(e)}")
        return {"status": "failed", "reason": f"Unknown error: {str(e)}", "data": None}

def check_sanctions(entity_type, entity_name, **context):
    """
    Check if an entity is on sanctions lists using OpenSanctions API.
    """
    try:
        transaction_id = _get_transaction_id_from_context(context)
        
        if not entity_name:
            return {"status": "failed", "reason": "No entity name provided", "data": []}
        
        session = requests.Session()
        session.headers["Authorization"] = f"ApiKey {OPENSANCTIONS_API_KEY}"
        
        query = {"schema": entity_type, "properties": {"name": [entity_name]}}
        batch = {"queries": {"q1": query}}
        
        response = session.post("https://api.opensanctions.org/match/sanctions?algorithm=best", json=batch)
        response.raise_for_status()
        
        data = response.json()
        responses = data.get("responses", {})
        results = responses.get("q1", {}).get("results", [])
        
        # Filter for high confidence matches
        high_confidence_results = [res for res in results if res.get("score", 0) > 0.70]
        
        # Save the sanctions check results to the transaction folder
        subfolder = "entity_data/organization_results/sanctions" if entity_type == "Company" else "entity_data/people_results/sanctions"
        file_name = f"{entity_name.replace(' ', '_')}.json"
        save_transaction_data(
            RESULTS_FOLDER, 
            transaction_id, 
            file_name, 
            high_confidence_results, 
            subfolder=subfolder
        )
            
        return {"status": "success", "data": high_confidence_results}
        
    except requests.exceptions.RequestException as e:
        logger.error(f"Error during OpenSanctions request: {str(e)}")
        return {"status": "failed", "reason": f"API request failed: {str(e)}", "data": []}
    except Exception as e:
        logger.error(f"Error checking sanctions: {str(e)}")
        return {"status": "failed", "reason": f"Unknown error: {str(e)}", "data": []}

def query_wikidata(entity_name, **context):
    """
    Query Wikidata for information about an organization using SPARQL.
    Returns information and potentially new people associated with the entity.
    """
    try:
        transaction_id = _get_transaction_id_from_context(context)
            
        sparql = SPARQLWrapper("https://query.wikidata.org/sparql")
        
        # First, find the entity ID in Wikidata
        entity_query = f"""
        SELECT ?company ?companyLabel WHERE {{
          SERVICE wikibase:mwapi {{
            bd:serviceParam wikibase:endpoint "www.wikidata.org";
                            wikibase:api "EntitySearch";
                            mwapi:search "{entity_name}";
                            mwapi:language "en".
            ?company wikibase:apiOutputItem mwapi:item.
          }}
          SERVICE wikibase:label {{ bd:serviceParam wikibase:language "en". }}
        }}
        LIMIT 1
        """
        
        sparql.setQuery(entity_query)
        sparql.setReturnFormat(JSON)
        results = sparql.query().convert()
        
        if not results["results"]["bindings"]:
            logger.warning(f"No Wikidata entity found for {entity_name}")
            return {"status": "no_results", "reason": f"No Wikidata entity found for {entity_name}", "data": None, "associated_people": []}
        
        # Get the entity ID
        entity_id = results["results"]["bindings"][0]["company"]["value"].split("/")[-1]
        
        # Get detailed information about the entity
        info_query = f"""
        SELECT ?prop ?propLabel ?value ?valueLabel WHERE {{
          wd:{entity_id} ?p ?value .
          ?prop wikibase:directClaim ?p .
          SERVICE wikibase:label {{ bd:serviceParam wikibase:language "en". }}
          FILTER((?prop = wdt:P17) || (?prop = wdt:P1454) || (?prop = wdt:P112) || (?prop = wdt:P169) || (?prop = wdt:P571) || (?prop = wdt:P856))
        }}
        """
        
        sparql.setQuery(info_query)
        info_results = sparql.query().convert()
        
        # Process the results
        entity_info = {
            "entity_id": entity_id,
            "entity_name": entity_name,
            "properties": {}
        }
        
        for result in info_results["results"]["bindings"]:
            prop_label = result["propLabel"]["value"]
            value_label = result.get("valueLabel", {}).get("value", "Unknown")
            entity_info["properties"][prop_label] = value_label
        
        # Now look for associated people (founders, CEOs, key people)
        people_query = f"""
        SELECT DISTINCT ?person ?personLabel ?roleLabel WHERE {{
          wd:{entity_id} ?rel ?person .
          ?role wikibase:directClaim ?rel .
          FILTER(?role IN (wdt:P169, wdt:P112, wdt:P3320))
          ?person wdt:P31 wd:Q5 .  # Filter for humans
          SERVICE wikibase:label {{ bd:serviceParam wikibase:language "en". }}
        }}
        LIMIT 10
        """
        
        sparql.setQuery(people_query)
        people_results = sparql.query().convert()
        
        # Extract associated people
        associated_people = []
        for result in people_results["results"]["bindings"]:
            person_name = result.get("personLabel", {}).get("value")
            role = result.get("roleLabel", {}).get("value", "associated person")
            if person_name:
                associated_people.append({
                    "name": person_name,
                    "role": role,
                    "source": "wikidata",
                    "entity_connection": entity_name
                })
            
        # Save the Wikidata information to the transaction folder
        full_result = {
            "entity_info": entity_info,
            "associated_people": associated_people
        }
        
        save_transaction_data(
            RESULTS_FOLDER, 
            transaction_id, 
            f"{entity_name.replace(' ', '_')}.json", 
            full_result, 
            subfolder="entity_data/organization_results/wikidata"
        )
            
        return {"status": "success", "data": entity_info, "associated_people": associated_people}
        
    except Exception as e:
        logger.error(f"Error querying Wikidata: {str(e)}")
        return {"status": "failed", "reason": f"Error querying Wikidata: {str(e)}", "data": None, "associated_people": []}

def check_pep_list(person_name, **context):
    """
    Check if a person is on the PEP (Politically Exposed Persons) list.
    """
    try:
        transaction_id = _get_transaction_id_from_context(context)
        
        if not person_name:
            return {"status": "failed", "reason": "No person name provided", "data": None}
            
        if not os.path.exists(PEP_DATA_FILE):
            logger.warning(f"PEP data file {PEP_DATA_FILE} not found")
            return {"status": "failed", "reason": f"PEP data file {PEP_DATA_FILE} not found", "data": None}
        
        # Create a simplified name for matching
        simplified_name = re.sub(r'[^\w\s]', '', person_name.lower())
        name_parts = simplified_name.split()
        
        # Read the PEP data
        pep_matches = []
        try:
            with open(PEP_DATA_FILE, 'r', encoding='utf-8') as csv_file:
                # Changed delimiter from tab to comma based on the sample data
                csv_reader = csv.DictReader(csv_file)
                
                for row in csv_reader:
                    # Check for missing keys and use empty string as default
                    row_name = row.get('name', '')
                    row_aliases = row.get('aliases', '').split(';') if row.get('aliases') else []
                    
                    # Simplify the row name and aliases for matching
                    simplified_row_name = re.sub(r'[^\w\s]', '', row_name.lower())
                    simplified_aliases = [re.sub(r'[^\w\s]', '', alias.lower()) for alias in row_aliases]
                    
                    # Improved name matching logic
                    # Check if any part of the search name appears in the PEP name
                    name_match = False
                    for part in name_parts:
                        if part and len(part) > 2:  # Only consider parts with more than 2 characters
                            if part in simplified_row_name.split():
                                name_match = True
                                break
                    
                    # Check if any part of the search name appears in any alias
                    alias_match = False
                    for alias in simplified_aliases:
                        for part in name_parts:
                            if part and len(part) > 2:
                                if part in alias.split():
                                    alias_match = True
                                    break
                        if alias_match:
                            break
                    
                    if name_match or alias_match:
                        pep_matches.append(row)
        
        except Exception as e:
            logger.error(f"Error reading PEP data file: {str(e)}")
            return {"status": "failed", "reason": f"Error reading PEP data: {str(e)}", "data": None}
        
        # Save the PEP matches to the transaction folder
        save_transaction_data(
            RESULTS_FOLDER, 
            transaction_id, 
            f"{person_name.replace(' ', '_')}.json", 
            pep_matches, 
            subfolder="entity_data/people_results/pep"
        )
            
        return {"status": "success", "data": pep_matches}
        
    except Exception as e:
        logger.error(f"Error checking PEP list: {str(e)}")
        return {"status": "failed", "reason": f"Error checking PEP list: {str(e)}", "data": None}

def check_adverse_news(entity_name, **context):
    """
    Check for adverse news about an entity using the GDELT API.
    """
    try:
        transaction_id = _get_transaction_id_from_context(context)
        
        if not entity_name:
            return {"status": "failed", "reason": "No entity name provided", "data": []}
            
        # Format entity name for URL
        formatted_name = entity_name.replace(' ', '+')
        
        # Build the query for fraud, scam, sanctions related news
        query_terms = "fraud+scam+scandal+sanctions+corruption+lawsuit+investigation"
        url = f"https://api.gdeltproject.org/api/v2/doc/doc?query={formatted_name}+{query_terms}&mode=artlist&format=json"
        
        print(f"Querying GDELT API with URL: {url}")
        
        response = requests.get(url)
        response.raise_for_status()
        data = response.json()
        
        articles = data.get("articles", [])
        
        # Process and filter articles
        filtered_articles = []
        for article in articles:
            article_info = {
                "title": article.get("title", ""),
                "url": article.get("url", ""),
                "source": article.get("domain", ""),
                "date": article.get("seendate", ""),
                "tone": article.get("tone", 0),  # GDELT sentiment score
                "themes": article.get("themes", [])
            }
            
            # Filter for negative sentiment and relevant themes
            if article_info["tone"] < -2:  # Negative tone
                filtered_articles.append(article_info)
        
        # Determine the correct subfolder based on the task ID or entity type
        task_instance = context.get('task_instance')
        task_id = task_instance.task_id if task_instance else ''
        is_person = task_id and 'person' in task_id
        subfolder = "entity_data/people_results/news" if is_person else "entity_data/organization_results/news"
        
        # Save the adverse news to the transaction folder
        save_transaction_data(
            RESULTS_FOLDER, 
            transaction_id, 
            f"{entity_name.replace(' ', '_')}.json", 
            filtered_articles, 
            subfolder=subfolder
        )
            
        return {"status": "success", "data": filtered_articles}
        
    except requests.exceptions.RequestException as e:
        logger.error(f"Error during GDELT request: {str(e)}")
        return {"status": "failed", "reason": f"GDELT API request failed: {str(e)}", "data": []}
    except Exception as e:
        logger.error(f"Error checking adverse news: {str(e)}")
        return {"status": "failed", "reason": f"Unknown error: {str(e)}", "data": []}

def process_wikidata_people(**context):
    """
    Process new people found via Wikidata queries and create tasks for them.
    """
    try:
        ti = context.get('ti')
        if not ti:
            logger.warning("Task instance not available in context")
            return []
            
        transaction_id = _get_transaction_id_from_context(context)
            
        new_people = []
        
        # Get entity extraction result to get original people
        original_entities = ti.xcom_pull(task_ids='extract_entities')
        original_people = set()
        if original_entities and 'people' in original_entities:
            for person in original_entities['people']:
                if 'name' in person:
                    original_people.add(person['name'].lower())
    
        # Look for all wikidata results
        for task_id in ti.xcom_pull(dag_id=context.get('dag').dag_id, include_prior_dates=True) or []:
            if task_id.startswith('wikidata_'):
                wikidata_result = ti.xcom_pull(task_ids=task_id)
                if wikidata_result and 'status' in wikidata_result and wikidata_result['status'] == 'success':
                    if 'associated_people' in wikidata_result:
                        for person in wikidata_result['associated_people']:
                            if person['name'].lower() not in original_people:
                                new_people.append(person)
                                original_people.add(person['name'].lower())  # Mark as processed to avoid duplicates
        
        # Save the new people list to the transaction folder
        save_transaction_data(
            RESULTS_FOLDER, 
            transaction_id, 
            "wikidata_discovered_people.json", 
            new_people
        )
        
        return new_people
    
    except Exception as e:
        logger.error(f"Error processing Wikidata people: {str(e)}")
        return []