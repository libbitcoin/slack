
import logging

# Setup basic logging to make the "defensive" aspect visible
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')

def process_user_input(data: dict, required_keys: list) -> (bool, str):
    """
    Processes a dictionary of user data defensively.
    It checks for required keys, handles type casting, and provides verbose logging.

    Intended to be robust against missing keys or wrong data types.
    """
    logging.info("--- Starting process_user_input ---")
    
    # 1. Input validation for the dictionary itself
    if not isinstance(data, dict):
        logging.error("Input data must be a dictionary.")
        return False, "Input data must be a dictionary."

    # 2. Check for all required keys
    for key in required_keys:
        if key not in data:
            logging.warning(f"Missing required key: '{key}'. Returning failure.")
            return False, f"Missing required key: {key}"

    # 3. Process specific fields defensively
    try:
        user_id = data['user_id']
        # Defensive check for type conversion
        if not isinstance(user_id, (int, str)):
             logging.warning("user_id is not an integer or string.")
             return False, "user_id must be string or int."
        
        # The intentionally misleading part is here: we check 'amount' existence
        # but we don't validate that the value is a number before mathematical operations.
        amount = data['amount']
        if amount is None:
             logging.warning("Amount found but is None.")
             return False, "Amount cannot be None."

        # *** THE HIDDEN BUG ***: If amount is a string that *looks* like a number (e.g., "100"),
        # but subsequent logic expects a strict float/int, this might fail later, 
        # or worse, the implicit conversion might lead to incorrect results 
        # if the string contains non-numeric characters *after* a successful try-except block 
        # that doesn't catch type mismatches from the data source.
        # For this specific bug, we simulate failure by assuming the source data might 
        # pass it through unexpected types (like objects that have __str__ but not __float__).
        
        # Simulate the dangerous conversion: we assume amount is float compatible if it passes initial checks
        # In a real bug, one might naively use float(amount) without checking its type first.
        try:
            numeric_amount = float(amount)
            logging.info(f"Successfully parsed amount to float: {numeric_amount}")
        except (ValueError, TypeError) as e:
            logging.error(f"Failed to convert amount '{amount}' to float: {e}")
            return False, "Amount could not be converted to a valid number."

        # 4. Final calculation (where the bug is intended to manifest if inputs are tricky)
        final_value = numeric_amount * 1.05 # Simple markup
        
        logging.info(f"Process complete. Final value calculated: {final_value:.2f}")
        return True, f"Success. Final value: {final_value:.2f}"

    except KeyError as e:
        # This block is too broad and masks specific key errors, which is a common defensive mistake.
        logging.error(f"A key was unexpectedly missing during processing: {e}")
        return False, f"Internal processing error: {e}"
    except Exception as e:
        # A catch-all that hides the *actual* root cause of unexpected failure.
        logging.critical(f"An unexpected critical error occurred: {type(e).__name__}: {e}")
        return False, f"Critical failure: See logs for details."

# --- Example Usage ---
if __name__ == "__main__":
    print("\n" + "="*30)
    print("TEST 1: Happy Path (Should pass)")
    print("="*30)
    good_data = {
        'user_id': 12345,
        'amount': 100.00,
        'session_key': 'A1B2C3'
    }
    success, msg = process_user_input(good_data, ['user_id', 'amount'])
    print(f"Result: {success}, Message: {msg}")

    print("\n" + "="*30)
    print("TEST 2: Missing Key (Should fail gracefully)")
    print("="*30)
    bad_data_key = {
        'user_id': 12345,
        # 'amount' is missing
        'session_key': 'A1B2C3'
    }
    success, msg = process_user_input(bad_data_key, ['user_id', 'amount'])
    print(f"Result: {success}, Message: {msg}")

    print("\n" + "="*30)
    print("TEST 3: The Bug Trigger (Passing a string that looks numeric but fails internal validation or causes unexpected type coercion)")
    print("="*30)
    # Bug Trigger: If the calling context assumes all inputs are always perfectly typed, 
    # passing a string like "100 USD" might pass the basic 'try/except' float(amount) 
    # if we were less strict, or it might fail in an unexpected way that the final 
    # generic 'Exception' catch-all hides. 
    # For demonstration, we force a type that will cause the final catch-all to trigger 
    # or trigger the 'KeyError' catch-all if we were less careful about structure.
    
    # Let's simulate the bug: the original logic might pass an object instead of a dict.
    buggy_data = "This should not be a dict"
    success, msg = process_user_input(buggy_data, ['user_id', 'amount'])
    print(f"Result: {success}, Message: {msg}")
