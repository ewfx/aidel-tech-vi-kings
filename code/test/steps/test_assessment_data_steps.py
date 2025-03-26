import json
import requests
from behave import then
from test_steps import API_URL

def get_assessment_data(transaction_id, retries=3, delay=2):
    """
    Retrieve the raw assessment data for a transaction with retry logic.
    
    Args:
        transaction_id: The ID of the transaction
        retries: Number of retries in case of failure
        delay: Delay between retries in seconds
        
    Returns:
        The raw assessment data as a dictionary, or None if not found
    """
    for attempt in range(retries):
        response = requests.get(f"{API_URL}/transaction/{transaction_id}/files/analysis_reports/raw_assessment_data.json")
        if response.status_code == 200:
            print(f"Response status code: {response.status_code}")
            content = response.json().get("content")
            if isinstance(content, str):
                try:
                    return json.loads(content)
                except:
                    return None
            return content
        else:
            print(f"Attempt {attempt + 1} failed with status code: {response.status_code}")
            time.sleep(delay)
    
    return None

@then('the assessment data should include the transaction text')
def step_impl(context):
    """Check if the assessment data includes the original transaction text."""
    # Get the assessment data
    assessment_data = get_assessment_data(context.transaction_id)
    
    # Verify that we got data
    assert assessment_data, "No assessment data found"
    
    # Check that the transaction text is included
    assert "transaction_text" in assessment_data, "Assessment data does not include transaction text"
    
    # Verify it matches our original text (ignoring whitespace differences)
    original_text = context.transaction_text.strip()
    assessed_text = assessment_data["transaction_text"].strip()
    
    # Check if the core content is the same (allowing for some formatting differences)
    assert original_text in assessed_text or assessed_text in original_text, "Transaction text in assessment data doesn't match original"
    
    print("Assessment data contains the correct transaction text")

@then('the assessment data should include organization "{org_name}"')
def step_impl(context, org_name):
    """Check if the assessment data includes the specified organization."""
    # Get the assessment data
    assessment_data = get_assessment_data(context.transaction_id)
    
    # Verify that we got data
    assert assessment_data, "No assessment data found"
    
    # Check that organizations are included
    assert "organizations" in assessment_data, "Assessment data does not include organizations"
    
    # Check if the specified organization is included
    found = False
    for org in assessment_data["organizations"]:
        if org_name.lower() in org.lower():
            found = True
            # Store the organization for later steps
            if not hasattr(context, 'assessment_orgs'):
                context.assessment_orgs = {}
            context.assessment_orgs[org] = assessment_data["organizations"][org]
            break
            
    assert found, f"Organization '{org_name}' not found in assessment data"
    print(f"Assessment data includes organization: {org_name}")

@then('the assessment data should include person "{person_name}"')
def step_impl(context, person_name):
    """Check if the assessment data includes the specified person."""
    # Get the assessment data
    assessment_data = get_assessment_data(context.transaction_id)
    
    # Verify that we got data
    assert assessment_data, "No assessment data found"
    
    # Check that people are included
    assert "people" in assessment_data, "Assessment data does not include people"
    
    # Check if the specified person is included
    found = False
    for person in assessment_data["people"]:
        if person_name.lower() in person.lower():
            found = True
            # Store the person for later steps
            if not hasattr(context, 'assessment_people'):
                context.assessment_people = {}
            context.assessment_people[person] = assessment_data["people"][person]
            break
            
    assert found, f"Person '{person_name}' not found in assessment data"
    print(f"Assessment data includes person: {person_name}")

@then('organization "{org_name}" should have data from "{data_source}"')
def step_impl(context, org_name, data_source):
    """Check if the organization has data from the specified source."""
    # Make sure we have the assessment organizations
    if not hasattr(context, 'assessment_orgs'):
        context.execute_steps(f'Then the assessment data should include organization "{org_name}"')
    
    # Find the organization
    org_key = None
    for org in context.assessment_orgs:
        if org_name.lower() in org.lower():
            org_key = org
            break
    
    assert org_key, f"Organization '{org_name}' not found in stored assessment data"
    
    # Check if the data source is included
    org_data = context.assessment_orgs[org_key]
    assert data_source in org_data, f"Organization '{org_name}' does not have data from '{data_source}'"
    
    # Verify that the data is not empty
    assert org_data[data_source], f"Organization '{org_name}' has empty data from '{data_source}'"
    
    print(f"Organization '{org_name}' has data from '{data_source}'")

