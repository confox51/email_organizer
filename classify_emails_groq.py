
import json
import os
import time
import datetime
import re
from typing import List, Dict, Optional
from dotenv import load_dotenv
from groq import Groq, RateLimitError

# Load environment variables
load_dotenv()

# Configuration
DATASET_PATH = "emails_dataset_2025-12-23_10-27-03.json"
TAXONOMY_PATH = "taxonomy.md"
OUTPUT_PATH = "classification_results.json"
MODELS = ["openai/gpt-oss-120b", "moonshotai/kimi-k2-instruct-0905"]
GROQ_API_KEY = os.getenv("GROQ_API_KEY")

if not GROQ_API_KEY:
    print("Error: GROQ_API_KEY not found in environment variables.")
    exit(1)

client = Groq(api_key=GROQ_API_KEY)

class RateLimiter:
    def __init__(self, requests_per_minute: int, tokens_per_minute: int):
        self.rpm_limit = requests_per_minute
        self.tpm_limit = tokens_per_minute
        self.request_timestamps = []
        self.token_timestamps = [] # Store (timestamp, token_count) tuples

    def wait_if_needed(self, estimated_tokens: int):
        now = time.time()
        
        # Prune old timestamps (older than 60 seconds)
        self.request_timestamps = [t for t in self.request_timestamps if now - t < 60]
        self.token_timestamps = [t for t in self.token_timestamps if now - t[0] < 60]

        # Check RPM
        if len(self.request_timestamps) >= self.rpm_limit:
            wait_time = 60 - (now - self.request_timestamps[0])
            if wait_time > 0:
                print(f"Rate limit (RPM) reached. Waiting {wait_time:.2f} seconds...")
                time.sleep(wait_time + 0.1) # Add buffer
                now = time.time() # Update now
                # Re-prune after waiting
                self.request_timestamps = [t for t in self.request_timestamps if now - t < 60]

        # Check TPM
        current_tokens = sum(t[1] for t in self.token_timestamps)
        if current_tokens + estimated_tokens > self.tpm_limit:
             # Find how long to wait to free up enough tokens
            tokens_needed = (current_tokens + estimated_tokens) - self.tpm_limit
            
            # Simple heuristic: wait until oldest tokens expire until we have room
            # This is a bit complex to calculate perfectly without a loop, so strict simple wait is safer
            # Find the timestamp where enough tokens expire
            tokens_freed = 0
            wait_until_timestamp = now
            for ts, count in self.token_timestamps:
                tokens_freed += count
                if tokens_freed >= tokens_needed:
                    wait_until_timestamp = ts + 60
                    break
            
            wait_time = wait_until_timestamp - now
            if wait_time > 0:
                print(f"Rate limit (TPM) reached. Waiting {wait_time:.2f} seconds...")
                time.sleep(wait_time + 0.1)
                now = time.time()

    def record_request(self, token_count: int):
        now = time.time()
        self.request_timestamps.append(now)
        self.token_timestamps.append((now, token_count))

# Initialize Rate Limiter
# 30 requests/min, 8000 tokens/min
limiter = RateLimiter(requests_per_minute=30, tokens_per_minute=8000)

def load_dataset(path: str) -> List[Dict]:
    with open(path, 'r') as f:
        data = json.load(f)
    print(f"Loaded {len(data)} emails.")
    return data

def parse_date(date_str: str) -> datetime.datetime:
    # Handle various date formats including "(UTC)"
    cleaned_date = re.sub(r'\s*\(.*\)$', '', date_str).strip()
    try:
        # Example: "Tue, 23 Dec 2025 03:56:32 +0000"
        return datetime.datetime.strptime(cleaned_date, "%a, %d %b %Y %H:%M:%S %z")
    except ValueError:
        try:
             # Example: "Tue, 16 Dec 2025 18:10:30 -0800"
             return datetime.datetime.strptime(cleaned_date, "%a, %d %b %Y %H:%M:%S %z")
        except ValueError:
            # Fallback for now, could add more formats
            return datetime.datetime.now(datetime.timezone.utc)

def get_system_prompt(path: str) -> str:
    with open(path, 'r') as f:
        content = f.read()
    
    # Extract logic similar to the notebook
    categories = []
    sections = re.split(r'^##\s+', content, flags=re.MULTILINE)[1:]
    
    prompt = "You are an intelligent email classification engine. Your goal is to organize a user's inbox to achieve \"Inbox Zero\" by categorizing emails into strict mapped folders.\n"
    prompt += "### Categories (Mutually Exclusive)\n"
    prompt += "You must assign exactly one of the following categories to each email. Do not invent new categories.\n"
    
    for i, section in enumerate(sections, 1):
        lines = section.strip().split('\n')
        header = lines[0].strip()
        category_name = re.sub(r'^\d+\.\s*', '', header)
        
        description = ""
        examples = ""
        for line in lines[1:]:
            if line.strip().startswith('*   **Description**:'):
                description = line.strip().replace('*   **Description**:', '').strip()
            elif line.strip().startswith('*   **Examples**:'):
                examples = line.strip().replace('*   **Examples**:', '').strip()
        
        if category_name:
            prompt += f"{i}. **{category_name}**\n"
            prompt += f"   - Description: {description}\n"
            prompt += f"   - Examples: {examples}\n"
            
    prompt += "### Output Format\n"
    prompt += "Return a JSON object with the email `id` and the assigned `category` and `reasoning`.\n"
    prompt += "Example:\n"
    prompt += "{\n"
    prompt += "  \"id\": \"19b382636b67d677\",\n"
    prompt += "  \"category\": \"Career & Professional\",\n"
    prompt += "  \"reasoning\": \"Email is a thread regarding a job application and interview feedback.\"\n"
    prompt += "}\n"
    prompt += "### formatting_instructions\n"
    prompt += "- The \"category\" value must MATCH EXACTLY one of the bolded titles above.\n"
    prompt += "- Return ONLY valid JSON. Do not include markdown formatting like ```json ... ```.\n"
    
    return prompt

