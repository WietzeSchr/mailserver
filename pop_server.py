import socket
import threading
import argparse

def handle_client_connection(client_socket, client_address):
    try:
        while True:
            client_request = client_socket.recv(1024).decode("utf-8")

            if client_request.lower() == "close":
                client_socket.send("closed".encode("utf-8"))
                break

            print(f"Received request from [{client_address[0]} - {client_address[1]}]: {client_request}")

            client_response = "accepted"
            client_socket.send(client_response.encode("utf-8"))

    except Exception as e:
        print(f"Error accepting client")

    finally:
        client_socket.close()
        print(f"The connection to client {client_address[0]} on port {client_address[1]} has been closed!")


def run_pop_server(host, port):
    try:
        # server is running with IPv4 address (socket.AF_INET)
        # server will be using TCP (socket.SOCK_STREAM)
        my_server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

        # bind the server to a specific IP and port
        # socket.bind expects a tuple with host and port!
        my_server.bind((host, port))
        
        # start listening for incoming connections
        my_server.listen()
        print(f"Server running on {host} listening on port {port}")

        # keep running and wait for incoming client connections
        while True:
            client_socket, client_address = my_server.accept()
            print(f"New incoming client connection form [{client_address[0]} - {client_address[1]}]")

            # to be able to accept multiple connections
            # start a new thread for the new client connection
            my_thread = threading.Thread(target=handle_client_connection, args=(client_socket, client_address,))
            my_thread.start()

    except Exception as e:
        print(f"Error: {e}")

    finally:
        # stop the server when something is going wrong
        my_server.close()


if __name__ == "__main__":
    
    parser = argparse.ArgumentParser(description='Get commandline arguments')
    parser.add_argument('-s', '--server', default="127.0.0.1", help='server address (IPv4)')
    parser.add_argument('-p', '--port', type=int, default=110, help='port of the server')
 
    args = parser.parse_args()

    run_pop_server(args.server, args.port)

    print(f"Server starting on {args.server} on port {args.port}...")
