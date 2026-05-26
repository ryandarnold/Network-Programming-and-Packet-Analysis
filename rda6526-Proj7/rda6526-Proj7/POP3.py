import socket
import ssl

def create_connection(ip_address, POP3_port):
	#NOTE: again, SSL is old and I should have wrapped this TCP socket in a TLS socket, not SSL socket
	client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
	client_socket.connect((ip_address, POP3_port))
	contextInstance = ssl.SSLContext()  # ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
	client_socket = contextInstance.wrap_socket(client_socket)
	return client_socket

def AUTHORIZATION(client_socket, username, password):
	#need to enter your username and password, kinda similar to SMTP login authentication
	print("v---- AUTH ----v")
	USER = "USER " + str(username) + "\r\n"
	client_socket.sendall(USER.encode())
	server_message = client_socket.recv(1024)
	print(server_message)

	PASS = "PASS " + str(password) + "\r\n"
	client_socket.sendall(PASS.encode())
	server_message = client_socket.recv(1024)
	print(server_message)
	print("^---- AUTH ----^")

def send_msg_in_TRANSACTIONAL_state(client_socket, message: str):
	#simply sends a message while in transactional state
	client_socket.sendall(message.encode())
	server_message = client_socket.recv(2048)
	print(server_message.decode())

def receive_emails(client_socket):
	#RFC 1939 for list of commands to server
	message = "STAT\r\n"
	send_msg_in_TRANSACTIONAL_state(client_socket, message)

	message = "LIST 1\r\n"
	send_msg_in_TRANSACTIONAL_state(client_socket, message)

	print("v------first email!------v")
	message = "RETR 1\r\n"
	send_msg_in_TRANSACTIONAL_state(client_socket, message)
	server_message = client_socket.recv(2048)
	print(server_message.decode())
	server_message = client_socket.recv(2048)
	print(server_message.decode())
	print("^------first email!------^")

	print("v------third email!------v")
	message = "RETR 3\r\n"
	send_msg_in_TRANSACTIONAL_state(client_socket, message)
	server_message = client_socket.recv(2048)
	print(server_message.decode())
	print("^------third email!------^")


def update_state(client_socket):
	#UIDL is the unique identifier for each message received in inbox
	print("v-----UIDL-----v")
	message = "UIDL 1\r\n"
	send_msg_in_TRANSACTIONAL_state(client_socket, message) #simply sends
	server_message = client_socket.recv(2048)
	print(server_message.decode())
	print("^-----UIDL-----^")

def main():
	#NOTE: See RFC 1939 for this document
	myLaptopHostname = socket.gethostname()
	myLaptopIP = socket.gethostbyname(myLaptopHostname)
	print("this laptop's IP: " + str(myLaptopIP))
	print(ssl.OPENSSL_VERSION)

	POP_server = 'pop.gmail.com' #google's POP server
	ip_address = socket.gethostbyname(POP_server)
	POP3_port = 995 #995 is SSL

	# Establish a TCP connection to the SMTP server
	client_socket = create_connection(ip_address, POP3_port)


	#NOTE: All commands are terminated by a CRLF (\r\n) pair.
	#very end of command is \r\n.\r\n
	server_greeting = client_socket.recv(1024)
	print(server_greeting)

	#from here down we are in the server's AUTHORIZATION state
	username = "emailName@gmail.com" #enter your email username here
	password = 'fovd vthv zatg ryec' # enter your temporary APP password here fovd vthv zatg ryec
	AUTHORIZATION(client_socket, username, password)

	#from here down we are in the TRANSACTION state
	receive_emails(client_socket)
	client_socket.sendall("QUIT \r\n".encode())

	#from here down we are in the UPDATE state
	update_state(client_socket)


if __name__ == '__main__':
	main()