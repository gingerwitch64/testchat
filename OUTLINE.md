Current thought process/set of ideas for how to go about this:
## Client Actions List
1. Ask the user for a preferred username/alias.
2. ~~Pseudo-randomly generate a User ID using (a) a __timestamp__ (b) a system __hardware ID__ or output of some kind of system-identifying command and (c) a __randomly generated number__; throw all of these into a String and __hash it__~~ Generate a [UUID](https://docs.python.org/3/library/uuid.html).
3. Send a user initialization request to the server.
4. If the server returns a __success__, allow the user to __start chatting__; if the server returns an __error__ (either because of a duplicate username or ID), request the user to __re-initialize__.
5. Messages from the user should be sent to the server; *new* messages from the server will be fetched via a periodic fetching request.

## Server Actions List
1. Initialize the server and its database (probably __SQLite__ or __Redis__ for our purposes), taking in user parameters for the hostname, port, etc.
2. Create main TCP threading server.
3. Listen for incoming connections and handle accordingly:

- If a user initialization request is sent, check a user database for any duplicate usernames or IDs. If there is no duplicate, allow the user to register (and add their username and ID to the database).
- If a user message is sent, __log the timestamp__ that the server received the message at, the __content of the message__ and the __username__ of the user (the __message request should also contain__ the **user's ID**, which will be __checked against the username-ID pair in the database__ to make sure there is no fraud happening).
- If a message fetch request is sent, read the timestamp of the last message that the user got; because this will be sent by the user, if it's something outrageous like <t:0>, the server will only send the last `n` messages to the user. Otherwise, send all messages since the user's last received message timestamp to said user.
