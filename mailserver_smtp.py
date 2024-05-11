import socket
import threading
import argparse
import datetime
import logging
import argparse
import re
import os

def handle_client_connection(client_socket, client_address):
    
    logger.info(f"Handle client connection from [{client_address[0]} - {client_address[1]}] in separate thread")

    received_commands = {"HELO": False,
                         "MAIL": False,
                         "RCPT": False,
                         "DATA": False}
    
    running_conversation = True

    try:
        server_response = f"220 {server_config['HOST']} Service Ready"
        logger.info(f"[{client_address[0]} - {client_address[1]}] - Server: {server_response}")
        print(f"Server: {server_response}")
        client_socket.send(server_response.encode("utf-8"))
        
        while running_conversation:
            client_request = client_socket.recv(1024).decode("utf-8")
            logger.info(f"[{client_address[0]} - {client_address[1]}] - Client: {client_request}")
            print(f"Client: {client_request}")

            command = client_request.split(' ')[0].upper()

            match command:

                case "HELO":

                    server_response = f"250 OK {client_request}"
                    received_commands["HELO"] = True

                case "MAIL":

                    if received_commands["HELO"]:
                        server_response = f"250 OK {client_request}"
                        received_commands["MAIL"] = True

                case "RCPT":
                    
                    if received_commands["MAIL"]:
                        user = client_request.split(' ')[2].split('@')[0]

                        # Check for valid user
                        if user in users:
                            server_response = f"250 OK {client_request}"
                            received_commands["RCPT"] = user
                        else:
                            server_response = f"550 No such user"

                case "DATA":

                    if received_commands["RCPT"]:
                        server_response = f"354 Start mail input; end with <CRLF>.<CRLF>"
                        print(f"Server: {server_response}")
                        logger.info(f"[{client_address[0]} - {client_address[1]}] - Server: {server_response}")
                        client_socket.send(server_response.encode("utf-8"))

                        content = []
                        data = client_socket.recv(1024).decode("utf-8")
                        logger.debug(data)
                        while data != ".":
                            content.append(data)
                            print(f"Client: {data}")
                            data = client_socket.recv(1024).decode("utf-8")
                            logger.debug(data)

                        content.append(".")

                        logger.debug(content)
                        store_mail(received_commands["RCPT"], content)

                        server_response = f"250 OK Message accepted for delivery"
                        
                case "QUIT":

                    server_response = f"221 {server_config['HOST']} Service closing transmission channel"
                    print(f"Server: {server_response}")
                    logger.info(f"[{client_address[0]} - {client_address[1]}] - Server: {server_response}")
                    client_socket.send(server_response.encode("utf-8"))
                    break

                case _:

                    server_response = f"502 Command not implemented"

            print(f"Server: {server_response}")
            logger.info(f"[{client_address[0]} - {client_address[1]}] - Server: {server_response}")
            client_socket.send(server_response.encode("utf-8"))

    except Exception as e:
        print(f"ERROR: Accepting client")
        print(e)
        logger.error(f"   {e}")

    finally:
        client_socket.close()
        print(f"The connection to client {client_address[0]} on port {client_address[1]} has been closed!")
        logger.info(f"The connection to client {client_address[0]} on port {client_address[1]} has been closed!")

def store_mail(recipient, data):

    logger.info(f"Store mail in mailbox for user [{recipient}]")

    try:
        mailbox = open(f"{os.path.join(server_config['MAILBOX_DIR'], recipient, "my_mailbox")}", "a")
        logger.debug(f"   Mail will be stored in [{mailbox}]")

        for line in data:
            logger.debug(f"   >>> {line}")
            mailbox.write(f"{line}\n")

            if line.split(' ')[0] == "Subject:":
                now = datetime.datetime.now()
                current_datetime = now.strftime("%d/%m/%Y %H:%M")
                mailbox.write(f"Received: {current_datetime}\n")

    except Exception as e:
        logger.error(f"   {e}")
        print(f"ERROR: {e}")

def read_user_info():

    # This function reads the user / password info from the userinfo.txt file
    # and returns a dictionary with all the information

    logger.info("Reading user information")

    try:
        userinfo_file = f"{os.path.join(server_config['WORKING_DIR'], "userinfo.txt")}"
        logger.info(f"   File containing all users and passwords: [{userinfo_file}]")

        with open(userinfo_file, 'r') as f: 

            # Read the text file into a list of lines  
            lines = f.readlines() 
    
        f.close()

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
        logger.error(f"   {e}")
        print(f"ERROR: {e}")
        exit(8)

    finally:
        return users

def run_mailserver_smtp():

    logger.info("Run SMTP mailserver")

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
        logger.error(f"   {e}")
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
    parser.add_argument('-p', '--port', type=int, default=25, help='port of the server')
    parser.add_argument('-l', '--loglevel', default="INFO", help='Log level', choices=['INFO', 'DEBUG', 'WARNING', 'ERROR', 'CRITICAL'])
 
    args = parser.parse_args()

    # Create a dictionary with configuration options for the server
    # to be able to pass trough the script.

    server_config = {"WORKING_DIR": os.path.dirname(os.path.abspath(__file__)),
                     "LOG_DIR": os.path.join(os.path.dirname(os.path.abspath(__file__)), 'log'),
                     "MAILBOX_DIR": os.path.join(os.path.dirname(os.path.abspath(__file__)), 'mailboxes'),
                     "HOST": args.server,
                     "PORT": args.port}
    
    # Instantiate a logger, to have a log file with all or specific messages logged by the script
    # based on a loglevel.
    
    logger = logging.getLogger()
    logger.setLevel(args.loglevel)
    
    # Create file handler in which the messages will be logged
    # and set a default loglevel

    fh = logging.FileHandler(os.path.join(server_config['LOG_DIR'], 'mailserver_smtp.log'))
    fh.setLevel(logging.DEBUG)
    
    # Create formatter and add it to the handler
    # to have a standardized output format in the logfile.

    formatter = logging.Formatter('%(asctime)s - %(levelname)-8s - %(message)s')
    fh.setFormatter(formatter)

    # Add the file handler to the logger

    logger.addHandler(fh)

    logger.info("==============================")
    logger.info("=   MAILSERVER SMTP          =")
    logger.info("==============================")
    logger.info("")
    logger.info(f"Mailserver SMTP config:")

    # Log all config parameters
    for key, value in server_config.items():
        logger.info(f"   {key}: [{value}]")

    # Read the userinfo file
    users = read_user_info()
    logger.debug(f"   {users}")
    
    # Start SMTP server
    run_mailserver_smtp()