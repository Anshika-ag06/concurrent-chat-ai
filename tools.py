from datetime import datetime
import pytz
from duckduckgo_search import DDGS


def get_time(timezone: str) -> str:
    """
    Returns the current time in the given timezone.
    timezone should be an IANA timezone string e.g. 'Asia/Kolkata', 'America/New_York'
    """
    try:
        tz = pytz.timezone(timezone)
        now = datetime.now(tz)
        return f"Current time in {timezone}: {now.strftime('%I:%M %p, %A %d %B %Y')}"
    except pytz.UnknownTimeZoneError:
        return f"Unknown timezone '{timezone}'. Use IANA format e.g. 'Asia/Kolkata', 'Europe/London'."


def calculate(expression: str) -> str:
    """
    Safely evaluates a mathematical expression string.
    e.g. '15 * 840 / 100' or '(200 + 50) * 1.18'
    """
    try:
        # Only allow safe characters — digits, operators, spaces, dots, brackets
        allowed = set("0123456789+-*/.() ")
        if not all(c in allowed for c in expression):
            return "Invalid expression — only numbers and basic operators allowed."
        result = eval(expression)
        return f"{expression} = {round(result, 4)}"
    except ZeroDivisionError:
        return "Error: division by zero."
    except Exception as e:
        return f"Could not evaluate expression: {e}"


def search_web(query: str) -> str:
    """
    Searches DuckDuckGo and returns a short summary of the top result.
    No API key needed.
    """
    try:
        with DDGS() as ddgs:
            results = list(ddgs.text(query, max_results=3))
        if not results:
            return f"No results found for '{query}'."
        # Return top 2 results as a brief summary
        summary = []
        for r in results[:2]:
            summary.append(f"- {r['title']}: {r['body'][:150]}...")
        return "\n".join(summary)
    except Exception as e:
        return f"Search failed: {e}"


# Registry — maps tool name to function
# When you want to add a new tool later, just add it here
TOOLS = {
    "get_time": get_time,
    "calculate": calculate,
    "search_web": search_web,
}


def run_tool(name: str, args: dict) -> str:
    """
    Executes a tool by name with the given args dict.
    Returns the result as a string.
    """
    if name not in TOOLS:
        return f"Unknown tool '{name}'."
    try:
        return TOOLS[name](**args)
    except TypeError as e:
        return f"Wrong arguments for tool '{name}': {e}"
