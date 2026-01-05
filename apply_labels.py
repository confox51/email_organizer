import json
import logging
import argparse
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from gmail_auth import get_service

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

def load_label_mappings(mapping_file='label_mappings.json'):
    try:
        with open(mapping_file, 'r') as f:
            label_map = json.load(f)
            # Create reverse mapping: Name -> ID
            return {v: k for k, v in label_map.items()}
    except FileNotFoundError:
        logging.error(f"{mapping_file} not found. Run get_label_mappings.py first.")
        return {}

def apply_label(service, email_id, category, name_to_id_map):
    """Applies a single label to an email."""
    label_id = name_to_id_map.get(category)
    if not label_id:
        # Prevent spamming logs for known missing categories?
        # But keeping warning is good for debugging.
        # logging.warning(f"Category '{category}' not found in mappings for email {email_id}.")
        return False

    try:
        body = {'addLabelIds': [label_id]}
        service.users().messages().modify(userId='me', id=email_id, body=body).execute()
        logging.info(f"Applied '{category}' to email {email_id}")
        return True
    except HttpError as error:
        logging.error(f"Error applying label to {email_id}: {error}")
        return False

def apply_labels_to_emails(input_file='classification_results_inbox.json'):
    # 1. Load Mappings
    name_to_id = load_label_mappings()
    if not name_to_id:
        return

    # 2. Load Classification Results
    try:
        with open(input_file, 'r') as f:
            classifications = json.load(f)
    except FileNotFoundError:
        logging.error(f"{input_file} not found.")
        return

    # 3. Authenticate
    service = get_service()
    if not service:
        logging.error("Could not authenticate.")
        return

    # 4. Apply Labels
    success_count = 0
    fail_count = 0
    skip_count = 0

    total_emails = len(classifications)
    logging.info(f"Starting label application for {total_emails} emails...")

    for i, email_data in enumerate(classifications):
        email_id = email_data.get('email_id')
        category = email_data.get('category')

        if not email_id or not category:
            skip_count += 1
            continue

        if apply_label(service, email_id, category, name_to_id):
            success_count += 1
        else:
            fail_count += 1
    
    logging.info("-" * 30)
    logging.info(f"Finished. Success: {success_count}, Failed: {fail_count}, Skipped: {skip_count}")

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Apply Gmail labels based on classification results.')
    parser.add_argument('--input', type=str, default='classification_results_inbox.json', 
                        help='Path to classification results JSON')
    args = parser.parse_args()
    
    apply_labels_to_emails(args.input)
