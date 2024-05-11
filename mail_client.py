import socket
import argparse
import getpass
import re
import logging
import time
import os

def send_mail_smtp(client_config, message):
    
    # This function sends correct formatted smtp commands to the server
    #
    # Supported SMTP commands by this function, with their correct syntax
    # according to RFC821 - https://www.rfc-editor.org/rfc/rfc821
    #
    #     HELO <SP> <domain> <CRLF>
    #     MAIL <SP> FROM:<reverse-path> <CRLF>
    #     RCPT <SP> TO:<forward-path> <CRLF>
    #     DATA <CRLF>
    #     QUIT <CRLF>
    # 
    # Possible return codes:
    #
    #     211 System status, or system help reply
    #     220 <domain> Service ready
    #     221 <domain> Service closing transmission channel
    #     250 Requested mail action okay, completed
    #     251 User not local; will forward to <forward-path>
    #     550 Requested action not taken: mailbox unavailable
    #     354 Start mail input; end with <CRLF>.<CRLF>
    #

    logger.info("Send mail to smtp server")
    try:
        # Connect to SMTP server
        logger.debug(f"   Connect to: {client_config['SMTP_HOST']} on port: {client_config['SMTP_PORT']}")

        client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        client.connect((client_config['SMTP_HOST'], client_config['SMTP_PORT']))

        # receive response from the server after connect and print
        response = client.recv(1024).decode("utf-8")
        logger.info(f"   Server: {response}")
        print(f"Server: {response}")

        # send HELO message after successful connect (220)
        if response[:3] == "220":
            client.send(f"HELO {client_config['SMTP_HOST']}".encode("utf-8")[:1024])
            logger.info(f"   Client: HELO {client_config['SMTP_HOST']}")
            # receive response from the server after HELO and print
            response = client.recv(1024).decode("utf-8")
            logger.info(f"   Server: {response}")
            print(f"Server: {response}")
            
        # send MAIL_FROM message after succesful HELO (250)
        if response[:3] == "250":
            client.send(f"MAIL {message[0]}".encode("utf-8")[:1024])
            logger.info(f"   Client: MAIL {message[0]}")
            # receive response from the server after MAIL_FROM and print
            response = client.recv(1024).decode("utf-8")
            logger.info(f"   Server: {response}")
            print(f"Server: {response}")

        # send RCPT_TO message after succesful MAIL (250)
        if response[:3] == "250":
            client.send(f"RCPT {message[1]}".encode("utf-8")[:1024])
            logger.info(f"   Client: RCPT {message[1]}")
            # receive response from the server after RCPT_TO and print
            response = client.recv(1024).decode("utf-8")
            logger.info(f"   Server: {response}")
            print(f"Server: {response}")
            
        # send DATA message after succesful RCPT (250)
        if response[:3] == "250":
            client.send(f"DATA".encode("utf-8")[:1024])
            logger.info(f"   Client: DATA")
            # receive response from the server after DATA and print
            response = client.recv(1024).decode("utf-8")
            logger.info(f"   Server: {response}")
            print(f"Server: {response}")

        # send the mail lines after successful DATA (354)
        if response[:3] == "354":
            logger.debug("start sending email text")
            for line in message:
                client.send(line.encode("utf-8")[:1024])
                logger.info(f"   Client: {line}")

                # wait for server
                time.sleep(0.1)

            response = client.recv(1024).decode("utf-8")
            logger.info(f"   Server: {response}")
            print(f"Server: {response}")

        # send QUIT message after successful sending mail lines (250)
        if response[:3] == "250":
            client.send(f"QUIT".encode("utf-8")[:1024])
            logger.info(f"   Client: QUIT")
            response = client.recv(1024).decode("utf-8")
            logger.info(f"   Server: {response}")
            print(f"Server: {response}")

    except Exception as e:
        print(f"ERROR: {e}")

    finally:
        # close client socket (connection to the server)
        client.close()
        logger.info(f"Connection to server [{client_config['SMTP_HOST']}] on port [{client_config['SMTP_PORT']}] closed")
        
