NOTE: You must run the reliable-receiver.py code first! Or else the transmitter won't know who to send to

-only sends and receives .txt files!

-the title/name of the file to be sent/received is NOT sent as 512 bytes of data, only the actual data is sent as 512 byte increments
-you must send at least 3 packets (each with 512 bytes (seq nums 0-2)) to properly calculate the appropriate timeout value 
(TO = (average RTT) + (4)(sigma), where sigma is the standard deviation). Otherwise the timeout time will be default = 1 second

-connect: since you input the port numbers and destination IP addresses as arguments, all 'connect' command does it start the three-way handshake
(which technically isn't needed for data transfer but since we're emulating a real TCP protocol, it is nice to have) between the receiver and transmitter

-for the commands 'connect', 'put' and 'get', you are only able to send/receive one file, then the entire program at both ends finishes. 
You need to restart both programs to send/receive additional files
-for the commands "quit" and "?", you can only enter "quit" at the beginning of the program, before sending or receiving anything, and before connecting. otherwise the program won't work (I know, I know. but it was going to require more logic to end the program after initially connecting and THEN quitting)
-NOTE: you must enter the 'connect' command in the console first before you're able to send/receive files! Or else the program won't work

Step 1) run the 'reliable-receiver.py' program:

example format: 
python3 reliable-receiver.py -dest [name_of_destination_IP_address] -sending_port [port_num_you're_using_to_send] -receiving_port [port_num_you're_using_to_receive]

example: 
python3 reliable-receiver.py -dest 127.0.1.1 -sending_port 5006 -receiving_port 5005


-For the receiver to fully finish writing the received file from the transmitter, you must manually "ctrl-c" or stop the receiver program. Then you will see the sent file on the server




Step 2) run the "reliable-transmitter.py" program: 

example format: 
python3 reliable-transmitter.py -dest [name_of_destination_IP_address] -sending_port [port_num_you're_using_to_send] -receiving_port [port_num_you're_using_to_receive]


example:

python3 reliable-transmitter.py -dest 127.0.1.1 -sending_port 5005 -receiving_port 5006


Step 3) Type "connect" and press enter, which initializes the three-way handshake between transmitter and receiver. Wait for up to 5 seconds until 
you can enter a new command in the 'reliable-transmitter.py' console window

Step 4) Type "put" and then the name of the file you want to send to the server/receiver
example: 

put nameOfFile.txt 

Step 4.5 (optional) type "get" and then the name of the file you want receive from the server/receiver
example: 
 get nameOfFile.txt

Step 5) terminate the receiveer python program and the sent file will appear in the local directory of the python file














