import socket
import threading
import argparse
import time
import logging
import argparse
import re
import os
import sys

def handle_client_connection(client_socket, client_address):
    received_commands = {"USER": False, "PASS": False}

    running_conversation = True

    mailbox = {}

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
                        print(f"Server: {server_response}")
                        client_socket.send(server_response.encode("utf-8"))
                        logger.debug(f"server response: {server_response}")


                    else:

                        server_response = "No such user"
                        print(f"Server: {server_response}")
                        client_socket.send(server_response.encode("utf-8"))
                        logger.debug(f"Server response: {server_response}")

                case "PASS":

                    if received_commands["USER"] is not False:
                        if users[received_commands["USER"]] == client_request[1]:
                            server_response = "" 
                            received_commands["PASS"] = True

                            server_response = "+OK valid logon"
                            print(f"Server: {server_response}")
                            client_socket.send(server_response.encode("utf-8"))
                            logger.debug(f"server response: {server_response}")

                            mailbox = read_mailbox(received_commands["USER"])

                            # TODO: get exclusive lock on the mailbox

                        else:

                            server_response = "Wrong password"
                            print(f"Server: {server_response}")
                            client_socket.send(server_response.encode("utf-8"))
                            logger.debug(f"server response: {server_response}")

                case "STAT":

                    if received_commands["PASS"]:

                        # get message count and size
                        username = received_commands["USER"]
                        total_size = mailbox['total_size']
                        total_mails = mailbox['message_count']

                        server_response = f"+OK {total_mails} {total_size}"
                        print(f"Server: {server_response}")
                        client_socket.send(server_response.encode("utf-8"))

                case "LIST":

                    if received_commands["PASS"]:

                        server_response = "+OK"
                        print(f"Server: {server_response}")
                        client_socket.send(server_response.encode("utf-8"))
                        logger.debug(mailbox)
                        logger.debug(f"Server: Listing {mailbox['message_count']} mails")

                        for mail_id in mailbox['mailbox_messages'].keys():

                            if not mailbox['mailbox_messages'][mail_id]['to_be_deleted']:
                                line = f"{mail_id}. From: {mailbox['mailbox_messages'][mail_id]['from']} Received: {mailbox['mailbox_messages'][mail_id]['received']} Subject: {mailbox['mailbox_messages'][mail_id]['subject']} Size: {mailbox['mailbox_messages'][mail_id]['message_size']}"
                                logger.debug(f"mail: {line}")
                                client_socket.send(line.encode("utf-8"))
                                time.sleep(0.1)

                        client_socket.send(".".encode("utf-8"))

                        logger.debug("Server: done listing emails")

                case "RETR":

                    if received_commands["PASS"]:

                        logger.debug(client_request)
                        logger.debug(f"{client_request[1]}, {list(mailbox['mailbox_messages'].keys())}")
                        logger.debug(f"mailbox {mailbox}")

                        if client_request[1] in list(mailbox['mailbox_messages'].keys()) and not mailbox['mailbox_messages'][client_request[1]]['to_be_deleted']:
                            
                            linecount = 2 + len(mailbox['mailbox_messages'][client_request[1]]['message_body'])
                            server_response = f"+OK retrieving mail containing {linecount} lines"
                            print(f"Server: {server_response}")
                            logger.debug(server_response)
                            client_socket.send(server_response.encode("utf-8"))
                            time.sleep(0.1)

                            server_response = f"From: {mailbox['mailbox_messages'][client_request[1]]['from']}"
                            logger.debug(server_response)
                            client_socket.send(server_response.encode("utf-8"))
                            time.sleep(0.1)

                            server_response = f"To: {mailbox['mailbox_messages'][client_request[1]]['to']}"
                            logger.debug(server_response)
                            client_socket.send(server_response.encode("utf-8"))
                            time.sleep(0.1)

                            server_response = f"Received: {mailbox['mailbox_messages'][client_request[1]]['received']}"
                            logger.debug(server_response)
                            client_socket.send(server_response.encode("utf-8"))
                            time.sleep(0.1)

                            server_response = f"Subject: {mailbox['mailbox_messages'][client_request[1]]['subject']}"
                            logger.debug(server_response)
                            client_socket.send(server_response.encode("utf-8"))
                            time.sleep(0.1)

                            for line in mailbox['mailbox_messages'][client_request[1]]['message_body']:
                                logger.debug(line)
                                client_socket.send(line.encode("utf-8"))
                                time.sleep(0.1)
                            
                            server_response = "."
                            logger.debug(server_response)
                            client_socket.send(server_response.encode("utf-8"))

                        else:

                            server_response = f"-ERR no such message"
                            print(f"Server: {server_response}")
                            client_socket.send(server_response.encode("utf-8"))

                    else:

                        server_response = "-ERR not authenticated"
                        print(f"Server: {server_response}")
                        client_socket.send(server_response.encode("utf-8"))

                case "DELE":

                    if received_commands["PASS"]:

                        if client_request[1] in mailbox['mailbox_messages'].keys():
                            mailbox['deleted_messages'] = True
                            mailbox['mailbox_messages'][client_request[1]]['to_be_deleted'] = True
                            server_response = "+OK"
                            print(f"Server: {server_response}")
                            client_socket.send(server_response.encode("utf-8"))

                        else:

                            server_response = "-ERR no such message"
                            print(f"Server: {server_response}")
                            client_socket.send(server_response.encode("utf-8"))

                    else:

                        server_response = "-ERR not authenticated"
                        print(f"Server: {server_response}")
                        client_socket.send(server_response.encode("utf-8"))

                case "RSET":

                    if received_commands["PASS"]:
                        mailbox['deleted_messages'] = False
                        for mail_id in mailbox['mailbox_messages'].keys():

                            mail = mailbox['mailbox_messages'][mail_id]
                            mail['to_be_deleted'] = False

                        server_response = "+OK"
                        print(f"Server: {server_response}")
                        client_socket.send(server_response.encode("utf-8"))

                    else:

                        server_response = "-ERR not authenticated"
                        print(f"Server: {server_response}")
                        client_socket.send(server_response.encode("utf-8"))

                case "QUIT":

                    if mailbox['deleted_messages']:
                        write_mailbox_file(mailbox)

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