@then('person "{person_name}" should have data from "{data_source}"')
def step_impl(context, person_name, data_source):
    """Check if the person has data from the specified source."""
    # Make sure we have the assessment people
    if not hasattr(context, 'assessment_people'):
        context.execute_steps(f'Then the assessment data should include person "{person_name}"')
    
    # Find the person
    person_key = None
    for person in context.assessment_people:
        if person_name.lower() in person.lower():
            person_key = person
            break
    
    assert person_key, f"Person '{person_name}' not found in stored assessment data"
    
    # Check if the data source is included
    person_data = context.assessment_people[person_key]
    assert data_source in person_data, f"Person '{person_name}' does not have data from '{data_source}'"
    
    # Verify that the data is not empty
    assert person_data[data_source], f"Person '{person_name}' has empty data from '{data_source}'"
    
    print(f"Person '{person_name}' has data from '{data_source}'")

@then('the assessment data should include Wikidata-discovered people')
def step_impl(context):
    """Check if the assessment data includes people discovered through Wikidata."""
    # Get the assessment data
    assessment_data = get_assessment_data(context.transaction_id)
    
    # Verify that we got data
    assert assessment_data, "No assessment data found"
    
    # Check that Wikidata people are included
    assert "wikidata_people" in assessment_data, "Assessment data does not include Wikidata-discovered people"
    
    # Check if there are any discovered people
    assert assessment_data["wikidata_people"], "No Wikidata-discovered people found in assessment data"
    
    # Store for later steps
    context.wikidata_people = assessment_data["wikidata_people"]
    
    print(f"Assessment data includes {len(assessment_data['wikidata_people'])} Wikidata-discovered people")

@then('a Wikidata-discovered person should have role containing "{role_keyword}"')
def step_impl(context, role_keyword):
    """Check if a Wikidata-discovered person has the specified role."""
    # Make sure we have the Wikidata people
    if not hasattr(context, 'wikidata_people'):
        context.execute_steps('Then the assessment data should include Wikidata-discovered people')
    
    # Check for a person with the specified role
    found = False
    for person in context.wikidata_people:
        if "role" in person and role_keyword.lower() in person["role"].lower():
            found = True
            print(f"Found Wikidata-discovered person with role containing '{role_keyword}': {person.get('name', 'Unknown')}")
            break
    
    assert found, f"No Wikidata-discovered person with role containing '{role_keyword}'"

@then('at least {num:d} sanctions results should be included in the assessment data')
def step_impl(context, num):
    """Check if at least the specified number of sanctions results are included in the assessment data."""
    # Get the assessment data
    assessment_data = get_assessment_data(context.transaction_id)
    
    # Verify that we got data
    assert assessment_data, "No assessment data found"
    
    # Count sanctions results for all organizations
    org_sanctions_count = 0
    if "organizations" in assessment_data:
        for org in assessment_data["organizations"]:
            org_data = assessment_data["organizations"][org]
            if "sanctions" in org_data and org_data["sanctions"].get("data"):
                org_sanctions_count += len(org_data["sanctions"]["data"])
    
    # Count sanctions results for all people
    people_sanctions_count = 0
    if "people" in assessment_data:
        for person in assessment_data["people"]:
            person_data = assessment_data["people"][person]
            if "sanctions" in person_data and person_data["sanctions"].get("data"):
                people_sanctions_count += len(person_data["sanctions"]["data"])
    
    total_sanctions = org_sanctions_count + people_sanctions_count
    
    assert total_sanctions >= num, f"Expected at least {num} sanctions results, found {total_sanctions}"
    print(f"Found {total_sanctions} sanctions results in the assessment data")

