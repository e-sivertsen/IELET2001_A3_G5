import threading
from socket import *

states = [
    "disconnected",
    "connected",
    "authorized"
]
TCP_PORT = 1300
SERVER_HOST = "datakomm.work"
current_state = "disconnected"
must_run = True
client_socket = None


def quit_application():
    global must_run
    must_run = False


def send_command(command, arguments):
    global client_socket
    payload = ("%s %s\n" %(command, arguments)).encode()
    try:
        bytes_sent = 0
        while bytes_sent < len(payload):
            bytes_sent += client_socket.send(payload[bytes_sent:])
            if bytes_sent == 0:
                raise IOError("Could not send request")
        return True
    except IOError as e:
        print("Error: ", e)
        return False


def read_one_line(sock):
    newline_received = False
    message = ""
    while not newline_received:
        try:
            character = sock.recv(1).decode()
        except UnicodeDecodeError: character = u'\u2610';	
        if character == '\n':
            newline_received = True
        elif character == '\r':
            pass
        else:
            message += character
    return message


def get_servers_response():
    global client_socket
    try:
        response = read_one_line(client_socket)
        return response
    except IOError as e:
        print("Error:", e)
        return None


def connect_to_server():
    global client_socket
    global current_state
    global TCP_PORT
    global SERVER_HOST
    client_socket = socket(AF_INET, SOCK_STREAM)
    try:
        client_socket.connect((SERVER_HOST, TCP_PORT))
    except IOError as e:
        print("Error: ", e)
        return False
    current_state = "connected"
    send_command("sync","")
    if get_servers_response() != "modeok":
        print("Error: could not set sync mode")


def disconnect_from_server():
    global client_socket
    global current_state
    try:
        client_socket.close()
        current_state = "disconnected"
        return True
    except IOError as e:
        print("Error: ", e)
        return False


def authorize():
    global current_state
    print("Enter displayname: ")
    while True:
        displayname = input()
        if send_command("login", displayname):
            response = get_servers_response()
            if response == "loginok":
                current_state = "authorized"
                print("Display name set to:", displayname)
                return
            elif not response: return
            else:
                 print("Displayname already in use, please enter another displayname: ")
        else: return


def broadcast():
    print("Enter message to broadcast to all users:")
    message = input().replace('\n','')
    if send_command("msg", message):
        response = get_servers_response()
        if "msgok" in response:
            print("Message successfully sent to %s people" %response.split(' ')[1])
        else: print("Error:", response)


def private_msg():
    print("Enter username of reccipient: ")
    target = input().replace('\n','')
    print("\nEnter message text:")
    message = input().replace('\n','')
    if send_command("privmsg", "%s %s" %(target, message)):
        response = get_servers_response()
        if "msgok" in response: print("\nSent message to", target)
        else: print("\nError:", response)


def print_columns(l, columns):
    width = 0
    for item in l: width = max(width, len(item))
    count = 0
    for item in l:
        if count == columns:
            print(item)
            count = 0
        else:
            while len(item) < width: item += " "
            print(item, end="   ")
            count += 1


def get_users():
    if send_command("users",""):
        response = get_servers_response()
        response = response.split(' ')
        response.pop(0)
        print("Users currently on server:")
        print_columns(response, 4)


def get_messages():
    if send_command("inbox",""):
        response = get_servers_response().split(' ')
        print("New messages:", response[1])
        for _ in range(0, int(response[1])):
            message = get_servers_response()
            sender = message.split(' ')[1]
            if "privmsg" in message: print("%s(private):" %sender)
            else: print("%s(public):" %sender)
            print(message[message.find(sender) + len(sender) + 1:], "\n")


def get_joke():
    if send_command("joke", ""): print(get_servers_response()[5:])


def recieve_async():
    while True:
        data = get_servers_response()
        if data is None: return
        command = data.split(' ')[0]
        if command == "privmsg" or command == "msg":
            msg_type = "public"
            if command == "privmsg": msg_type = "private"
            sender = data.split(' ')[1]
            print("%s(%s): %s\n" %(sender, msg_type, data[data.find(sender) + len(sender) + 1:]))
        elif command == "msgok": pass
        elif command == "modeok": return
        else: print(data,"\n")


def async_mode():
    if send_command("async", "") and "modeok" in get_servers_response():
        reciever_thread = threading.Thread(target=recieve_async)
        reciever_thread.start()
        print('Type "public <message>" to send a public message')
        print('Type "private <user> <message>" to send a private message')
        print('Type "exit" to exit chat mode\n')
        while client_socket.fileno() != -1:
            user_input = input()
            command = user_input.split(' ')[0].lower()
            if command == "exit":
                if send_command("sync",""):
                    reciever_thread.join()
                    return
            elif command == "public" and len(user_input.split(' ')) >= 2: send_command("msg", user_input[7:])
            elif command == "private" and len(user_input.split(' ')) >= 3: send_command("privmsg", user_input[8:])
            else: print("Error: invalid command")
            print()


available_actions = [
    {
        "description": "Connect to a chat server",
        "valid_states": ["disconnected"],
        "function": connect_to_server
    },
    {
        "description": "Disconnect from the server",
        "valid_states": ["connected", "authorized"],
        "function": disconnect_from_server
    },
    {
        "description": "Authorize (log in)",
        "valid_states": ["connected", "authorized"],
        "function": authorize
    },
    {
        "description": "Send a public message",
        "valid_states": ["connected", "authorized"],
        "function": broadcast
    },
    {
        "description": "Send a private message",
        "valid_states": ["authorized"],
        "function": private_msg
    },
    {
        "description": "Read messages in the inbox",
        "valid_states": ["connected", "authorized"],
        "function": get_messages
    },
    {
        "description": "See list of users",
        "valid_states": ["connected", "authorized"],
        "function": get_users
    },
    {
        "description": "Get a joke",
        "valid_states": ["connected", "authorized"],
        "function": get_joke
    },
    {
        "description": "Quit the application",
        "valid_states": ["disconnected", "connected", "authorized"],
        "function": quit_application
    },
    {
        "description": "Chat mode",
        "valid_states": ["connected", "authorized"],
        "function": async_mode
    },
]


def run_chat_client():
    while must_run:
        print_menu()
        action = select_user_action()
        perform_user_action(action)
    print("Thanks for watching. Like and subscribe! 👍")


def print_menu():
    """ Print the menu showing the available options """
    print("==============================================")
    print("What do you want to do now? ")
    print("==============================================")
    print("Available options:")
    i = 1
    for a in available_actions:
        if current_state in a["valid_states"]:
            print("  %i) %s" % (i, a["description"]))
        i += 1
    print()


def select_user_action():
    number_of_actions = len(available_actions)
    hint = "Enter the number of your choice (1..%i):" % number_of_actions
    choice = input(hint)
    try:
        choice_int = int(choice)
    except ValueError:
        choice_int = -1
    if 1 <= choice_int <= number_of_actions:
        action = choice_int - 1
    else:
        action = None
    return action


def perform_user_action(action_index):
    if action_index is not None:
        print()
        action = available_actions[action_index]
        if current_state in action["valid_states"]:
            function_to_run = available_actions[action_index]["function"]
            if function_to_run is not None:
                function_to_run()
            else:
                print("Internal error: NOT IMPLEMENTED (no function assigned for the action)!")
        else:
            print("This function is not allowed in the current system state (%s)" % current_state)
    else:
        print("Invalid input, please choose a valid action")
    print()
    return None


if __name__ == '__main__':
    run_chat_client()