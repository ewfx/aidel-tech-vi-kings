import re
from behave import then
import requests

# Reuse the API_URL from the environment
from test_steps import API_URL

def get_transaction_network(transaction_id):
    """Get the network visualization data for a transaction."""
    response = requests.get(f"{API_URL}/transaction/{transaction_id}/network")
    if response.status_code != 200:
        return None
    return response.json()

def get_entity_history(transaction_id):
    """Get historical information for all entities in a transaction."""
    response = requests.get(f"{API_URL}/transaction/{transaction_id}/history")
    if response.status_code != 200:
        return None
    return response.json()

def count_distinct_risk_factors(risk_assessment):
    """Count the number of distinct risk factors mentioned in the assessment."""
    if not risk_assessment:
        return 0
        
    reason = risk_assessment.get('reason', '')
    evidence = risk_assessment.get('supporting_evidence', [])
    
    # Combine reason and evidence into a single text for analysis
    combined_text = reason + " " + " ".join(evidence)
    
    # List of known risk factor keywords
    risk_factors = [
        "shell company", "offshore", "high-risk jurisdiction", "tax haven",
        "politically exposed", "pep", "sanction", "adverse media",
        "layering", "beneficial owner", "complex structure", "round-trip",
        "trade-based", "money laundering", "terrorist financing", "corruption",
        "fraud", "bribery", "embezzlement", "blacklisted", "non-cooperative",
        "unregulated", "concealment", "nominee", "high-value", "cash intensive",
        "structuring", "integration", "placement", "smurfing", "hawala"
    ]
    
    # Count distinct factors
    found_factors = []
    for factor in risk_factors:
        if factor in combined_text.lower():
            found_factors.append(factor)
    
    return len(found_factors)

@then("at least {num:d} distinct risk factors should be identified")
def step_impl(context, num):
    """Check if at least the specified number of distinct risk factors are identified."""
    # Make sure we have the result
    assert hasattr(context, 'result'), "No transaction result available"
    
    # Count distinct risk factors
    factor_count = count_distinct_risk_factors(context.result)
    
    assert factor_count >= num, f"Expected at least {num} distinct risk factors, found {factor_count}"
    print(f"Found {factor_count} distinct risk factors in the assessment")

@then("the network analysis should show connected entities")
def step_impl(context):
    """Check if the network analysis shows connected entities."""
    # Get the network data
    network_data = get_transaction_network(context.transaction_id)
    
    # Check that we got data
    assert network_data, "No network data returned"
    
    # Check that there are nodes and links
    assert "nodes" in network_data, "No nodes in network data"
    assert "links" in network_data, "No links in network data"
    
    # Check that there are enough connections
    assert len(network_data["nodes"]) > 1, "Not enough nodes in network"
    assert len(network_data["links"]) > 0, "No connections between entities"
    
    # Store the network data for later steps
    context.network_data = network_data
    
    print(f"Network analysis contains {len(network_data['nodes'])} nodes and {len(network_data['links'])} connections")

@then("the transaction history should include previous high-risk transactions")
def step_impl(context):
    """Check if transaction history shows previous high-risk transactions."""
    # Get entity history data
    history_data = get_entity_history(context.transaction_id)
    
    # Check that we got data
    assert history_data, "No entity history data returned"
    
    # Look for high-risk previous transactions
    found_high_risk = False
    
    for entity_name, entity_data in history_data.items():
        # Check both organization and person history
        for entity_type in ["organization", "person"]:
            if entity_type in entity_data:
                # Check for high risk score in transaction history
                max_risk = entity_data[entity_type].get("max_risk_score")
                if max_risk is not None and max_risk >= 0.7:
                    found_high_risk = True
                    print(f"Found high-risk history for {entity_name} ({entity_type}) with risk score {max_risk}")
                    break
        
        if found_high_risk:
            break
    
    assert found_high_risk, "No previous high-risk transactions found in entity history"
    
    # Store the history data for later steps
    context.history_data = history_data

