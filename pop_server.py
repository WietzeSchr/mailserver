import socket
import threading
import argparse
import time
import logging
import argparse
import re
import os

def handle_client_connection(client_socket, client_address):
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
                        mailbox = f"{os.path.join(os.path.dirname(os.path.abspath(__file__)), username, "my_mailbox")}"
                        
                        with open
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

def read_mailbox(user):

    """
    mailbox_messages
	1
		from		sender
		to		receiver
		received	datetime
		message_body	[]
		message_size	9999
		to_be_deleted	True/False
	2
		from		sender
		to		receiver
		received	datetime
		message_body	[]
		message_size	9999
		to_be_deleted	True/False
	...
    """
    logger.info("Process - read-mailbox")

    try:
        mailbox_file = f"{os.path.join(os.path.dirname(os.path.abspath(__file__)), username, "my_mailbox")}"

        with open(mailbox_file, 'r') as m:
            mailbox_lines = m.readlines()

        mailbox = {}

        mail_count = 0

        if len(mailbox_lines) > 0:
            mailcount = mailcount + 1

            for line in mailbox_lines:

                line = line.strip()


                        
def read_user_info():

    logger.info("Process - read_user_info")

    try:
        userinfo_file = f"{os.path.join(server_config['WORKING_DIR'], "userinfo.txt")}"
        logger.debug(f"   {userinfo_file} contains all users and passwords")

        with open(userinfo_file, 'r') as f: 

            # Read the text file into a list of lines  
            lines = f.readlines() 
    
        # Create an empty dictionary 
        users = {} 
        
        # Loop through the lines in the text file  
        for line in lines:
            # Remove trailing and leading spaces from the line
            line = line.strip()

            # Replace multiple spaces by 1 space in the line 
            line = re.sub(r'\s+', ' ', line)
            
            user_name, user_password = line.split(' ') 
            
            # Add user, password pair to the dictionary 
            users[user_name] = user_password
    
    except Exception as e:
        logger.error(e)
        print(e)
        exit(8)

    finally:
        return users

def run_pop_server():

    logger.info("Process - run_mailserver_smtp")

    try:

        # server is running with IPv4 address (socket.AF_INET)
        # server will be using TCP (socket.SOCK_STREAM)
        my_server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

        # bind the server to a specific IP and port
        # socket.bind expects a tuple with host and port!
        my_server.bind((server_config['HOST'], server_config['PORT']))
        
        # start listening for incoming connections
        my_server.listen()
        logger.info(f"   Server running on {server_config['HOST']} listening on port {server_config['PORT']}")
        print(f"Server running on {server_config['HOST']} listening on port {server_config['PORT']}")

        # keep running and wait for incoming client connections
        while True:
            client_socket, client_address = my_server.accept()
            logger.info(f"   New incoming client connection form [{client_address[0]} - {client_address[1]}]")
            print(f"New incoming client connection form [{client_address[0]} - {client_address[1]}]")

            # to be able to accept multiple connections
            # start a new thread for each new client connection
            my_thread = threading.Thread(target=handle_client_connection, args=(client_socket, client_address))
            my_thread.start()

    except Exception as e:
        logger.error(e)
        print(f"Error: {e}")

    finally:
        # stop the server when something is going wrong
        my_server.close()

if __name__ == "__main__":
    
    # Get the arguments passed to the script
    #
    #    server   : ip address on which the server will be running - default: 127.0.0.1
    #    port     : port on which the server will be listening - default: 25
    #    loglevel : loglevel on which the script is running, to achieve less or more logging - default: INFO

    parser = argparse.ArgumentParser(description='Get commandline arguments')
    parser.add_argument('-s', '--server', default="127.0.0.1", help='server address (IPv4)')
    parser.add_argument('-p', '--port', type=int, default=110, help='port of the server')
    parser.add_argument('-l', '--loglevel', default="INFO", help='Log level', choices=['INFO', 'DEBUG', 'WARNING', 'ERROR', 'CRITICAL'])
 
    args = parser.parse_args()

    # Create a dictionary with configuration options for the server
    # to be able to pass trough the script.

    server_config = {"WORKING_DIR": os.path.dirname(os.path.abspath(__file__)),
                     "HOST": args.server,
                     "PORT": args.port}
    
    # Instantiate a logger, to have a log file with all or specific messages logged by the script
    # based on a loglevel.
    
    logger = logging.getLogger()
    logger.setLevel(args.loglevel)
    
    # Create file handler in which the messages will be logged
    # and set a default loglevel

    fh = logging.FileHandler(os.path.join(server_config['WORKING_DIR'], 'pop_server.log'))
    fh.setLevel(logging.DEBUG)
    
    # Create formatter and add it to the handler
    # to have a standardized output format in the logfile.

    formatter = logging.Formatter('%(asctime)s - %(levelname)-8s - %(message)s')
    fh.setFormatter(formatter)

    # Add the file handler to the logger

    logger.addHandler(fh)

    logger.info("==============================")
    logger.info("=   MAILSERVER POP3          =")
    logger.info("==============================")
    logger.info(f"Mailserver POP3 config:")
    logger.info(f"   POP3_HOST: {server_config['HOST']}")
    logger.info(f"   POP3_PORT: {server_config['PORT']}")

    # Read the userinfo file

    users = read_user_info()
    logger.debug(users)
    
    run_pop_server()