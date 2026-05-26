import socket
import ssl
import base64



def initiate_connection(client_socket):
	#server sends some of its information when connecting to it via TCP
	print("v-----initiate connection-----v")
	server_greeting = client_socket.recv(1024)  # 220 smtp.gmail.com ESMTP z4-20020ac86b84000000b004399a5bbea5sm91699qts.56 - gsmtp
	print(server_greeting.decode())
	print("^-----initiate connection-----^")

def greeting_and_commands(client_socket, ip_address):
	# Receive the server's greeting
	# Send EHLO command to initiate the SMTP session
	print("v-----greeting and commands-----v")
	#NOTE: I don't think the [129.21.134.245] IP address below is used but keep it in there just in case
	client_socket.sendall(b'EHLO [129.21.134.245]\r\n') #129.21.135.229
	server_response = client_socket.recv(1024)  # prints out different commands client can send to smtp server
	print(server_response.decode())
	print("^-----greeting and commands-----^")

def start_TLS_encryption(client_socket) -> socket:
	print("v-----START TLS CONN-----v")
	client_socket.sendall(b'STARTTLS\r\n')  # tells server to start a TLS session for secure communication
	tls_response = client_socket.recv(1024)
	print(tls_response.decode())
	contextInstance = ssl.SSLContext()  # ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
	client_socket = contextInstance.wrap_socket(client_socket)
	print("^-----START TLS CONN-----^")
	return client_socket

def send_login_credentials(client_socket, username, password):
	print("v-----AUTHORIZE LOGIN-----v")
	auth_command = f'AUTH LOGIN {base64.b64encode(username.encode()).decode()}\r\n'
	client_socket.sendall(auth_command.encode())
	auth_response = client_socket.recv(1024)

	print(auth_response.decode())

	password_command = f'{base64.b64encode(password.encode()).decode()}\r\n'
	client_socket.sendall(password_command.encode())
	password_response = client_socket.recv(1024)
	print(password_response.decode())
	print("^-----AUTHORIZE LOGIN-----^")

def send_email(client_socket, from_address, to_address, subject, body):
	#NOTE: found in RFC 5321
	#step 1) MAIL FROM:<reverse-path> [SP <mail-parameters> ] <CRLF>
	#step 2) RCPT TO:<forward-path> [ SP <rcpt-parameters> ] <CRLF>
	#step 3) DATA <CRLF>
	#step 4) (send the data of the actual email here)
	#step 5) \r\n.\r\n                    #to end the email
	print("v-----MAIL FROM-----v")
	MAILFROM = "MAIL FROM:<" + str(from_address) + ">\r\n"
	client_socket.sendall(MAILFROM.encode()) #encodes string as UTF-8
	print("sent: " + str(MAILFROM))
	server_response = client_socket.recv(1024)
	print(server_response.decode())
	print("^-----MAIL FROM-----^")

	print("v-----RCPT TO-----v")
	RCPTTO = "RCPT TO:<" + str(to_address) + ">\r\n"
	client_socket.sendall(RCPTTO.encode())
	print("sent: " + str(RCPTTO))
	server_response = client_socket.recv(1024)
	print(server_response.decode())
	print("^-----RCPT TO-----^")

	# client_socket.sendall(f'Message-ID: <CAD5iMkUmf-mudSiv6F2nNH29MXRG-Tv-NrTJk-fDzZ4DzJUO0A@mail.gmail.com>\r\n'.encode())
	# email_response = client_socket.recv(1024)
	# print(email_response.decode())
	print("v-----DATA -----v")
	client_socket.sendall(b'DATA \r\n')
	print("sent: DATA")
	server_response = client_socket.recv(1024)
	print(server_response.decode())
	print("^-----DATA -----^")

	print("v-----SUBJECT-----v")
	#subject_message = "cringe worthiness hoohoo"
	#TEXT = "the epitome of internet culture"
	#message = 'Subject: {}\n\n'.format(SUBJECT) #WORKS
	SUBJECT = "Subject: " + str(subject) + "\n\n"
	# client_socket.sendall(f'Subject: {subject}\n\n{body}\r\n'.encode())
	client_socket.sendall(SUBJECT.encode())
	print("^-----SUBJECT-----^")

	print("v-----BODY-----v")
	client_socket.sendall(body.encode()) #send the body of the message
	print("sent: BODY")
	print("^-----BODY-----^")

	print("v-----ENDING EMAIL-----v")
	client_socket.sendall(b'\r\n.\r\n') #tells server that there is no more information to put into email
	server_response = client_socket.recv(1024)
	print(server_response.decode())
	print("^-----ENDING EMAIL-----^")



def main():
	myLaptopHostname = socket.gethostname()
	myLaptopIP = socket.gethostbyname(myLaptopHostname)
	print("this laptop's IP: " + str(myLaptopIP))
	print(ssl.OPENSSL_VERSION)
	# SMTP server details
	#NOTE: aspmx.l.google.com works up to the "550-5.7.1 Messages missing a valid Message-ID header are not accepted
	smtp_server = 'smtp.gmail.com' #  smtp.gmail.com   smtp.mail.yahoo.com   aspmx.l.google.com
	ip_address = socket.gethostbyname(smtp_server)
	#NOTE: smtp_port = 25 works a lot of the way for smtp.gmail.com
	#NOTE: smtp_port = 587 works with smtp.mail.yahoo.com
	smtp_port = 587 #smtp_port = 465  # Example port for SMTP with TLS

	# Establish a TCP connection to the SMTP server
	client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
	client_socket.connect((ip_address, smtp_port))


	initiate_connection(client_socket)

	greeting_and_commands(client_socket, ip_address)

	# Start TLS encryption
	client_socket = start_TLS_encryption(client_socket)


	# Send authentication commands to verify the person sending the email isn't spam
	username = '' #username to log into your email account
	password = '' #google-generated temporary app password

	send_login_credentials(client_socket, username, password)


	# Send the email
	from_address = '' #where this email is coming from
	to_address = '' #email address to send to
	subject = 'god I love pancakes yummy'
	body = 'Maple syrup was invented in (who knows) and was \nlater used for pancakes haha'
	send_email(client_socket, from_address, to_address, subject, body)


	# Close the SMTP connection to server
	client_socket.sendall(b'QUIT\r\n')
	client_socket.close()


if __name__ == '__main__':
	main()
