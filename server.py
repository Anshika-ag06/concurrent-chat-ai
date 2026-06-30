import socket
import threading
from datetime import datetime
from bot import run_agent


clients_list = []
client_username = {}
clients_lock = threading.Lock()


def remove_client(c_socket):
    with clients_lock:
        if c_socket in clients_list:
            clients_list.remove(c_socket)
        client_username.pop(c_socket, None)
    c_socket.close()


def sendAll(message, sender):
    with clients_lock:
        # If sender is None, send to ALL clients (used by bot)
        targets = [c for c in clients_list if c != sender]

    for c in targets:
        try:
            c.send(message.encode())
        except (ConnectionResetError, OSError):
            remove_client(c)


def handle_client(c_socket, addr):
    try:
        username = c_socket.recv(1024).decode().strip()
        if not username:
            c_socket.send("Invalid username. Connection closing.".encode())
            c_socket.close()
            return

        with clients_lock:
            client_username[c_socket] = username

        join_msg = f"[System] {username} joined the chat."
        print(join_msg)
        sendAll(join_msg, c_socket)

        while True:
            message = c_socket.recv(1024).decode()

            if not message or message.lower() == "quit":
                leave_msg = f"[System] {username} left the chat."
                print(leave_msg)
                remove_client(c_socket)
                sendAll(leave_msg, c_socket)
                break

            timestamp = datetime.now().strftime("%H:%M:%S")
            timestamped_message = f"[{timestamp}] {username}: {message}"
            print(timestamped_message)
            sendAll(timestamped_message, c_socket)

            # If message is directed at the bot, run the agent in a background thread
            # so the server isn't blocked waiting for the AI response
            if message.strip().lower().startswith("@bot"):
                def bot_reply(msg, ts):
                    reply = run_agent(msg)
                    bot_message = f"[{ts}] Bot: {reply}"
                    print(bot_message)
                    sendAll(bot_message, None)  # None = send to ALL clients including sender
                threading.Thread(target=bot_reply, args=(message, timestamp), daemon=True).start()

    except (ConnectionResetError, OSError):
        print(f"Connection lost: {addr}")
        remove_client(c_socket)


def main():
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    print("Socket created")
    server.bind(("localhost", 12345))
    server.listen(5)
    print("Waiting for connections...")

    while True:
        client, addr = server.accept()
        with clients_lock:
            clients_list.append(client)
        print(f"Connected: {addr}")
        thread = threading.Thread(target=handle_client, args=(client, addr), daemon=True)
        thread.start()


if __name__ == "__main__":
    main()
