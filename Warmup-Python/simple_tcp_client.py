import random
import time
from socket import *

HOST = "datakomm.work"
PORT = 1301

client_socket = None


def connect_to_server(host, port):
    global client_socket

    client_socket = socket(AF_INET, SOCK_STREAM)

    try:
        client_socket.connect((host, port))
        return True
    
    except IOError as e:
        print("Error: ", e)
        return False


def close_connection():
    global client_socket

    try:
        client_socket.close()
        return True

    except IOError as e:
        print("Error: ", e)
        return False


def send_request_to_server(request):
    global client_socket
    request += "\n"

    try:
        bytes_sent = 0
        while bytes_sent < len(request.encode()):
            bytes_sent += client_socket.send(request[bytes_sent:].encode())
            if bytes_sent == 0:
                raise IOError("Could not send request")
        return True

    except IOError as e:
        print("Error: ", e)
        return False


def read_response_from_server():
    global client_socket

    return client_socket.recv(1024).decode()


def run_client_tests():
    """
    Runs different "test scenarios" from the TCP client side
    :return: String message that represents the result of the operation
    """
    print("Simple TCP client started")
    if not connect_to_server(HOST, PORT):
        return "ERROR: Failed to connect to the server"

    print("Connection to the server established")
    a = random.randint(1, 20)
    b = random.randint(1, 20)
    request = str(a) + "+" + str(b)

    if not send_request_to_server(request):
        return "ERROR: Failed to send valid message to server!"

    print("Sent ", request, " to server")
    response = read_response_from_server()
    if response is None:
        return "ERROR: Failed to receive server's response!"

    print("Server responded with: ", response)
    seconds_to_sleep = 2 + random.randint(0, 5)
    print("Sleeping %i seconds to allow simulate long client-server connection..." % seconds_to_sleep)
    time.sleep(seconds_to_sleep)

    request = "bla+bla"
    if not send_request_to_server(request):
        return "ERROR: Failed to send invalid message to server!"

    print("Sent " + request + " to server")
    response = read_response_from_server()
    if response is None:
        return "ERROR: Failed to receive server's response!"

    print("Server responded with: ", response)
    if not (send_request_to_server("game over") and close_connection()):
        return "ERROR: Could not finish the conversation with the server"

    print("Game over, connection closed")
    # When the connection is closed, try to send one more message. It should fail.
    if send_request_to_server("2+2"):
        return "ERROR: sending a message after closing the connection did not fail!"

    print("Sending another message after closing the connection failed as expected")
    return "Simple TCP client finished"


# Main entrypoint of the script
if __name__ == '__main__':
    result = run_client_tests()
    print(result)
