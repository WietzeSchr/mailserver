import socket
import argparse
import getpass
import re
import logging

def send_mail_smtp(client_config, message):
    
    # This function sends smtp commands to the smtp server
    # The function receives:
    #    client_config - contains the host and port for the smtp server
    #    message - a list with the checked mail lines

    logger.info("Send mail to smtp server")
    try:
        logger.debug(f"   Connect to: {client_config['SMTP_HOST']} on port: {client_config['SMTP_PORT']}")
        client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        client.connect((client_config['SMTP_HOST'], client_config['SMTP_PORT']))

        # receive response from the server after connect and print
        response = client.recv(1024).decode("utf-8")
        logger.debug(f"   {response}")
        print(f"Server: {response}")

        # send HELO message after successful connect (220)
        if response[:3] == "220":
            client.send(f"HELO {client_config['SMTP_HOST']}".encode("utf-8")[:1024])
            # receive response from the server after HELO and print
            response = client.recv(1024).decode("utf-8")
            logger.debug(f"   {response}")
            print(f"Server: {response}")
        
        # send MAIL_FROM message after succesful HELO (250)
        if response[:3] == "250":
            client.send(f"{message[0].replace("From", "MAIL_FROM")}".encode("utf-8")[:1024])
            # receive response from the server after MAIL_FROM and print
            response = client.recv(1024).decode("utf-8")
            logger.debug(f"   {response}")
            print(f"Server: {response}")

        # send RCPT_TO message after succesful MAIL_FROM (250)
        if response[:3] == "250":
            client.send(f"{message[1].replace("To", "RCPT_TO")}".encode("utf-8")[:1024])
            # receive response from the server after RCPT_TO and print
            response = client.recv(1024).decode("utf-8")
            logger.debug(f"   {response}")
            print(f"Server: {response}")
        
        # send DATA message after succesful RCPT_TO (250)
        if response[:3] == "250":
            client.send(f"DATA".encode("utf-8")[:1024])
            # receive response from the server after DATA and print
            response = client.recv(1024).decode("utf-8")
            logger.debug(f"   {response}")
            print(f"Server: {response}")

        ## send the mail lines after successful DATA (354)
        #if response[:3] == "354":
        #    for line in message:
        #        client.send(line.encode("utf-8")[:1024])

        #response = client.recv(1024).decode("utf-8")
        #logger.debug(f"   {response}")
        #print(f"Server: {response}")

        # temporarily set response to 250 and get response after each line
        if response[:3] == "250":
            for line in message:
                client.send(line.encode("utf-8")[:1024])

                response = client.recv(1024).decode("utf-8")
                logger.debug(f"   {response}")
                print(f"Server: {response}")

        # send QUIT message after successful sending mail lines (250)
        if response[:3] == "250":
            client.send(f"QUIT".encode("utf-8")[:1024])
            response = client.recv(1024).decode("utf-8")
            logger.debug(f"   {response}")
            print(f"Server: {response}")

    except Exception as e:
        print(f"Error: {e}")

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

def mail_management(client_config):
    
    logger.info("Menu option - Mail Management - selected")

    connect_TCP_socket(client_config['POP3_HOST'], client_config['POP3_PORT'])

def mail_searching(client_config):

    logger.info("Menu option - Mail Searching - selected")

    connect_TCP_socket(client_config['POP3_HOST'], client_config['POP3_PORT'])

def get_user_credentials():
    
    # This function requests the user name and password
    #
    # This function returns a dictionary with the users credentials

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
    
if __name__ == "__main__":

    parser = argparse.ArgumentParser(description='Get commandline arguments')
    parser.add_argument('-s', '--server', default="127.0.0.1", help='server address (IPv4)')
    parser.add_argument('-l', '--loglevel', default="INFO", help='Log level', choices=['INFO', 'DEBUG', 'WARNING', 'ERROR', 'CRITICAL'])
 
    args = parser.parse_args()

    logger = logging.getLogger()
    logger.setLevel(args.loglevel)
    
    # create file handler which logs even debug messages
    fh = logging.FileHandler('mail_client.log')
    fh.setLevel(logging.DEBUG)
    
    # create formatter and add it to the handlers
    formatter = logging.Formatter('%(asctime)s - %(levelname)-8s - %(message)s')
    fh.setFormatter(formatter)

    # add the handler to logger
    logger.addHandler(fh)

    logger.info("==============================")
    logger.info("=   MAIL CLIENT              =")
    logger.info("==============================")
    
    client_config = {"SMTP_HOST": args.server,
                     "SMTP_PORT": 25,
                     "POP3_HOST": args.server,
                     "POP3_PORT": 110}

    logger.info(f"Mail Client config:")
    logger.info(f"   SMTP_HOST: {client_config['SMTP_HOST']}")
    logger.info(f"   SMTP_PORT: {client_config['SMTP_PORT']}")
    logger.info(f"   POP3_HOST: {client_config['POP3_HOST']}")
    logger.info(f"   POP3_PORT: {client_config['POP3_PORT']}")

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
                mail_management(client_config)
            case "c":
                mail_searching(client_config)
            case "d":
                exit(0)
            case _:
                print("Invalid option!")