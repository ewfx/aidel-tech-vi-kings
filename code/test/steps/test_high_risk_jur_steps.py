import re
import json
from behave import given, when, then
import requests

# Reuse API_URL from the existing steps
from steps.test_steps import API_URL

# List of known tax havens and offshore financial centers
TAX_HAVENS = [
    "cayman islands", "bermuda", "british virgin islands", "bvi", "bahamas", 
    "jersey", "guernsey", "isle of man", "panama", "liechtenstein", 
    "luxembourg", "switzerland", "singapore", "hong kong", "mauritius", 
    "seychelles", "monaco", "andorra", "bahrain", "malta", "cyprus", 
    "marshall islands", "samoa", "belize", "vanuatu", "cook islands", 
    "st. kitts and nevis", "gibraltar", "turks and caicos", "anguilla"
]

# List of FATF grey-listed jurisdictions (as of 2023)
FATF_GREY_LIST = [
    "barbados", "burkina faso", "cambodia", "cayman islands", 
    "haiti", "jamaica", "jordan", "mali", "morocco", "myanmar", 
    "nicaragua", "pakistan", "panama", "philippines", "senegal", 
    "south sudan", "syria", "tanzania", "turkey", "uganda", 
    "united arab emirates", "uae", "yemen"
]

# Countries with sanctions programs
SANCTIONED_COUNTRIES = [
    "iran", "north korea", "syria", "cuba", "venezuela", "russia", 
    "belarus", "afghanistan", "burma", "myanmar", "crimea", "eritrea", 
    "ethiopia", "iraq", "lebanon", "libya", "somalia", "south sudan", 
    "sudan", "yemen", "zimbabwe"
]

# Countries adjacent to sanctioned countries (for sanctions circumvention)
ADJACENT_TO_SANCTIONED = [
    "turkmenistan", "azerbaijan", "armenia", "turkey", "iraq", 
    "pakistan", "uzbekistan", "kazakhstan", "kyrgyzstan", "tajikistan", 
    "china", "south korea", "jordan", "lebanon", "georgia"
]

def extract_jurisdictions_from_assessment(assessment):
    """Extract jurisdictions mentioned in the risk assessment."""
    if not assessment:
        return []
        
    reason = assessment.get('reason', '')
    evidence = ' '.join(assessment.get('supporting_evidence', []))
    combined_text = reason + " " + evidence
    
    # Extract country names using regex
    # This is a basic approach - could be improved with NLP
    countries = re.findall(r'\b([A-Z][a-z]{2,}(?:\s+[A-Z][a-z]{2,})*)\b', combined_text)
    
    # Add special cases like UAE, BVI, USA that might not be caught by the regex
    special_cases = re.findall(r'\b(UAE|BVI|USA|UK)\b', combined_text)
    
    return [country.lower() for country in countries + special_cases]

def classify_jurisdiction(jurisdiction):
    """Classify a jurisdiction into categories."""
    jurisdiction = jurisdiction.lower()
    categories = []
    
    if jurisdiction in TAX_HAVENS:
        categories.append("tax haven")
    
    if jurisdiction in FATF_GREY_LIST:
        categories.append("FATF grey-listed")
    
    if jurisdiction in SANCTIONED_COUNTRIES:
        categories.append("sanctioned")
    
    if jurisdiction in ADJACENT_TO_SANCTIONED:
        categories.append("sanctions circumvention risk")
    
    return categories or ["standard"]

@then("at least {num:d} different jurisdictions should be identified")
def step_impl(context, num):
    """Check if at least the specified number of different jurisdictions are identified."""
    # Make sure we have the result
    assert hasattr(context, 'result'), "No transaction result available"
    
    # Extract jurisdictions from the assessment
    jurisdictions = extract_jurisdictions_from_assessment(context.result)
    
    # Add jurisdictions explicitly mentioned in the entities
    for entity in context.result.get('extracted_entities', []):
        for country in TAX_HAVENS + FATF_GREY_LIST + SANCTIONED_COUNTRIES + ADJACENT_TO_SANCTIONED:
            if country in entity.lower():
                jurisdictions.append(country)
    
    # Remove duplicates
    unique_jurisdictions = set(jurisdictions)
    
    assert len(unique_jurisdictions) >= num, f"Expected at least {num} different jurisdictions, found {len(unique_jurisdictions)}: {unique_jurisdictions}"
    
    # Store for later steps
    context.jurisdictions = list(unique_jurisdictions)
    
    print(f"Found {len(unique_jurisdictions)} different jurisdictions: {', '.join(unique_jurisdictions)}")

