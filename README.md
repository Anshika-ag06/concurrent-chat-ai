#Real-Time Multi-Client Chat Application in Python

##Overview

This is a real-time chat application built using Python's socket programming and threading. It supports multiple clients connecting simultaneously to a server and exchanging messages. Each client sets a username, and messages include timestamps for easy tracking.

##Features

- Multi-threaded server handling multiple clients concurrently
- User-chosen usernames
- Timestamps on all messages
- Graceful client connection and disconnection notifications
- Command-line interface for server and clients

##Technologies Used

- Python 3.x
- socket module for TCP networking
- threading module for concurrency
- datetime module for timestamps

##How to Run

###Running the Server

1. Open a terminal.
2. Navigate to the project folder.
3. Run: python3 server.py


###Running the Client

1. Open one or more terminal windows.
2. Navigate to the project folder.
3. Run: python3 client.py
4. Enter your desired username when prompted.
5. Start chatting!
6. To quit, type `quit`.

##License

This project is licensed under the MIT License. 





