import os
import socket
import threading
import argparse
import logging
import re


def handle_client_connection(client_socket, client_address, users):

    received_commands = {"USER": False, "PASS": False}

    running_conversation = True

    mailbox = None

    try:

        server_response = "+OK POP3 server ready"
        print(f"Server: {server_response}")
        logger.debug(f"server response: {server_response}")
        client_socket.send(server_response.encode("utf-8"))


        while running_conversation:
            client_request = client_socket.recv(1024).decode("utf-8")
            print(f"Client: {client_request}")
            client_request = client_request.split(' ')

            command = client_request[0].upper()
            logger.debug(f"{command}")
            match command:

                # Authentication phase

                case "USER":

                    username = client_request[1]

                    if username in users:

                        received_commands["USER"] = username

                        server_response = "+OK Please enter a password"
                        logger.debug(f"server response: {server_response}")


                    else:

                        server_response = "No such user"
                        logger.debug(f"Server response: {server_response}")

                case "PASS":

                    if received_commands["USER"] is not False:
                        if users[received_commands["USER"]] == client_request[1]:
                            server_response = ""
                            received_commands["PASS"] = True

                            server_response = "+OK valid logon"
                            logger.debug(f"server response: {server_response}")

                            # TODO: get exclusive lock on the mailbox

                        else:

                            server_response = "Wrong password"
                            logger.debug(f"server response: {server_response}")

                case "STAT":

                    if received_commands["PASS"]:

                        # get message count and size
                        username = received_commands["USER"]
                        mailbox = open(f"{os.path.join(os.path.dirname(os.path.abspath(__file__)), username, "my_mailbox")}", "a")
                        total_size = os.stat(os.path.join(os.path.dirname(os.path.abspath(__file__)), username, "my_mailbox"))
                        total_mails = 0
                        for line in mailbox:
                            if line == ".":
                                total_mails += 1

                        server_response = f"+OK {total_mails} {total_size}"

                case "LIST":
                    pass

                case "RETR":
                    pass

                case "DELE":
                    pass

                case "RSET":
                    pass

                case "QUIT":

                    running_conversation = False
                    client_socket.send("closed".encode("utf-8"))

                case _:
                    server_response = f"502 Command not implemented"

            print(f"Server: {server_response}")
            client_socket.send(server_response.encode("utf-8"))

    except Exception as e:
        logger.error(e)
        print(f"Error accepting client")

    finally:
        client_socket.close()
        print(f"The connection to client {client_address[0]} on port {client_address[1]} has been closed!")


def run_pop_server(host, port, users):
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
            my_thread = threading.Thread(target=handle_client_connection, args=(client_socket, client_address, users))
            my_thread.start()

    except Exception as e:
        print(f"Error: {e}")

    finally:
        # stop the server when something is going wrong
        my_server.close()


def read_user_info():
    logger.info("Process userinfo file")

    try:
        userinfo_file = f"{os.path.join(os.path.dirname(os.path.abspath(__file__)), "userinfo.txt")}"
        print(userinfo_file)

        with open(userinfo_file, 'r') as f:
            # read the text file into a list of lines
            lines = f.readlines()

            # create an empty dictionary
        users = {}

        # loop through the lines in the text file
        for line in lines:
            # remove trailing and leading spaces from the lin
            line = line.strip()

            # replace multiple spaces by 1 space in the line
            line = re.sub(r'\s+', ' ', line)

            user_name, user_password = line.split(' ')

            # add user, password pair to the dictionary
            users[user_name] = user_password

    except Exception as e:
        logger.error(e)
        print(e)
        exit(8)

    finally:
        return users


if __name__ == "__main__":
    
    parser = argparse.ArgumentParser(description='Get commandline arguments')
    parser.add_argument('-s', '--server', default="127.0.0.1", help='server address (IPv4)')
    parser.add_argument('-p', '--port', type=int, default=110, help='port of the server')
    parser.add_argument('-l', '--loglevel', default="INFO", help='Log level',
                        choices=['INFO', 'DEBUG', 'WARNING', 'ERROR', 'CRITICAL'])

    args = parser.parse_args()

    logger = logging.getLogger()
    logger.setLevel(args.loglevel)

    # create file handler which logs even debug messages
    fh = logging.FileHandler('pop_server.log')
    fh.setLevel(logging.DEBUG)

    # create formatter and add it to the handlers
    formatter = logging.Formatter('%(asctime)s - %(levelname)-8s - %(message)s')
    fh.setFormatter(formatter)

    # add the handler to logger
    logger.addHandler(fh)

    logger.info("==============================")
    logger.info("=   POP3 - SERVER            =")
    logger.info("==============================")

    users = read_user_info()

    run_pop_server(args.server, args.port, users)

    print(f"Server starting on {args.server} on port {args.port}...")
