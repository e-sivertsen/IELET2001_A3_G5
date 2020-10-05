import threading
from socket import *

def handle_request(request):
    try:
        request = request.split('+')
        response = int(request[0]) + int(request[1])
        return str(response)

    except ValueError:
        return "Error"

def handle_connection(conn, addr):
    print("Connected to:", addr)

    with conn:
        while True:
            try:
                data = conn.recv(1024)

            except IOError as e:
                print("Error in connection",addr, ":", e)
                break
            
            if not data or data.decode() == "game over\n":
                print("Disconnected from: ", addr)
                break
            
            response = handle_request(data.decode()) + "\n"

            try:
                bytes_sent = 0
                while bytes_sent < len(response.encode()):
                    bytes_sent += conn.send(response[bytes_sent:].encode())
                    if bytes_sent == 0:
                        raise IOError("Could not send response")

            except IOError as e:
                print("Error in connection:",addr,":", e)
                break



def run_server():
    print("Starting TCP server...")

    try:
        server_socket = socket(AF_INET, SOCK_STREAM)
        server_socket.bind(('localhost',1300))
        server_socket.listen()
        print("Started TCP server, listening for connections")

    except IOError as e:
        print("Error: ", e)
        return

    connections = []
    while True:
        conn, addr = server_socket.accept()

        if not conn == None:
            t = threading.Thread(target=handle_connection, args=(conn,addr))
            t.start()


# Main entrypoint of the script
if __name__ == '__main__':
    run_server()
