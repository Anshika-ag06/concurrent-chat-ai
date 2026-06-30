import json
import re
from groq import Groq
import os
from dotenv import load_dotenv
from tools import run_tool, TOOLS

load_dotenv()

ai_client = Groq(api_key=os.environ.get("GROQ_API_KEY"))

# Build the tool descriptions dynamically from the TOOLS registry
# This means when you add a new tool to tools.py, the bot automatically knows about it
TOOL_DESCRIPTIONS = """
You have access to the following tools:

1. get_time
   - Description: Get the current time in any timezone
   - Args: {"timezone": "<IANA timezone string e.g. Asia/Kolkata, America/New_York>"}

2. calculate
   - Description: Evaluate a mathematical expression
   - Args: {"expression": "<math expression e.g. 15 * 840 / 100>"}

3. search_web
   - Description: Search the web for current information
   - Args: {"query": "<search query string>"}
"""

SYSTEM_PROMPT = f"""You are a helpful bot inside a group chat application. 
Users will mention you with @bot followed by their request.

{TOOL_DESCRIPTIONS}

When a user asks something, decide if you need a tool or can answer directly.

If you need a tool, respond with ONLY a JSON object in this exact format:
{{"tool": "<tool_name>", "args": {{<args>}}}}

If you do NOT need a tool, respond with ONLY a JSON object in this exact format:
{{"tool": null, "reply": "<your reply>"}}

Never respond with anything other than one of these two JSON formats.
Do not add explanation, markdown, or extra text outside the JSON."""


def parse_agent_response(raw: str) -> dict:
    raw = re.sub(r"```json|```", "", raw).strip()
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        return {"tool": None, "reply": raw}  

def run_agent(user_message: str) -> str:
    response = ai_client.chat.completions.create(
        model="llama-3.1-8b-instant",
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_message}
        ],
        max_tokens=300
    )
    raw = response.choices[0].message.content.strip()
    parsed = parse_agent_response(raw)

    if parsed.get("tool") is None:
        return parsed.get("reply", "I'm not sure how to help with that.")

    tool_name = parsed.get("tool")
    tool_args = parsed.get("args", {})
    tool_result = run_tool(tool_name, tool_args)

    followup = ai_client.chat.completions.create(
        model="llama-3.1-8b-instant",
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_message},
            {"role": "assistant", "content": raw},
            {"role": "user", "content": f"Tool result: {tool_result}\nNow give a friendly natural language reply based on this result. Respond with only the JSON format: {{\"tool\": null, \"reply\": \"<reply>\"}}"}
        ],
        max_tokens=300
    )
    raw2 = followup.choices[0].message.content.strip()
    parsed2 = parse_agent_response(raw2)
    return parsed2.get("reply", tool_result) 