import json
from typing import Dict
from google import genai   
# -----------------------------
# SET YOUR API KEY HERE
# -----------------------------

client = genai.Client(api_key="AIzaSyDo-40Fj6lwmFWXRpE-3ilwtoN-_I1XQWY")  
# -----------------------------
# SYSTEM PROMPT
# -----------------------------
SYSTEM_PROMPT = """
You are a strict JSON extraction system.

Extract:
- issue_category (login_issue, billing_issue, network_issue, app_issue, general_issue)
- urgency (low, medium, high)
- sentiment (positive, negative, neutral)
- one_sentence_summary (exactly one sentence)

RULES:
- Return ONLY JSON
- No extra text
- Always include all fields
- If unclear:
    urgency = "medium"
    sentiment = dominant tone

FORMAT:
{
  "issue_category": "...",
  "urgency": "low|medium|high",
  "sentiment": "positive|negative|neutral",
  "one_sentence_summary": "..."
}
"""
# -----------------------------
# FALLBACK
# -----------------------------

def fallback_extractor(ticket: str) -> Dict:
    text = ticket.lower()

    if "internet" in text:
        category = "network_issue"
    elif "login" in text:
        category = "login_issue"
    elif "billing" in text:
        category = "billing_issue"
    elif "crash" in text or "app" in text:
        category = "app_issue"
    else:
        category = "general_issue"

    if "urgent" in text or "immediately" in text:
        urgency = "high"
    elif "not urgent" in text:
        urgency = "low"
    else:
        urgency = "medium"

    if "thank" in text:
        sentiment = "positive"
    elif "frustrat" in text or "down" in text:
        sentiment = "negative"
    else:
        sentiment = "neutral"

    summary = ticket.strip().split("\n")[0].strip()
    if not summary.endswith("."):
        summary += "."

    return {
        "issue_category": category,
        "urgency": urgency,
        "sentiment": sentiment,
        "one_sentence_summary": summary
    }

# -----------------------------
# EXTRACTION
# -----------------------------
def extract_ticket_data(ticket: str) -> Dict:
    prompt = SYSTEM_PROMPT + "\n\nTicket:\n" + ticket

    try:
        response = client.models.generate_content(
            model="gemini-1.5-flash",  
            contents=prompt
        )

        text = response.text.strip()
        return json.loads(text)

    except Exception as e:
        print("API ERROR:", e)
        print("Using fallback...\n")
        return fallback_extractor(ticket)
# -----------------------------
# VALIDATION
# -----------------------------

def validate_output(data: Dict):
    required = ["issue_category", "urgency", "sentiment", "one_sentence_summary"]

    for field in required:
        if field not in data:
            print("WARNING: Missing", field)

    print("Output validated\n")

# -----------------------------
# TEST CASES
# -----------------------------

tickets = [
    "My internet has been down for 3 days and no one is responding!",
    "Unable to login since yesterday.",
    "Billing issue still exists.",
    "App crashes after update.",
    "Dashboard is slow."
]

print("\nNORMAL TEST CASES\n")

for i, t in enumerate(tickets, 1):
    print(f"Ticket {i}:")
    result = extract_ticket_data(t)
    print(json.dumps(result, indent=2))
    validate_output(result)

# -----------------------------
# CONFUSING CASE
# -----------------------------
confusing_ticket = """
The app sometimes works and sometimes logs me out.
It’s frustrating but not terrible. Not urgent unless it gets worse.
"""

print("\nCONFUSING TEST CASE\n")

result = extract_ticket_data(confusing_ticket)
print(json.dumps(result, indent=2))
validate_output(result)