@then("the entity relationships should identify at least one politically exposed person")
def step_impl(context):
    """Check if entity relationships include at least one PEP."""
    # Make sure we have the network data
    if not hasattr(context, 'network_data'):
        context.execute_steps('Then the network analysis should show connected entities')
    
    # Look for PEP indicators in node labels and properties
    found_pep = False
    
    # Check both network data and the assessment text
    if hasattr(context, 'network_data'):
        for node in context.network_data["nodes"]:
            if "pep" in str(node).lower() or "politically exposed" in str(node).lower():
                found_pep = True
                print(f"Found PEP in network: {node.get('label')}")
                break
    
    # If not found in network, check the assessment text
    if not found_pep and hasattr(context, 'result'):
        reason = context.result.get('reason', '').lower()
        evidence = ' '.join(context.result.get('supporting_evidence', [])).lower()
        combined_text = reason + " " + evidence
        
        if "pep" in combined_text or "politically exposed" in combined_text:
            found_pep = True
            
            # Extract the name of the PEP if possible
            pep_match = re.search(r'(?:pep|politically exposed person)[:\s]*([\w\s]+)', combined_text, re.IGNORECASE)
            if pep_match:
                pep_name = pep_match.group(1).strip()
                print(f"Found PEP in assessment: {pep_name}")
            else:
                print("Found PEP reference in assessment but couldn't extract name")
    
    assert found_pep, "No politically exposed person identified in entity relationships"

@then("the risk assessment should identify cross-jurisdictional concerns")
def step_impl(context):
    """Check if risk assessment identifies cross-jurisdictional concerns."""
    # Make sure we have the result
    assert hasattr(context, 'result'), "No transaction result available"
    
    # Look for cross-jurisdictional indicators in the assessment
    reason = context.result.get('reason', '').lower()
    evidence = ' '.join(context.result.get('supporting_evidence', [])).lower()
    combined_text = reason + " " + evidence
    
    # List of cross-jurisdictional terms to look for
    jurisdictional_terms = [
        "cross-jurisdictional", "cross-border", "offshore", "tax haven",
        "multiple jurisdiction", "multiple countries", "international",
        "foreign", "overseas", "different jurisdiction", "high-risk jurisdiction"
    ]
    
    found_terms = []
    for term in jurisdictional_terms:
        if term in combined_text:
            found_terms.append(term)
    
    assert len(found_terms) > 0, "No cross-jurisdictional concerns identified in risk assessment"
    print(f"Found cross-jurisdictional concerns: {', '.join(found_terms)}")

@then("the pattern analysis should identify round-trip characteristics")
def step_impl(context):
    """Check if pattern analysis identifies round-trip transaction characteristics."""
    # Make sure we have the result
    assert hasattr(context, 'result'), "No transaction result available"
    
    # Look for round-trip indicators in the assessment
    reason = context.result.get('reason', '').lower()
    evidence = ' '.join(context.result.get('supporting_evidence', [])).lower()
    combined_text = reason + " " + evidence
    
    # List of round-trip terms to look for
    round_trip_terms = [
        "round-trip", "circular", "back-to-back", "layering", "return", 
        "related transaction", "previous transaction", "offsetting", 
        "mirror", "corresponding", "matching", "reversal"
    ]
    
    found_terms = []
    for term in round_trip_terms:
        if term in combined_text:
            found_terms.append(term)
    
    assert len(found_terms) > 0, "No round-trip transaction characteristics identified"
    print(f"Found round-trip characteristics: {', '.join(found_terms)}")

