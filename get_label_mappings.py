import os.path
import json
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

# If modifying these scopes, delete the file token.json.
SCOPES = ['https://www.googleapis.com/auth/gmail.modify']

def get_credentials():
    """Gets valid user credentials from storage or initiates OAuth2 flow."""
    creds = None
    if os.path.exists('token.json'):
        creds = Credentials.from_authorized_user_file('token.json', SCOPES)
    
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            if not os.path.exists('credentials.json'):
                print("Error: credentials.json not found.")
                return None
            flow = InstalledAppFlow.from_client_secrets_file(
                'credentials.json', SCOPES)
            creds = flow.run_local_server(port=0)
        
        with open('token.json', 'w') as token:
            token.write(creds.to_json())
    return creds

def fetch_label_mappings():
    """Fetches Gmail label ID to Name mappings."""
    creds = get_credentials()
    if not creds:
        return {}

    try:
        service = build('gmail', 'v1', credentials=creds)
        results = service.users().labels().list(userId='me').execute()
        labels = results.get('labels', [])

        if not labels:
            print('No labels found.')
            return {}

        mapping = {}
        for label in labels:
            mapping[label['id']] = label['name']
        
        return mapping

    except Exception as e:
        print(f'An error occurred: {e}')
        return {}

def main():
    """Fetches and prints Gmail label ID to Name mappings."""
    mapping = fetch_label_mappings()
    
    if not mapping:
        return

    print(f"{'Label ID':<40} | {'Label Name'}")
    print("-" * 60)
    
    for label_id, label_name in mapping.items():
        print(f"{label_id:<40} | {label_name}")

    # No longer saving to JSON file since we fetch dynamically now