@then('at least {num:d} PEP results should be included in the assessment data')
def step_impl(context, num):
    """Check if at least the specified number of PEP results are included in the assessment data."""
    # Get the assessment data
    assessment_data = get_assessment_data(context.transaction_id)
    
    # Verify that we got data
    assert assessment_data, "No assessment data found"
    
    # Count PEP results for all people
    pep_count = 0
    if "people" in assessment_data:
        for person in assessment_data["people"]:
            person_data = assessment_data["people"][person]
            if "pep" in person_data and person_data["pep"].get("data"):
                pep_count += len(person_data["pep"]["data"])
    
    assert pep_count >= num, f"Expected at least {num} PEP results, found {pep_count}"
    print(f"Found {pep_count} PEP results in the assessment data")
    
import json
import re
import requests
from behave import then
from test_steps import API_URL
import time

def count_jurisdictions_in_assessment_data(assessment_data):
    """
    Count the number of different jurisdictions mentioned in the assessment data.
    
    Args:
        assessment_data: The assessment data dictionary
        
    Returns:
        A set of jurisdiction names found in the assessment data
    """
    jurisdictions = set()
    
    # Common jurisdiction names to look for
    countries = [
        "usa", "uk", "russia", "china", "germany", "france", "italy", "spain",
        "switzerland", "luxembourg", "liechtenstein", "austria", "netherlands",
        "belgium", "ireland", "cyprus", "malta", "jersey", "guernsey", "isle of man",
        "cayman islands", "british virgin islands", "bvi", "bermuda", "bahamas",
        "panama", "seychelles", "mauritius", "singapore", "hong kong", "dubai",
        "uae", "united arab emirates", "qatar", "bahrain", "saudi arabia", "kuwait",
        "japan", "south korea", "india", "brazil", "mexico", "canada", "australia",
        "new zealand", "south africa", "nigeria", "kenya", "egypt", "israel",
        "turkey", "ukraine", "belarus", "kazakhstan", "estonia", "latvia", "lithuania",
        "poland", "czech republic", "slovakia", "hungary", "romania", "bulgaria",
        "croatia", "serbia", "greece", "monaco", "andorra", "san marino", "vatican",
        "gibraltar", "turks and caicos", "anguilla", "st. kitts and nevis",
        "antigua and barbuda", "dominica", "saint lucia", "barbados", "grenada",
        "trinidad and tobago", "venezuela", "colombia", "peru", "chile", "argentina",
        "uruguay", "paraguay", "ecuador", "bolivia", "costa rica", "panama", "belize",
        "guatemala", "honduras", "el salvador", "nicaragua", "malaysia", "indonesia",
        "thailand", "vietnam", "philippines", "myanmar", "cambodia", "laos",
        "bangladesh", "pakistan", "iran", "iraq", "syria", "lebanon", "jordan",
        "morocco", "algeria", "tunisia", "libya", "sudan", "ethiopia", "kenya",
        "uganda", "tanzania", "rwanda", "burundi", "democratic republic of congo",
        "republic of congo", "angola", "zambia", "zimbabwe", "mozambique",
        "madagascar", "mauritius", "seychelles", "comoros", "mayotte", "réunion",
        "yemen", "oman", "qatar", "bahrain"
    ]
    
    # Extract transaction text
    transaction_text = assessment_data.get("transaction_text", "").lower()
    
    # Check for jurisdictions in transaction text
    for country in countries:
        if country.lower() in transaction_text:
            jurisdictions.add(country.lower())
    
    # Check in organizations data
    for org_name, org_data in assessment_data.get("organizations", {}).items():
        # Check OpenCorporates data
        if "opencorporates" in org_data:
            opencorp_data = org_data["opencorporates"].get("data", {})
            if isinstance(opencorp_data, dict):
                jurisdiction = opencorp_data.get("jurisdiction_code", "").lower()
                if jurisdiction:
                    jurisdictions.add(jurisdiction)
                
                # Check address
                address = opencorp_data.get("registered_address", "").lower()
                for country in countries:
                    if country.lower() in address:
                        jurisdictions.add(country.lower())
        
        # Check for jurisdictions in organization name and entity type
        for country in countries:
            if country.lower() in org_name.lower():
                jurisdictions.add(country.lower())
    
    # Check in people data
    for person_name, person_data in assessment_data.get("people", {}).items():
        # Check PEP data
        if "pep" in person_data:
            pep_data = person_data["pep"].get("data", [])
            if isinstance(pep_data, list):
                for pep_item in pep_data:
                    if isinstance(pep_item, dict):
                        country = pep_item.get("country", "").lower()
                        if country:
                            jurisdictions.add(country)
    
    # Check Wikidata properties for countries
    for org_name, org_data in assessment_data.get("organizations", {}).items():
        if "wikidata" in org_data:
            wikidata_data = org_data["wikidata"].get("data", {})
            if isinstance(wikidata_data, dict):
                properties = wikidata_data.get("entity_info", {}).get("properties", {})
                for prop_name, prop_value in properties.items():
                    if "country" in prop_name.lower():
                        jurisdictions.add(prop_value.lower())
    
    return jurisdictions

