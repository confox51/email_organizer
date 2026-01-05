import os
import sys
import time
import base64
import logging
from typing import Dict, List, Set
import google.auth.exceptions
import gmail_auth
import classify_emails_groq as classifier
import db_client
from apply_labels import apply_label, load_label_mappings
from datetime import datetime

# --- Configuration ---
POLL_INTERVAL_SECONDS = 60
TAXONOMY_PATH = "taxonomy.md"

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def get_header_value(headers: List[Dict], name: str) -> str:
    for header in headers:
        if header['name'].lower() == name.lower():
            return header['value']
    return ""

def parse_email_body(payload: Dict) -> str:
    body = ""
    if 'parts' in payload:
        for part in payload['parts']:
            if part['mimeType'] == 'text/plain':
                data = part['body'].get('data')
                if data:
                    body += base64.urlsafe_b64decode(data).decode('utf-8')
            elif 'parts' in part:
                body += parse_email_body(part)
    elif payload.get('mimeType') == 'text/plain':
        data = payload['body'].get('data')
        if data:
            body += base64.urlsafe_b64decode(data).decode('utf-8')
    return body

def start_listening():
    logging.info("--- Starting Gmail Listener (Polling Mode - Groq) ---")
    
    service = gmail_auth.get_service()
    if not service:
        logging.error("Failed to authorize. Exiting application to trigger restart.")
        os._exit(1) # Force exit so Render sees the failure

    # 1. Initialize Resources
    try:
        system_prompt = classifier.get_system_prompt(TAXONOMY_PATH)
        label_mappings = load_label_mappings()
    except Exception as e:
        logging.error(f"Error loading resources: {e}. Exiting.")
        os._exit(1)

    # 2. Load History
    # Use Supabase for persistence
    # Note: Ensure DB connection is reliable
    processed_ids = db_client.get_processed_ids()
    logging.info(f"Loaded {len(processed_ids)} previously processed emails from storage.")

    logging.info(f"Listening for new emails every {POLL_INTERVAL_SECONDS} seconds...")

    while True:
        try:
            # Poll for unread in INBOX
            results = service.users().messages().list(
                userId='me', 
                q='label:INBOX', 
                maxResults=10
            ).execute()
            
            messages = results.get('messages', [])
            
            new_messages = [m for m in messages if m['id'] not in processed_ids]
            
            if new_messages:
                logging.info(f"Detected {len(new_messages)} new emails.")
                
                for msg in new_messages:
                    msg_id = msg['id']
                    
                    if msg_id in processed_ids: continue

                    logging.info(f"  Fetching {msg_id}...")
                    try:
                        message_full = service.users().messages().get(userId='me', id=msg_id, format='full').execute()
                    except Exception as e:
                         logging.error(f"Error fetching message {msg_id}: {e}")
                         continue
                    
                    payload = message_full.get('payload', {})
                    headers = payload.get('headers', [])
                    
                    email_data = {
                        'id': msg_id,
                        'threadId': message_full.get('threadId'),
                        'labelIds': message_full.get('labelIds', []),
                        'snippet': message_full.get('snippet', ''),
                        'date': get_header_value(headers, 'Date'),
                        'from': get_header_value(headers, 'From'),
                        'subject': get_header_value(headers, 'Subject'),
                        'body': parse_email_body(payload)
                    }
                    
                    logging.info(f"  Classifying: '{email_data['subject'][:40]}...'")
                    
                    try:
                        # Use Groq classifier
                        classification = classifier.classify_single_email(email_data, system_prompt)
                        category = classification.get("category")
                        
                        logging.info(f"  -> Classified as: {category}")

                        # Apply Label immediately
                        if category:
                            applied = apply_label(service, msg_id, category, label_mappings)
                            if applied:
                                logging.info(f"  -> Label applied.")
                            else:
                                logging.warning(f"  -> Failed to apply label.")

                        # Save to Storage
                        db_client.add_processed_id(msg_id)
                        processed_ids.add(msg_id)
                        
                    except Exception as e:
                        logging.error(f"  Error classifying {msg_id}: {e}")

            else:
                pass

        except google.auth.exceptions.RefreshError as e:
            logging.error(f"Authentication token expired or revoked: {e}. Exiting to trigger re-auth flow.")
            os._exit(1)
        except Exception as e:
            logging.critical(f"Critical error in poll loop: {e}. Exiting.")
            os._exit(1)
            
        time.sleep(POLL_INTERVAL_SECONDS)

if __name__ == "__main__":
    start_listening()
