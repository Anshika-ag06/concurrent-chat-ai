import socket
import threading
from groq import Groq
import os
from dotenv import load_dotenv

message_history = []    
history_lock = threading.Lock()
MAX_HISTORY = 10

load_dotenv()
ai_client = Groq(api_key=os.environ.get("GROQ_API_KEY"))

def add_to_history(msg):
    with history_lock:
        message_history.append(msg)
        if len(message_history) > MAX_HISTORY:
            message_history.pop(0)


def get_suggestions(context, username):
    conversation = "\n".join(context)
    prompt = f"""You are a helpful assistant inside a group chat application.
            Here is the recent chat history:

            {conversation}

            The user '{username}' wants to reply. Suggest exactly 3 short, natural reply options for them.
            Format your response as a numbered list like this:
            1. <suggestion>
            2. <suggestion>
            3. <suggestion>
            Only return the numbered list, nothing else."""

    try:
        response = ai_client.chat.completions.create(
                    model="llama-3.1-8b-instant",
                    messages=[{"role": "user", "content": prompt}],
                    max_tokens=200)
        raw = response.choices[0].message.content.strip()

        # Parse the numbered list into a Python list
        suggestions = []
        for line in raw.splitlines():
            line = line.strip()
            if line and line[0].isdigit() and ". " in line:
                suggestions.append(line.split(". ", 1)[1])
        return suggestions if suggestions else ["(Could not parse suggestions, try again)"]

    except Exception as e:
        return [f"(API error: {e})"]


def fetch_and_display_suggestions(context, username, client_socket):
    print("\r" + " " * 80, end="")
    print("\r[AI] Fetching suggestions...", flush=True)

    suggestions = get_suggestions(context, username)

    # Clear line and print suggestions cleanly
    print("\r" + " " * 80, end="")
    print("\r[AI] Suggested replies:")
    for i, s in enumerate(suggestions, 1):
        print(f"  {i}. {s}")
    print("  Enter 1 / 2 / 3 to send, or press Enter to skip.")
    print("You: ", end="", flush=True)

    # Read the user's choice — handled in a thread so input() here
    # won't clash with the main loop's input()
    choice = input().strip()
    if choice in ("1", "2", "3"):
        idx = int(choice) - 1
        if idx < len(suggestions):
            msg = suggestions[idx]
            client_socket.send(msg.encode())
            add_to_history(f"You: {msg}")
            print(f"[Sent]: {msg}")
    else:
        print("[Skipped]")
    


def rec_message(client):
    while True:
        try:
            message = client.recv(1024).decode()
            if not message:
                print("\nDisconnected from server.")
                break
            add_to_history(message)
            print('\r' + ' ' * 80, end='')
            print('\r' + message)
            print("You: ", end='', flush=True)
        except (ConnectionResetError, OSError):
            print("\nConnection lost.")
            break


def main():
    client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    client.connect(('localhost', 12345))
    print("Connected to server at ('localhost', 12345)")

    username = input("Enter your username: ").strip()
    while not username:
        username = input("Username cannot be empty. Enter your username: ").strip()
    client.send(username.encode())
    print(f"Joined as {username}. Type /suggest for AI reply suggestions, or 'quit' to exit.\n")

    rec_thread = threading.Thread(target=rec_message, args=(client,), daemon=True)
    rec_thread.start()

    while True:
        message = input("You: ")

        if message.lower() == "quit":
            client.send(message.encode())
            print("Chat quit.")
            break

        if message.strip() == "/suggest":
            with history_lock:
                context = list(message_history)
            if not context:
                print("[No messages in history yet to suggest from]")
                continue
            # Fire the API call in a background thread — main loop stays responsive
            suggest_thread = threading.Thread(
                target=fetch_and_display_suggestions,
                args=(context, username, client),
                daemon=True
            )
            suggest_thread.start()
            suggest_thread.join()  # Wait for picker to finish before next input
            continue

        client.send(message.encode())
        add_to_history(f"You: {message}")

    client.close()


if __name__ == "__main__":
    main()