def classify_email(email: Dict, system_content: str, model: str) -> Dict:
    # Prepare email content for the prompt
    email_content = {
        "id": email.get("id"),
        "from": email.get("from"),
        "subject": email.get("subject"),
        "snippet": email.get("snippet"),
        "body": email.get("body", "")[:1000] # Truncate body to save tokens
    }
    user_content = json.dumps(email_content, indent=2)
    
    # Estimate tokens (very rough approximation: 4 chars / token)
    # Input + Output (assume ~200 output tokens)
    estimated_input_chars = len(system_content) + len(user_content)
    estimated_tokens = (estimated_input_chars // 4) + 200
    
    limiter.wait_if_needed(estimated_tokens)
    
    try:
        completion = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": system_content},
                {"role": "user", "content": f"Classify this email:\n{user_content}"}
            ],
            temperature=0,
            response_format={"type": "json_object"}
        )
        
        limiter.record_request(estimated_tokens) # Update with actual usage if available, but staying conservative with estimate is fine
        
        response_content = completion.choices[0].message.content
        return json.loads(response_content)
        
    except RateLimitError as e:
        print(f"Hit 429 RateLimitError for {model}. Waiting 60s...")
        time.sleep(60)
        # Retry once
        return classify_email(email, system_content, model)
    except Exception as e:
        print(f"Error classifying email {email.get('id')} with {model}: {e}")
        return {"category": "Error", "reasoning": str(e)}

def main():
    # 1. Load Data
    data = load_dataset(DATASET_PATH)
    
    # 2. Sort Data (Oldest First)
    for email in data:
        email['_parsed_date'] = parse_date(email.get('date', ''))
    
    sorted_data = sorted(data, key=lambda x: x['_parsed_date'])
    
    # 3. Take Oldest 100
    top_100 = sorted_data[:100]
    print(f"Processing {len(top_100)} oldest emails.")
    print(f"Oldest: {top_100[0]['date']}")
    print(f"Newest of batch: {top_100[-1]['date']}")
    
    # 4. Prepare System Prompt
    system_prompt = get_system_prompt(TAXONOMY_PATH)
    
    # Load existing results if any
    results = []
    if os.path.exists(OUTPUT_PATH):
        try:
            with open(OUTPUT_PATH, 'r') as f:
                results = json.load(f)
            print(f"Resuming... Loaded {len(results)} existing results.")
        except json.JSONDecodeError:
            print("Warning: Could not decode existing results. Starting fresh.")
    
    existing_ids = {r['email_id'] for r in results}
    
    # 5. Process Loop
    for i, email in enumerate(top_100):
        if email.get('id') in existing_ids:
            print(f"[{i+1}/{len(top_100)}] Skipping {email.get('id')} (already processed).")
            continue

        print(f"[{i+1}/{len(top_100)}] Processing {email.get('id')}...")
        
        row = {
            "email_id": email.get("id"),
            "subject": email.get("subject"),
            "date": email.get("date")
        }
        
        for model in MODELS:
            name = "gpt" if "gpt" in model else "kimi"
            print(f"  - Classifying with {name}...")
            
            result = classify_email(email, system_prompt, model)
            
            row[f"{name}_category"] = result.get("category")
            row[f"{name}_reasoning"] = result.get("reasoning")
            
        results.append(row)
        
        # Save incrementally
        with open(OUTPUT_PATH, 'w') as f:
            json.dump(results, f, indent=2)
        
    print(f"Results saved to {OUTPUT_PATH}")
    
    # 7. Comparison Summary
    print("\n--- Summary of Differences ---")
    disagreements = [r for r in results if r.get('gpt_category') != r.get('kimi_category')]
    
    print(f"Total Emails: {len(results)}")
    print(f"Agreements: {len(results) - len(disagreements)}")
    print(f"Disagreements: {len(disagreements)}")
    
    if disagreements:
        print("\nDisagreements details:")
        # Display as a dataframe-like table
        header = f"{'Email ID':<18} | {'GPT Category':<25} | {'Kimi Category':<25}"
        print(header)
        print("-" * len(header))
        for d in disagreements:
            print(f"{d['email_id']:<18} | {str(d.get('gpt_category', 'N/A'))[:25]:<25} | {str(d.get('kimi_category', 'N/A'))[:25]:<25}")

def classify_single_email(email: Dict, system_prompt: str, model: str = "openai/gpt-oss-120b") -> Dict:
    """Classifies a single email object using the provided system prompt. Defaults to GPT-OSS-120B."""
    return classify_email(email, system_prompt, model)

def extract_categories_from_taxonomy(path: str) -> List[Dict[str, str]]:
    """Helper to extract categories (compatible with the other script's interface)."""
    # This script actually parses inside get_system_prompt, but let's just 
    # provide a wrapper if needed or just use get_system_prompt directly.
    # For now, the listener calls extract_categories... then get_system_prompt.
    # But this script's get_system_prompt does it all in one.
    # So we should adapt the listener or this script.
    # Easier to just let the listener use this script's get_system_prompt directly.
    pass

if __name__ == "__main__":
    main()