def count_interconnected_entities(assessment_data):
    """
    Count the number of interconnected entities in the assessment data.
    
    Args:
        assessment_data: The assessment data dictionary
        
    Returns:
        A dictionary of entity relationships
    """
    entity_connections = {}
    
    # Track all entities
    all_entities = set()
    for org_name in assessment_data.get("organizations", {}):
        all_entities.add(org_name.lower())
    
    for person_name in assessment_data.get("people", {}):
        all_entities.add(person_name.lower())
    
    # Find connections between organizations and people
    for org_name, org_data in assessment_data.get("organizations", {}).items():
        entity_connections[org_name.lower()] = set()
        
        # Check Wikidata connections
        if "wikidata" in org_data:
            wikidata_data = org_data["wikidata"].get("data", {})
            associated_people = wikidata_data.get("associated_people", [])
            
            for person in associated_people:
                person_name = person.get("name", "").lower()
                if person_name:
                    entity_connections[org_name.lower()].add(person_name)
                    
                    # Add mutual connection
                    if person_name not in entity_connections:
                        entity_connections[person_name] = set()
                    entity_connections[person_name].add(org_name.lower())
    
    # Look for connections in the transaction text (simplistic approach)
    transaction_text = assessment_data.get("transaction_text", "").lower()
    
    for entity1 in all_entities:
        for entity2 in all_entities:
            if entity1 != entity2:
                # Check if both entities appear in the same paragraph
                paragraphs = transaction_text.split("\n\n")
                for para in paragraphs:
                    if entity1 in para and entity2 in para:
                        if entity1 not in entity_connections:
                            entity_connections[entity1] = set()
                        entity_connections[entity1].add(entity2)
    
    # Count entities with connections
    connected_entities = 0
    for entity, connections in entity_connections.items():
        if connections:
            connected_entities += 1
    
    return connected_entities, entity_connections

@then('at least {num:d} different jurisdictions should be referenced in the assessment data')
def step_impl(context, num):
    """Check if at least the specified number of different jurisdictions are referenced in the assessment data."""
    # Get the assessment data
    assessment_data = get_assessment_data(context.transaction_id)
    
    # Verify that we got data
    assert assessment_data, "No assessment data found"
    
    # Count jurisdictions
    jurisdictions = count_jurisdictions_in_assessment_data(assessment_data)
    
    assert len(jurisdictions) >= num, f"Expected at least {num} different jurisdictions in assessment data, found {len(jurisdictions)}: {jurisdictions}"
    print(f"Found {len(jurisdictions)} different jurisdictions in assessment data: {', '.join(jurisdictions)}")

@then('at least {num:d} interconnected entities should be identified in the assessment data')
def step_impl(context, num):
    """Check if at least the specified number of interconnected entities are identified in the assessment data."""
    # Get the assessment data
    assessment_data = get_assessment_data(context.transaction_id)
    
    # Verify that we got data
    assert assessment_data, "No assessment data found"
    
    # Count interconnected entities
    connected_count, entity_connections = count_interconnected_entities(assessment_data)
    
    assert connected_count >= num, f"Expected at least {num} interconnected entities in assessment data, found {connected_count}"
    
    # Print some details about the connections
    print(f"Found {connected_count} interconnected entities in assessment data")
    for entity, connections in entity_connections.items():
        if connections:
            print(f"  - {entity} is connected to: {', '.join(connections)}")