def check_mail(message):

    # This function checks the mail message on correct formatting
    # The format of the mail meessage should be:
    #    "From: <username>@<domain name>"
    #    "To: <username>@<domain name>"
    #    "Subject: <subject string, max 150 characters>"
    #    "<Message body – one or more lines, terminated by a final line with only a full stop character>"
    #
    # The function receives a list of lines.
    # The function expects:
    #    The first line to be the FROM part
    #    The second line to be the TO part
    #    The third line to be the SUBJECT part
    #    The last line to be a single full stop character (.)
    #
    # The function returns True if the formatting is OK
    # The function returns False if the formatting is not OK

    logger.info("Check mail message")

    check_mail_OK = True

    if len(message) > 0:
        # First line should contain the FROM part - From: <username>@<domain name>
        if re.match(r'(^FROM: [a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$)', message[0], re.IGNORECASE):
            logger.debug(f"   [{message[0]}] - OK")
        else:
            check_mail_OK = False
            logger.debug(f"   [{message[0]}] - invalid pattern - From: <username>@<domain name>")
        
        # Second line should contain the TO part - To: <username>@<domain name>
        if re.match(r'(^TO: [a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$)', message[1], re.IGNORECASE):
            logger.debug(f"   [{message[1]}] - OK")
        else:
            check_mail_OK = False
            logger.debug(f"   [{message[1]}] - invalid pattern - To: <username>@<domain name>")
        
        # Third line should contain the SUBJECT part - Subject: <subject string, max 150 characters>
        if re.match(r'(^SUBJECT: .{0,150}$)', message[2], re.IGNORECASE):
            logger.debug(f"   [{message[2]}] - OK")
        else:
            check_mail_OK = False
            logger.debug(f"   [{message[2]}] - invalid pattern - Subject: <subject string, max 150 characters>")
        
        # Last line should be a Full stop character
        if message[len(message) - 1] == ".":
            logger.debug(f"   [{message[len(message) - 1]}] - OK")
        else:
            check_mail_OK = False
            logger.debug(f"   [{message[len(message) - 1]}] - invalid pattern - Last line should contain full stop character")
    
    return check_mail_OK

def get_mail_message():

    # This function requests a mail message from the user
    # Each line of input is stored in a list
    #
    # The function returns a list with all the lines
    
    logger.info("Get mail message from user input")

    print("")
    print("Please enter the mail message in the following format:")
    print("")
    print("From: <username>@<domain name>")
    print("To: <username>@<domain name>")
    print("Subject: <subject string, max 150 characters>")
    print("<Message body – one or more lines, terminated by a final line with only a full stop character>")
    print("")

    mail_message = []

    while True:

        user_input = input()
        mail_message.append(user_input)

        if user_input == ".":
            break
    
    for line in mail_message:
        logger.debug(f"   {line}")

    return mail_message

def mail_searching_words(mail_messages):

    logger.info("Process - mail_searching_words")

    search_string = input("input: ")
    logger.info(f"   Input: {search_string}")

    print("output:")

    for message in mail_messages:
        logger.debug(f">>> {mail_messages[message]}")
        string_found = False

        for key, value in mail_messages[message].items():
            logger.debug(f"   >>> searching in : {key} [{value}]")
            
            if search_string in value:
                string_found = True
        
        if string_found:
            logger.info(f"   Found: {mail_messages[message]}")
            print(mail_messages[message])

def mail_searching_senders(mail_messages):

    logger.info("Process - mail_searching_senders")

    search_sender = input("input: ")
    logger.info(f"   Input: {search_sender}")

    print("output:")

    for message in mail_messages:
        if mail_messages[message]['from'] == search_sender:
            logger.info(f"   Found: {mail_messages[message]}")
            print(mail_messages[message])

def mail_searching_date(mail_messages):

    logger.info("Process - mail_searching_date")

    search_date = input("input (DD/MM/YYYY): ")
    logger.info(f"   Input: {search_date}")

    print("output:")

    for message in mail_messages:
        if mail_messages[message]['received'].split(' ')[0] == search_date:
            logger.info(f"   Found: {mail_messages[message]}")
            print(mail_messages[message])

