import logging
import google.generativeai as genai
from config.settings import (
    gemini_key_rotator, 
    GEMINI_MODEL, 
    GEMINI_TEMPERATURE, 
    GEMINI_TOP_P, 
    GEMINI_TOP_K, 
    GEMINI_MAX_OUTPUT_TOKENS
)

def create_genai_model(max_retries=3):
    """
    Create a Generative AI model with key rotation and retry logic
    
    :param max_retries: Maximum number of key rotation attempts
    :return: Configured GenerativeModel instance
    """
    logger = logging.getLogger(__name__)
    
    # Safety settings to reduce blocking
    safety_settings = {
        genai.types.HarmCategory.HARM_CATEGORY_HARASSMENT: genai.types.HarmBlockThreshold.BLOCK_NONE,
        genai.types.HarmCategory.HARM_CATEGORY_HATE_SPEECH: genai.types.HarmBlockThreshold.BLOCK_NONE,
        genai.types.HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT: genai.types.HarmBlockThreshold.BLOCK_NONE,
        genai.types.HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT: genai.types.HarmBlockThreshold.BLOCK_NONE,
    }
    
    generation_config = {
        "temperature": GEMINI_TEMPERATURE,
        "top_p": GEMINI_TOP_P,
        "top_k": GEMINI_TOP_K,
        "max_output_tokens": GEMINI_MAX_OUTPUT_TOKENS,
    }
    
    # Track used keys to prevent repeated failures
    used_keys = set()
    
    for attempt in range(max_retries):
        try:
            # Get a new key
            current_key = gemini_key_rotator.get_key()
            
            # Skip keys we've already tried in this round
            if current_key in used_keys:
                continue
            
            # Configure Gemini with the current key
            genai.configure(api_key=current_key)
            
            # Create model
            model = genai.GenerativeModel(
                model_name=GEMINI_MODEL,
                generation_config=generation_config,
                safety_settings=safety_settings
            )
            
            return model
        
        except Exception as e:
            logger.warning(f"Key rotation attempt {attempt + 1} failed: {e}")
            
            # Mark the current key as failed
            gemini_key_rotator.mark_key_failed(current_key)
            used_keys.add(current_key)
            
            # If we've exhausted all keys, raise the last exception
            if attempt == max_retries - 1 or gemini_key_rotator.get_key_count() <= len(used_keys):
                logger.error("All Gemini API keys have failed.")
                raise
    
    raise RuntimeError("Unable to create Generative AI model after multiple attempts")