def get_size(obj, seen=None):

    # Function to get the size of a python object
    size = sys.getsizeof(obj)
    
    if seen is None:
        seen = set()

    obj_id = id(obj)
    
    if obj_id in seen:
        return 0
    
    seen.add(obj_id)
    
    if isinstance(obj, dict):
        size += sum([get_size(v, seen) for v in obj.values()])
        size += sum([get_size(k, seen) for k in obj.keys()])
    
    elif hasattr(obj, '__dict__'):
        size += get_size(obj.__dict__, seen)
    
    elif hasattr(obj, '__iter__') and not isinstance(obj, (str, bytes, bytearray)):
        size += sum([get_size(i, seen) for i in obj])
    
    return size

def write_mailbox_file(mailbox):

    logger.info("Process - write_mailbox_file")
    logger.debug(f"   Writing mailbox for user [{mailbox['user']}]")

    try:

        mailbox_file = f"{os.path.join(os.path.dirname(os.path.abspath(__file__)), mailbox['user'], "my_mailbox")}"

        with open(mailbox_file, 'w') as m:

            for mail in mailbox['mailbox_messages']:
                
                if not mailbox['mailbox_messages'][str(mail)]['to_be_deleted']:

                    m.write(f"From: {mailbox['mailbox_messages'][str(mail)]['from']}\n")
                    m.write(f"To: {mailbox['mailbox_messages'][str(mail)]['to']}\n")
                    m.write(f"Subject: {mailbox['mailbox_messages'][str(mail)]['subject']}\n")
                    m.write(f"Received: {mailbox['mailbox_messages'][str(mail)]['received']}\n")

                    for line in mailbox['mailbox_messages'][str(mail)]['message_body']:
                        m.write(f"{line}\n")
                    
                    m.write(".\n")

        m.close()

    except Exception as e:
        logger.error(e)
        print(e)

def read_mailbox(user):

    """
    mailbox
        user
        message_count
        total_size
        deleted_messages
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
        mailbox_file = f"{os.path.join(os.path.dirname(os.path.abspath(__file__)), user, "my_mailbox")}"

        with open(mailbox_file, 'r') as m:
            mailbox_lines = m.readlines()

        m.close()

        mailbox = {}
        mailbox['user'] = user
        mailbox['total_size'] = 0
        mailbox['message_count'] = 0
        mailbox['deleted_messages'] = False
        mailbox['mailbox_messages'] = {}

        mail_count = 0

        if len(mailbox_lines) > 0:

            mail = {"from": None, "to": None, "received": None, "subject": None, "message_body": [], "message_size": 0, "to_be_deleted": False}

            for line in mailbox_lines:
                
                line = line.strip()
                logger.debug(f"   >>> {line}")

                if line == ".":
                    logger.debug("   this is a . line")
                    
                    mail_count += 1
                    mailbox['message_count'] += 1

                    mail['message_size'] = get_size(mail)
                    mailbox["total_size"] += get_size(mail)

                    logger.debug(mail)
                    mailbox['mailbox_messages'][str(mail_count)] = mail

                    logger.debug(f"current mail count {mail_count}")
                    mail = {"from": None, "to": None, "received": None, "subject": None, "message_body": [], "message_size": 0, "to_be_deleted": False}

                else:

                    line_split = line.split(' ')

                    if line_split[0].lower() == "from:":
                        logger.debug("   this is a FROM line")
                        mail["from"] = line[6:]

                    elif line_split[0].lower() == "to:":
                        logger.debug("   this is a TO line")
                        mail["to"] = line[4:]

                    elif line_split[0].lower() == "received:":
                        logger.debug("   this is a RECEIVED line")
                        mail["received"] = line[10:]

                    elif line_split[0].lower() == "subject:":
                        logger.debug("   this is a SUBJECT line")
                        mail["subject"] = line[9:]

                    else:
                        logger.debug("   this is a MESSAGE BODY line")
                        mail["message_body"].append(line)

            return mailbox

    except Exception as e:
        logger.error(e)
        print(f"Error: {e}")
                        
def read_user_info():

    logger.info("Process - read_user_info")

    try:
        userinfo_file = f"{os.path.join(server_config['WORKING_DIR'], "userinfo.txt")}"
        logger.debug(f"   {userinfo_file} contains all users and passwords")

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