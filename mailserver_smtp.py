import socket
import threading
import argparse
import time

def handle_client_connection(server_config, client_socket, client_address):
    received_commands = {"HELO": False,
                         "MAIL_FROM": False,
                         "RCPT_TO": False,
                         "DATA": False}
    
    running_conversation = True

    try:
        server_response = f"220 {server_config['HOST']} Service Ready"
        print(f"Server: {server_response}")
        client_socket.send(server_response.encode("utf-8"))
        
        while running_conversation:
            client_request = client_socket.recv(1024).decode("utf-8")
            print(f"Client: {client_request}")

            if client_request.lower() == "quit":
                server_response = f"221 {server_config['HOST']} Service closing transmission channel"
                print(f"Server: {server_response}")
                client_socket.send(server_response.encode("utf-8"))
                break

            server_response = f"250 OK {client_request}"
            print(f"Server: {server_response}")
            client_socket.send(server_response.encode("utf-8"))

    except Exception as e:
        print(f"Error accepting client")

    finally:
        client_socket.close()
        print(f"The connection to client {client_address[0]} on port {client_address[1]} has been closed!")


def run_mailserver_smtp(server_config):
    try:
        # server is running with IPv4 address (socket.AF_INET)
        # server will be using TCP (socket.SOCK_STREAM)
        my_server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

        # bind the server to a specific IP and port
        # socket.bind expects a tuple with host and port!
        my_server.bind((server_config['HOST'], server_config['PORT']))
        
        # start listening for incoming connections
        my_server.listen()
        print(f"Server running on {server_config['HOST']} listening on port {server_config['PORT']}")

        # keep running and wait for incoming client connections
        while True:
            client_socket, client_address = my_server.accept()
            print(f"New incoming client connection form [{client_address[0]} - {client_address[1]}]")

            # to be able to accept multiple connections
            # start a new thread for the new client connection
            my_thread = threading.Thread(target=handle_client_connection, args=(server_config, client_socket, client_address,))
            my_thread.start()

    except Exception as e:
        print(f"Error: {e}")

    finally:
        # stop the server when something is going wrong
        my_server.close()


if __name__ == "__main__":
    
    parser = argparse.ArgumentParser(description='Get commandline arguments')
    parser.add_argument('-s', '--server', default="127.0.0.1", help='server address (IPv4)')
    parser.add_argument('-p', '--port', type=int, default=25, help='port of the server')
 
    args = parser.parse_args()

    server_config = {"HOST": args.server,
                     "PORT": args.port}

    run_mailserver_smtp(server_config)

    print(f"Server starting on {args.server} on port {args.port}...")
