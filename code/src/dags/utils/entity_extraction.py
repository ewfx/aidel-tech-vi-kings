import os
import json
import logging
import re
import google.generativeai as genai
from dags.utils.gemini_util import create_genai_model

from dags.config.settings import (
    RESULTS_FOLDER
)

# Import the transaction folder utilities
from dags.utils.transaction_folder import (
    get_transaction_folder, save_transaction_data, load_transaction_data
)

# Configure logging
logger = logging.getLogger(__name__)


def extract_entities_from_text(transaction_text, transaction_id, **context):
    """
    Use Gemini to extract entities from transaction text.
    
    Args:
        transaction_text: The raw text of the transaction
        transaction_id: The ID of the transaction
        context: Airflow task context
        
    Returns:
        Dictionary of extracted entities
    """
    try:
        model = create_genai_model()

        logger.info(f"Extracting entities for transaction: {transaction_id}")
        
        if not transaction_text:
            raise ValueError("Transaction text is empty")
        
        # Create the transaction folder
        transaction_folder = get_transaction_folder(RESULTS_FOLDER, transaction_id)
        
        # Save the original transaction text
        with open(os.path.join(transaction_folder, "transaction.txt"), "w", encoding="utf-8") as f:
            f.write(transaction_text)
        
        # Create a prompt for entity extraction
        prompt = f"""
        You are a financial crime expert. Extract entities from the following transaction data:

        {transaction_text}

        Please identify:
        1. Organizations involved (sender and recipient companies/entities)
        2. People mentioned (directors, approvers, beneficiaries)
        3. Transaction details (amount, currency, purpose)
        4. Jurisdictions mentioned (countries, territories)
        
        Format your response as a JSON object with the following structure and don't include any other text or comments:
        {{
          "transaction_id": "string",
          "organizations": [
            {{
              "name": "string",
              "role": "sender|recipient|intermediary",
              "jurisdiction": "string",
              "entity_type": "corporation|shell_company|non_profit|government_agency|financial_institution"
            }}
          ],
          "people": [
            {{
              "name": "string",
              "role": "director|approver|beneficiary|other",
              "country": "string"
            }}
          ],
          "transaction": {{
            "amount": "string",
            "currency": "string",
            "purpose": "string",
            "date": "string"
          }},
          "jurisdictions": [
            "string"
          ]
        }}
        """

        # Generate a response from Gemini
        response = model.generate_content(prompt)
        result_text = response.text
        
        print(f"Gemini response: {result_text}")

        # Extract JSON from the response
        json_match = re.search(r'```json\s*(.*?)\s*```', result_text, re.DOTALL)
        if json_match:
            extracted_json = json_match.group(1)
        else:
            # Try to extract JSON directly
            json_start = result_text.find('{')
            json_end = result_text.rfind('}') + 1
            if json_start != -1 and json_end != -1:
                extracted_json = result_text[json_start:json_end]
            else:
                raise ValueError("Could not extract JSON from Gemini response")

        # Parse the JSON
        entities = json.loads(extracted_json)
        
        # Ensure transaction_id is set correctly
        entities["transaction_id"] = transaction_id
        
        # Log the result
        logger.info(f"Extracted entities: {entities}")
        
        # Save the extracted entities to the transaction folder
        save_transaction_data(RESULTS_FOLDER, transaction_id, "entities.json", entities)
            
        return entities
    
    except Exception as e:
        logger.error(f"Error extracting entities: {str(e)}")
        raise