@then("the transaction should be flagged for potential trade-based money laundering")
def step_impl(context):
    """Check if transaction is flagged for potential trade-based money laundering."""
    # Make sure we have the result
    assert hasattr(context, 'result'), "No transaction result available"
    
    # Look for TBML indicators in the assessment
    reason = context.result.get('reason', '').lower()
    evidence = ' '.join(context.result.get('supporting_evidence', [])).lower()
    combined_text = reason + " " + evidence
    
    # List of TBML terms to look for
    tbml_terms = [
        "trade-based", "tbml", "over-invoicing", "under-invoicing", 
        "phantom shipment", "multiple invoicing", "trade discrepancy",
        "mis-invoicing", "false declaration", "commodity", "goods",
        "trade financing", "letter of credit", "price manipulation"
    ]
    
    found_terms = []
    for term in tbml_terms:
        if term in combined_text:
            found_terms.append(term)
    
    assert len(found_terms) > 0, "No trade-based money laundering indicators identified"
    print(f"Found TBML indicators: {', '.join(found_terms)}")

@then("the risk assessment should recommend enhanced due diligence")
def step_impl(context):
    """Check if risk assessment recommends enhanced due diligence."""
    # Make sure we have the result
    assert hasattr(context, 'result'), "No transaction result available"
    
    # Look for EDD recommendations in the assessment
    reason = context.result.get('reason', '').lower()
    evidence = ' '.join(context.result.get('supporting_evidence', [])).lower()
    combined_text = reason + " " + evidence
    
    # List of EDD terms to look for
    edd_terms = [
        "enhanced due diligence", "edd", "further investigation",
        "additional scrutiny", "closer examination", "more information",
        "deeper review", "thorough review", "detailed review",
        "additional checks", "elevated risk", "high risk", "investigation"
    ]
    
    found_terms = []
    for term in edd_terms:
        if term in combined_text:
            found_terms.append(term)
    
    assert len(found_terms) > 0, "No enhanced due diligence recommendation identified"
    print(f"Found enhanced due diligence recommendations: {', '.join(found_terms)}")

@then("the beneficial ownership analysis should identify PEP connections")
def step_impl(context):
    """Check if beneficial ownership analysis identifies PEP connections."""
    # Make sure we have the result
    assert hasattr(context, 'result'), "No transaction result available"
    
    # Look for beneficial ownership and PEP connections in the assessment
    reason = context.result.get('reason', '').lower()
    evidence = ' '.join(context.result.get('supporting_evidence', [])).lower()
    combined_text = reason + " " + evidence
    
    # Need to find both beneficial ownership and PEP terms
    ownership_terms = [
        "beneficial owner", "ubo", "ultimate beneficial", "real owner",
        "beneficial ownership", "true owner", "ownership structure"
    ]
    
    pep_terms = [
        "pep", "politically exposed", "political figure", "government official",
        "senior official", "public official", "politician", "political connection"
    ]
    
    found_ownership = any(term in combined_text for term in ownership_terms)
    found_pep = any(term in combined_text for term in pep_terms)
    
    assert found_ownership and found_pep, "No beneficial ownership with PEP connections identified"
    print("Successfully identified beneficial ownership with PEP connections")

@then("the risk assessment should identify layered ownership structures")
def step_impl(context):
    """Check if risk assessment identifies layered ownership structures."""
    # Make sure we have the result
    assert hasattr(context, 'result'), "No transaction result available"
    
    # Look for layered ownership indicators in the assessment
    reason = context.result.get('reason', '').lower()
    evidence = ' '.join(context.result.get('supporting_evidence', [])).lower()
    combined_text = reason + " " + evidence
    
    # List of layered ownership terms to look for
    layered_terms = [
        "layered", "complex structure", "multiple layers", "nested",
        "chain of ownership", "indirect ownership", "ownership chain",
        "corporate veil", "holding company", "subsidiary", "parent company",
        "shell company", "nominee", "trust", "foundation", "intricate"
    ]
    
    found_terms = []
    for term in layered_terms:
        if term in combined_text:
            found_terms.append(term)
    
    assert len(found_terms) > 0, "No layered ownership structure indicators identified"
    print(f"Found layered ownership structure indicators: {', '.join(found_terms)}")