def authenticate_pop(user_credentials, client):

    logger.info(f"Authenticating user [{user_credentials['name']}]")

    client.send(f"USER {user_credentials['name']}".encode("utf-8")[:1024])
    logger.info(f"   Client: USER {user_credentials['name']}")
    
    response = client.recv(1024).decode("utf-8")
    logger.info(f"   Server: {response}")
    print(f"Server: {response}")

    if response == "+OK Please enter a password":

        message = f"PASS {user_credentials['password']}"
        client.send(message.encode("utf-8")[:1024])
        logger.info(f"   Client: {message}")

        response = client.recv(1024).decode("utf-8")
        logger.info(f"   Server: {response}")
        print(f"Server: {response}")

        if response == "+OK valid logon":

            return True

        else:

            return False

    else:

        return False

def mail_sending(client_config):

    logger.info("Menu option - Mail Sending - selected")

    # Get the mail message
    mail_message = get_mail_message()
    
    # Check the mail message
    mail_format_OK = check_mail(mail_message)

    if mail_format_OK:
        logger.debug("   Mail format OK!")
        send_mail_smtp(client_config, mail_message)
    else:
        logger.error("   Mail format NOT OK!")
        print("This is an incorrect format")

def mail_management(client_config, user_credentials):
    
    logger.info("Menu option - Mail Management - selected")

    client = None
    try:
        logger.info(f"Connecting to POP3 server [{client_config['POP3_HOST']}] on port [{client_config['POP3_PORT']}]")

        client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        client.connect((client_config['POP3_HOST'], client_config['POP3_PORT']))

        response = client.recv(1024).decode("utf-8")
        logger.info(f"   Server: {response}")
        print(f"Server: {response}")

        # authenticate the user

        if response == "+OK POP3 server ready":

            while not authenticate_pop(user_credentials, client):
                user_credentials = get_user_credentials()

        client.send("LIST".encode("utf-8"))
        logger.info(f"   Client: LIST")

        response = client.recv(1024).decode("utf-8")
        logger.info(f"   Server: {response}")

        if response == "+OK":

            print("")
            print("========================================")
            print("   YOUR MAILS")
            print("========================================")
            print("")

            response = client.recv(1024).decode("utf-8")
            logger.info(f"   Server: {response}")

            while not response == ".":

                print(f"    {response}")
                response = client.recv(1024).decode("utf-8")
                logger.info(f"   Server: {response}")

            display_management_options()

        running_conversation = True
        while running_conversation:

            line = input()
            pop3_command = line.split(' ')

            match pop3_command[0]:

                case "STAT":

                    client.send(line.encode("utf-8"))
                    logger.info(f"   Client: {line}")
                    response = client.recv(1024).decode("utf-8")
                    print(f"Server: {response}")
                    logger.info(f"   Server: {response}")

                case "LIST":

                    client.send(line.encode("utf-8"))
                    logger.info(f"   Client: {line}")
                    response = client.recv(1024).decode("utf-8")
                    logger.info(f"   Server: {response}")

                    if response == "+OK":

                        print("")
                        print("========================================")
                        print("   YOUR MAILS")
                        print("========================================")
                        print("")

                        response = client.recv(1024).decode("utf-8")
                        logger.info(f"   Server: {response}")

                        while not response == ".":
                            print(f"    {response}")
                            response = client.recv(1024).decode("utf-8")
                            logger.info(f"   Server: {response}")

                case "RETR":

                    client.send(line.encode("utf-8"))
                    logger.info(f"   Client: {line}")
                    time.sleep(0.1)

                    response = client.recv(1024).decode("utf-8")
                    logger.info(f"   Server: {response}")
                    print(f"Server: {response}")
                    if response[:3] == "+OK":

                        response = client.recv(1024).decode("utf-8")
                        logger.info(f"   Server: {response}")

                        while not response == ".":
                            print(response)
                            response = client.recv(1024).decode("utf-8")
                            logger.info(f"   Server: {response}")

                case "DELE":

                    client.send(line.encode("utf-8"))
                    logger.info(f"   Client: {line}")
                    response = client.recv(1024).decode("utf-8")
                    logger.info(f"   Server: {response}")
                    print(f"Server: {response}")

                case "RSET":

                    client.send(line.encode("utf-8"))
                    logger.info(f"   Client: {line}")
                    response = client.recv(1024).decode("utf-8")
                    logger.info(f"   Server: {response}")
                    print(f"Server: {response}")

                case "QUIT":

                    client.send(line.encode("utf-8"))
                    logger.info(f"   Client: {line}")

                    response = client.recv(1024).decode("utf-8")
                    logger.info(f"   Server: {response}")
                    print(f"Server: {response}")
                    if response == "closed":
                        running_conversation = False

                case _:

                    print("Invalid command!")

    except Exception as e:
        print(f"ERROR: {e}")
        logger.error(f"   {e}")

    finally:
        # close client socket (connection to the server)
        client.close()
        logger.info(f"Connection to server [{client_config['SMTP_HOST']}] on port [{client_config['SMTP_PORT']}] closed")