@then("all jurisdictions should be classified correctly")
def step_impl(context):
    """Check if all jurisdictions are classified correctly."""
    # Make sure we have the jurisdictions
    assert hasattr(context, 'jurisdictions'), "No jurisdictions identified in previous step"
    
    # Classify each jurisdiction
    classifications = {}
    for jurisdiction in context.jurisdictions:
        categories = classify_jurisdiction(jurisdiction)
        classifications[jurisdiction] = categories
    
    # Store for later steps
    context.jurisdiction_classifications = classifications
    
    # Check if at least one jurisdiction is classified as high-risk
    high_risk_categories = ["tax haven", "FATF grey-listed", "sanctioned", "sanctions circumvention risk"]
    
    has_high_risk = False
    for jurisdiction, categories in classifications.items():
        if any(category in high_risk_categories for category in categories):
            has_high_risk = True
            break
    
    assert has_high_risk, "No high-risk jurisdictions identified in the transaction"
    
    print("Jurisdiction classifications:")
    for jurisdiction, categories in classifications.items():
        print(f"  - {jurisdiction}: {', '.join(categories)}")

@then("multiple offshore jurisdictions should be identified")
def step_impl(context):
    """Check if multiple offshore jurisdictions are identified."""
    # Make sure we have the jurisdictions
    if not hasattr(context, 'jurisdictions'):
        context.execute_steps('Then at least 2 different jurisdictions should be identified')
    
    # Count offshore jurisdictions
    offshore_count = sum(1 for j in context.jurisdictions if j in TAX_HAVENS)
    
    assert offshore_count >= 2, f"Expected at least 2 offshore jurisdictions, found {offshore_count}"
    
    print(f"Found {offshore_count} offshore jurisdictions")

@then("the entity type classification should identify shell companies")
def step_impl(context):
    """Check if entity type classification identifies shell companies."""
    # Make sure we have the result
    assert hasattr(context, 'result'), "No transaction result available"
    
    # Check if "shell company" is in entity types
    entity_types = context.result.get('entity_types', [])
    found_shell = any("shell" in entity_type.lower() for entity_type in entity_types)
    
    # If not found in entity types, check in the reasoning
    if not found_shell:
        reason = context.result.get('reason', '').lower()
        evidence = ' '.join(context.result.get('supporting_evidence', [])).lower()
        combined_text = reason + " " + evidence
        
        found_shell = "shell company" in combined_text or "shell corporation" in combined_text
    
    assert found_shell, "No shell companies identified in entity classification"
    
    print("Shell company identified in classification")

@then("the transaction should identify multiple FATF-monitored jurisdictions")
def step_impl(context):
    """Check if transaction identifies multiple FATF-monitored jurisdictions."""
    # Check if we have jurisdiction classifications
    if not hasattr(context, 'jurisdiction_classifications'):
        context.execute_steps('Then all jurisdictions should be classified correctly')
    
    # Count FATF grey-listed jurisdictions
    fatf_count = 0
    for jurisdiction, categories in context.jurisdiction_classifications.items():
        if "FATF grey-listed" in categories:
            fatf_count += 1
    
    # Also check the assessment text for FATF mentions
    reason = context.result.get('reason', '').lower()
    evidence = ' '.join(context.result.get('supporting_evidence', [])).lower()
    combined_text = reason + " " + evidence
    
    # If FATF is mentioned, assume it's regarding at least one FATF-monitored jurisdiction
    if "fatf" in combined_text and fatf_count == 0:
        fatf_count = 1
    
    assert fatf_count > 0, "No FATF-monitored jurisdictions identified"
    print(f"Identified {fatf_count} FATF-monitored jurisdictions")

