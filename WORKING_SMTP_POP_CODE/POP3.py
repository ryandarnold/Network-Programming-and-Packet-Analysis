import socket
import ssl

def create_connection(ip_address, POP3_port):
	client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
	client_socket.connect((ip_address, POP3_port))
	contextInstance = ssl.SSLContext()  # ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
	client_socket = contextInstance.wrap_socket(client_socket)
	return client_socket

def AUTHORIZATION(client_socket, username, password):
	USER = "USER " + str(username) + "\r\n"
	#client_socket.sendall(b'USER \r\n')
	client_socket.sendall(USER.encode())
	server_message = client_socket.recv(1024)
	print(server_message)

	PASS = "PASS " + str(password) + "\r\n"
	client_socket.sendall(PASS.encode())
	server_message = client_socket.recv(1024)
	print(server_message)

def send_msg_in_TRANSACTIONAL_state(client_socket, message: str):
	client_socket.sendall(message.encode())
	server_message = client_socket.recv(2048)
	print(server_message.decode())

def receive_emails(client_socket):
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
	#print("\n\n\n\n\n")
	print("^------first email!------^")



	print("v------third email!------v")
	message = "RETR 3\r\n"
	send_msg_in_TRANSACTIONAL_state(client_socket, message)
	server_message = client_socket.recv(2048)
	print(server_message.decode())
	print("^------third email!------^")
	# server_message = client_socket.recv(2048)
	# print(server_message.decode())

def main():
	#NOTE: See RFC 1939 for this document
	myLaptopHostname = socket.gethostname()
	myLaptopIP = socket.gethostbyname(myLaptopHostname)
	print("this laptop's IP: " + str(myLaptopIP))
	print(ssl.OPENSSL_VERSION)

	POP_server = 'pop.gmail.com'
	ip_address = socket.gethostbyname(POP_server)
	POP3_port = 995 #995 is SSL

	# Establish a TCP connection to the SMTP server
	client_socket = create_connection(ip_address, POP3_port)


	#NOTE: All commands are terminated by a CRLF (\r\n) pair.
	#very end of command is \r\n.\r\n
	server_greeting = client_socket.recv(1024)
	print(server_greeting)

	#from here down we are in the server's AUTHORIZATION state
	username = "emailName@gmail.com"
	password = 'zfmk sehr sfts vqbd' #POP3 password
	AUTHORIZATION(client_socket, username, password)

	#from here down we are in the TRANSACTION state
	receive_emails(client_socket)
	client_socket.sendall("QUIT \r\n".encode())

	#from here down we are in the UPDATE state



if __name__ == '__main__':
	main()