def mail_searching(client_config, user_credentials):

    logger.info("Menu option - Mail Searching - selected")

    client = None
    try:
        logger.info(f"Connecting to POP3 server [{client_config['POP3_HOST']}] on port [{client_config['POP3_PORT']}]")

        client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        client.connect((client_config['POP3_HOST'], client_config['POP3_PORT']))

        response = client.recv(1024).decode("utf-8")
        logger.info(f"   Server: {response}")
        print(f"Server: {response}")

        # authenticate the user

        if response == "+OK POP3 server ready":

            while not authenticate_pop(user_credentials, client):
                user_credentials = get_user_credentials()
        
        client.send("STAT".encode("utf-8"))
        logger.info(f"   Client: STAT")
        response = client.recv(1024).decode("utf-8")
        logger.info(f"   Server: {response}")
        
        rc, message_count, mailbox_size = response.split(' ')

        mail_messages = {}

        for i in range(1, int(message_count) + 1):
            mail = {}
            mail['from'] = ""
            mail['to'] = ""
            mail['subject'] = ""
            mail['received'] = ""
            mail['message'] = ""

            client.send(f"RETR {i}".encode("utf-8"))
            logger.info(f"   Client: RETR {i}")
            time.sleep(0.1)
            response = client.recv(1024).decode("utf-8")
            logger.info(f"   Server: {response}")

            if response[:3] == "+OK":
                response = client.recv(1024).decode("utf-8")
                logger.info(f"   Server: {response}")
                while not response == ".":

                    if response[0:6] == "From: ":
                        mail['from'] = response[6:]
                    elif response[0:4] == "To: ":
                        mail['to'] = response[4:]
                    elif response[0:9] == "Subject: ":
                        mail['subject'] = response[9:]
                    elif response[0:10] == "Received: ":
                        mail['received'] = response[10:]
                    else:
                        mail['message'] += f"{response}\n"

                    logger.debug(response)
                    response = client.recv(1024).decode("utf-8")
                    logger.info(f"   Server: {response}")
            
            mail_messages[str(i)] = mail

        menu_option = ""

        while (not menu_option == "d"):
            # display menu
            display_search_menu()

            menu_option = input("Option: ")

            match menu_option:
                case "a":
                    mail_searching_words(mail_messages)
                case "b":
                    mail_searching_senders(mail_messages)
                case "c":
                    mail_searching_date(mail_messages)
                case "d":
                    exit(0)
                case _:
                    print("Invalid option!")

    except Exception as e:
        print(f"ERROR: {e}")
        logger.error(f"   {e}")

    finally:
        # close client socket (connection to the server)
        client.close()
        logger.info(f"Connection to server [{client_config['SMTP_HOST']}] on port [{client_config['SMTP_PORT']}] closed")