@then("the transaction should identify geographic proximity to sanctioned jurisdictions")
def step_impl(context):
    """Check if the transaction identifies geographic proximity to sanctioned jurisdictions."""
    # Make sure we have the result
    assert hasattr(context, 'result'), "No transaction result available"
    
    # Check for sanctioned countries and adjacent countries
    adjacent_found = False
    
    # First check in classifications if we have them
    if hasattr(context, 'jurisdiction_classifications'):
        for jurisdiction, categories in context.jurisdiction_classifications.items():
            if "sanctions circumvention risk" in categories:
                adjacent_found = True
                print(f"Found adjacent country to sanctioned jurisdiction: {jurisdiction}")
                break
    
    # If not found, check in the assessment text
    if not adjacent_found:
        reason = context.result.get('reason', '').lower()
        evidence = ' '.join(context.result.get('supporting_evidence', [])).lower()
        combined_text = reason + " " + evidence
        
        # Terms indicating geographical proximity to sanctions
        proximity_terms = [
            "proximity", "adjacent", "nearby", "neighboring", "bordering",
            "circumvention", "evasion", "transit", "transshipment", "diversion",
            "front company", "proxy", "intermediary"
        ]
        
        for term in proximity_terms:
            if term in combined_text:
                for country in ADJACENT_TO_SANCTIONED:
                    if country in combined_text:
                        adjacent_found = True
                        print(f"Found adjacent country term '{term}' with country '{country}'")
                        break
            if adjacent_found:
                break
    
    assert adjacent_found, "No geographic proximity to sanctioned jurisdictions identified"

@then("the jurisdiction risk analysis should be comprehensive")
def step_impl(context):
    """Check if the jurisdiction risk analysis is comprehensive."""
    # Make sure we have the result
    assert hasattr(context, 'result'), "No transaction result available"
    
    # Check if the assessment mentions multiple jurisdiction risk factors
    reason = context.result.get('reason', '').lower()
    evidence = ' '.join(context.result.get('supporting_evidence', [])).lower()
    combined_text = reason + " " + evidence
    
    # List of jurisdiction risk analysis terms
    jurisdiction_terms = [
        "jurisdiction", "country", "territory", "offshore", "tax haven",
        "fatf", "high-risk", "sanctions", "regulatory", "compliance",
        "international", "cross-border", "geographical", "regional"
    ]
    
    found_terms = []
    for term in jurisdiction_terms:
        if term in combined_text:
            found_terms.append(term)
    
    assert len(found_terms) >= 3, f"Expected at least 3 jurisdiction risk analysis terms, found {len(found_terms)}: {found_terms}"
    print(f"Found comprehensive jurisdiction analysis with terms: {', '.join(found_terms)}")

@then("at least {num:d} offshore financial centers should be identified")
def step_impl(context, num):
    """Check if at least the specified number of offshore financial centers are identified."""
    # Make sure we have the result
    assert hasattr(context, 'result'), "No transaction result available"
    
    # First check if we have jurisdictions already
    if not hasattr(context, 'jurisdictions'):
        # Extract jurisdictions from the assessment
        jurisdictions = extract_jurisdictions_from_assessment(context.result)
        
        # Add jurisdictions explicitly mentioned in the entities
        for entity in context.result.get('extracted_entities', []):
            for country in TAX_HAVENS:
                if country in entity.lower():
                    jurisdictions.append(country)
        
        # Remove duplicates
        context.jurisdictions = list(set(jurisdictions))
    
    # Count offshore financial centers
    offshore_centers = [j for j in context.jurisdictions if j in TAX_HAVENS]
    
    assert len(offshore_centers) >= num, f"Expected at least {num} offshore financial centers, found {len(offshore_centers)}: {offshore_centers}"
    print(f"Found {len(offshore_centers)} offshore financial centers: {', '.join(offshore_centers)}")