def get_user_credentials():
    
    # This function requests the user name and password and
    # returns a dictionary with the users credentials

    logger.info(f"Get user credentials")

    user_credentials = {}
    user_credentials['name'] = input("Username: ")
    user_credentials['password'] = getpass.getpass()

    logger.debug(f"   user name:     {user_credentials['name']}")
    logger.debug(f"   user password: {user_credentials['password']}")

    return user_credentials

def display_menu():
    
    # This function displays the mail client menu
    logger.info("Display mail client menu")

    print("")
    print("========================================")
    print("   MAIL CLIENT")
    print("========================================")
    print("")
    print("   a)   Mail Sending")
    print("   b)   Mail Management")
    print("   c)   Mail Searching")
    print("   d)   Exit")
    print("")

def display_management_options():

    # This function displays the mail management menu
    print("")
    print("Possible commands:")
    print("LIST - lists all mails")
    print("STAT - returns +OK <mail_count> <total_size>")
    print("RETR <Mail_index> - retrieves mail with given index")
    print("DELE <Mail_index> - deletes mail with given index on the server")
    print("RSET - reset mails that were marked deleted")
    print("QUIT - close connection")
    print("")
    print(">")

def display_search_menu():

    # This function displays the mail search menu
    print("")
    print("========================================")
    print("   MAIL CLIENT")
    print("========================================")
    print("")
    print("   a)   Mail Search on words")
    print("   b)   Mail Search on senders id")
    print("   c)   Mail Search on date")
    print("   d)   Exit")
    print("")

if __name__ == "__main__":

    # Get the arguments passed to the script
    #
    #    server   : ip address on which the server will be running - default: 127.0.0.1
    #    loglevel : loglevel on which the script is running, to achieve less or more logging - default: INFO
    
    parser = argparse.ArgumentParser(description='Get commandline arguments')
    parser.add_argument('-s', '--server', default="127.0.0.1", help='server address (IPv4)')
    parser.add_argument('-l', '--loglevel', default="INFO", help='Log level', choices=['INFO', 'DEBUG', 'WARNING', 'ERROR', 'CRITICAL'])
 
    args = parser.parse_args()

    # Create a dictionary with configuration options for the client
    # to be able to pass through the script.

    client_config = {"WORKING_DIR": os.path.dirname(os.path.abspath(__file__)),
                     "LOG_DIR": os.path.join(os.path.dirname(os.path.abspath(__file__)), 'logfiles'),
                     "MAILBOX_DIR": os.path.join(os.path.dirname(os.path.abspath(__file__)), 'mailboxes'),
                     "SMTP_HOST": args.server,
                     "SMTP_PORT": 25,
                     "POP3_HOST": args.server,
                     "POP3_PORT": 110}
    
    # Instantiate a logger, to have a log file with all or specific messages logged by the script
    # based on a loglevel.

    logger = logging.getLogger()
    logger.setLevel(args.loglevel)
    
    # Create file handler in which the messages will be logged
    # and set a default loglevel

    fh = logging.FileHandler(os.path.join(client_config['LOG_DIR'], 'log', 'mail_client.log'))
    fh.setLevel(logging.DEBUG)
    
    # Create formatter and add it to the handler
    # to have a standardized output format in the logfile.

    formatter = logging.Formatter('%(asctime)s - %(levelname)-8s - %(message)s')
    fh.setFormatter(formatter)

    # add the handler to logger
    logger.addHandler(fh)

    logger.info("==============================")
    logger.info("=   MAIL CLIENT              =")
    logger.info("==============================")
    logger.info("")
    logger.info(f"Mail Client config:")

    # Log all config parameters
    for key, value in client_config.items():
        logger.info(f"   {key}: [{value}]")

    # ask for user credentials
    user_credentials = get_user_credentials()

    menu_option = ""

    while( not menu_option == "d" ):
        # display menu
        display_menu()

        menu_option = input("Option: ")

        match menu_option:
            case "a":
                mail_sending(client_config)
            case "b":
                mail_management(client_config, user_credentials)
            case "c":
                mail_searching(client_config, user_credentials)
            case "d":
                exit(0)
            case _:
                print("Invalid option!")
