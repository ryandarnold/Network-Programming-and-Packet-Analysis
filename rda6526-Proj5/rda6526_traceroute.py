import socket
import struct
import sys
import time


def parse_args():
    argument_dictionary = {}
    #first argument is always either IP address or website URL
    argument_dictionary["ping"] = sys.argv[1]
    for x in range(2, len(sys.argv)):
        if sys.argv[x] == "-n":
            argument_dictionary["-n"] = "-n"
        if sys.argv[x] == "-q":
            argument_dictionary["-q"] = sys.argv[x+1]
        if sys.argv[x] == "-S":
            argument_dictionary["-S"] = "-S"
        if sys.argv[x] == "-h":
            argument_dictionary["-h"] = "-h"
        if sys.argv[x] == "--help":
            argument_dictionary["--help"] = "--help"
    return argument_dictionary


def return_ip_and_hostname(ip_or_URL, arg_dict):
    if "www" in ip_or_URL: #user entered normal URL
        try:
            hostname = ip_or_URL
            ip_addr = socket.gethostbyname(ip_or_URL)
        except socket.error as e:
            print(e)
    else: #raw IPv4 address
        try:
            ip_addr = ip_or_URL
            hostname = socket.gethostbyaddr(ip_addr)[0]
        except socket.error as e:
            print(e)

    return ip_addr, hostname

def calc_chksum(data_to_convert):
    # length is 20 because BBHHH = 8 bytes, and data_to_send = 12 bytes = 20 bytes total
    if len(data_to_convert) % 2 != 0:
        data_to_convert = data_to_convert + b'\x00'
    # 'H' is a sixteen bit value. But the struct.unpack requires you to add an 'H' or a 'B' for every byte you want to unpack
    # thus you must multiply the 'H' by the len(data)//2 because you want to convert a bunch of 8-bit words into 16 bit words
    # making the total number of 'H' half the original length of data_to_convert
    sixteen_bit_list = struct.unpack('H' * (len(data_to_convert) // 2), data_to_convert)  # ten 16-bit words
    sum = 0
    for x in sixteen_bit_list:
        sum = sum + x #note: this can result in overflow from the 16-bit sum you need
    upper_bits = sum >> 16 #grabs all the large digits
    lower_bits = sum & 0xFFFF #grabs the 16 lower bits
    upper_and_lower = upper_bits + lower_bits #recombines overflow back into sum
    #but recombining the overflow back into the sum can result in overflow again
    #so you must combine overflow back into the sum one more time
    upper_and_lower = upper_and_lower + (upper_and_lower >> 16)
    ones_complement_16_bits = ~upper_and_lower & 0xffff

    #wireshark says the upper and lower bits are in the wrong endianess so we need to flip it
    byte_1 = (ones_complement_16_bits >> 8) & 0x00FF
    byte_2 = (ones_complement_16_bits << 8) & 0xFF00
    reversed_checksum = byte_1 | byte_2
    return reversed_checksum

def create_data():
    data_size = 56 #56 bytes if data size not specified
    data_to_send = b''
    if data_size % 2 == 0:
        add_this_to_data = b'A' #'A' is for even length
    else:
        add_this_to_data = b'B' #'B is for odd length
    for x in range(0, data_size):
        data_to_send = data_to_send + add_this_to_data

    return data_to_send

def echo_request(dest_IP, data_to_send, ICMP_sequence_num, time_to_live):
    # create the raw ICMP socket
    ICMP_socket = socket.socket(socket.AF_INET, socket.SOCK_RAW, socket.IPPROTO_ICMP)
    ICMP_socket.setsockopt(socket.IPPROTO_IP, socket.IP_TTL, time_to_live) #TTL originally 63?

    ICMP_type = 8  # 8 is for echo request (i.e. 1 byte)
    ICMP_code = 0  # all echo requests and replies have code type of zero (i.e. 1 byte)
    initial_checksum = 0 # (i.e. 2 bytes)

    #below is 'rest of header'
    ICMP_identifier = 12345  # identifier allows sender (this program) to know which echo reply came in (i.e. 2 bytes)
    #above is 'rest of header'


    # ! for big endian, first 'B' because "ICMP_type" is 8 bits (and 'B' means 8 bits)
    # ICMP_code is 8 bits, so we use a second 'B'. 'H' is unsigned short (16 bits)
    # thus we use first 'H' for checksum, second 'H' for 16 bit ICMP_identifier
    # and third 'H' for 16-bit icmp_sequence
    ICMP_checksum=calc_chksum(struct.pack('!BBHHH', ICMP_type,ICMP_code,initial_checksum,ICMP_identifier,ICMP_sequence_num)+data_to_send)

    # creates the ICMP packet by concatenating everything together in byte and bytebyte form
    ICMP_packet = struct.pack('!BBHHH', ICMP_type, ICMP_code, ICMP_checksum,ICMP_identifier,ICMP_sequence_num) + data_to_send

    ICMP_socket.sendto(ICMP_packet, (dest_IP, 0))

    ICMP_socket.close()  # closes the connection of the socket

def receive_echo_reply(received_IP):
    ICMP_socket = socket.socket(socket.AF_INET, socket.SOCK_RAW, socket.IPPROTO_ICMP)
    #artificially setting timeout to three seconds
    ICMP_socket.settimeout(3)

    ICMP_packet = ICMP_socket.recv(1024) #the received ICMP packetIdentifier (BE): 12345 (0x3039)
    IP_header = ICMP_packet[:20] #IP header is first 20 bytes
    #inet_ntoa converts 32 bit packed IP address into byte.byte.byte.byte form
    incoming_ip = socket.inet_ntoa(struct.unpack("!4s", IP_header[12:16])[0])
    ICMP_header = ICMP_packet[20:28]
    icmp_type, icmp_code, icmp_checksum, icmp_id, icmp_seq = struct.unpack("bbHHH", ICMP_header)
    # icmp data is wrong endianess so need to flip

    received_data = ICMP_packet[28:]

    ICMP_socket.close()
    return incoming_ip

def find_duration(start_time):
    duration = time.time() - start_time
    duration_ms_decimal = duration * 1000
    split_list = str(duration_ms_decimal).split(".")
    duration_ms_no_decimal = split_list[0] + "." + split_list[1][:3]
    return duration_ms_no_decimal

def print_first_line(dest_ip, hostname, max_hops):
    #sending 64 byte ICMP packets. This is hardcoded
    print("Traceroute to " + str(hostname) + " (" + str(dest_ip) + "), " + str(max_hops) + " hops max, 64 byte packets" )

def start_traceroute(arg_dict):
    max_hops = 30 #hardcoded max hop number
    dest_ip, hostname = return_ip_and_hostname(arg_dict["ping"], arg_dict)
    print_first_line(dest_ip, hostname, max_hops)
    ICMP_data = create_data()

    seq_num = 1
    time_to_live = 1
    incoming_IP = ""
    if "-q" in arg_dict:
        probe_count = int(arg_dict["-q"])
    else:
        probe_count = 3
    list_for_summary = []
    not_answered_count = 0
    while incoming_IP != dest_ip:
        for x in range(0, probe_count):
            start_time = time.time()
            echo_request(dest_ip, ICMP_data, seq_num, time_to_live)
            try:
                incoming_IP = receive_echo_reply(dest_ip)
                if "-n" not in arg_dict:
                    try:
                        hostname = socket.gethostbyaddr(incoming_IP)[0]
                    except socket.herror:
                        hostname = incoming_IP
                    if x == 0:
                        print(str(time_to_live), end="   ")
                        print(str(hostname) + " (" + str(incoming_IP) + ") ", end="")
                else:
                    if x == 0:
                        print(str(time_to_live), end="   ")
                        print(str(incoming_IP) + " ", end="")
            except socket.timeout:
                if x == 0:
                    print(str(time_to_live), end="   ")
                print("* ", end="") #cuts off rest of probes to this IP address
                not_answered_count = not_answered_count + 1
                continue

            seq_num = seq_num + 1
            duration = find_duration(start_time)
            print(str(duration) + "ms ", end="")

        print("")
        list_for_summary.append([time_to_live, not_answered_count])
        not_answered_count = 0
        time_to_live = time_to_live + 1

    if "-S" in arg_dict:
        print()
        print_summary(list_for_summary)


def print_summary(summary_list):
    print("Summary: ")
    for x in range(0, len(summary_list)):
        print("Hop " + str(summary_list[x][0])+ " probes not answered: " + str(summary_list[x][1]))

def print_help_message():
    print("usage: [nameOfThisFile].py [-h] [-n] [-q Q] [-S] destination")
    print()
    print("options: ")
    print("-h, --help   Show this help message and exit")
    print("-n           Print hop addresses numerically rather than symbolically and numerically")
    print("-q Q         Set the number of probes per `ttl' to nqueries")
    print("-S           Print a summary of how many probes were not answered for each hop")

def main():
    argument_dictionary = parse_args()
    if (("-h" in argument_dictionary["ping"]) or ("--help" in argument_dictionary["ping"])):
        print_help_message()
    else:
        start_traceroute(argument_dictionary)


if __name__ == '__main__':
    main()import socket
import struct
import sys
import time


def parse_args():
    argument_dictionary = {}
    #first argument is always either IP address or website URL
    argument_dictionary["ping"] = sys.argv[1]
    for x in range(2, len(sys.argv)):
        if sys.argv[x] == "-n":
            argument_dictionary["-n"] = "-n"
        if sys.argv[x] == "-q":
            argument_dictionary["-q"] = sys.argv[x+1]
        if sys.argv[x] == "-S":
            argument_dictionary["-S"] = "-S"
        if sys.argv[x] == "-h":
            argument_dictionary["-h"] = "-h"
        if sys.argv[x] == "--help":
            argument_dictionary["--help"] = "--help"
    return argument_dictionary


def return_ip_and_hostname(ip_or_URL, arg_dict):
    if "www" in ip_or_URL: #user entered normal URL
        try:
            hostname = ip_or_URL
            ip_addr = socket.gethostbyname(ip_or_URL)
        except socket.error as e:
            print(e)
    else: #raw IPv4 address
        try:
            ip_addr = ip_or_URL
            hostname = socket.gethostbyaddr(ip_addr)[0]
        except socket.error as e:
            print(e)

    return ip_addr, hostname

def calc_chksum(data_to_convert):
    # length is 20 because BBHHH = 8 bytes, and data_to_send = 12 bytes = 20 bytes total
    if len(data_to_convert) % 2 != 0:
        data_to_convert = data_to_convert + b'\x00'
    # 'H' is a sixteen bit value. But the struct.unpack requires you to add an 'H' or a 'B' for every byte you want to unpack
    # thus you must multiply the 'H' by the len(data)//2 because you want to convert a bunch of 8-bit words into 16 bit words
    # making the total number of 'H' half the original length of data_to_convert
    sixteen_bit_list = struct.unpack('H' * (len(data_to_convert) // 2), data_to_convert)  # ten 16-bit words
    sum = 0
    for x in sixteen_bit_list:
        sum = sum + x #note: this can result in overflow from the 16-bit sum you need
    upper_bits = sum >> 16 #grabs all the large digits
    lower_bits = sum & 0xFFFF #grabs the 16 lower bits
    upper_and_lower = upper_bits + lower_bits #recombines overflow back into sum
    #but recombining the overflow back into the sum can result in overflow again
    #so you must combine overflow back into the sum one more time
    upper_and_lower = upper_and_lower + (upper_and_lower >> 16)
    ones_complement_16_bits = ~upper_and_lower & 0xffff

    #wireshark says the upper and lower bits are in the wrong endianess so we need to flip it
    byte_1 = (ones_complement_16_bits >> 8) & 0x00FF
    byte_2 = (ones_complement_16_bits << 8) & 0xFF00
    reversed_checksum = byte_1 | byte_2
    return reversed_checksum

def create_data():
    data_size = 56 #56 bytes if data size not specified
    data_to_send = b''
    if data_size % 2 == 0:
        add_this_to_data = b'A' #'A' is for even length
    else:
        add_this_to_data = b'B' #'B is for odd length
    for x in range(0, data_size):
        data_to_send = data_to_send + add_this_to_data

    return data_to_send

def echo_request(dest_IP, data_to_send, ICMP_sequence_num, time_to_live):
    # create the raw ICMP socket
    ICMP_socket = socket.socket(socket.AF_INET, socket.SOCK_RAW, socket.IPPROTO_ICMP)
    ICMP_socket.setsockopt(socket.IPPROTO_IP, socket.IP_TTL, time_to_live) #TTL originally 63?

    ICMP_type = 8  # 8 is for echo request (i.e. 1 byte)
    ICMP_code = 0  # all echo requests and replies have code type of zero (i.e. 1 byte)
    initial_checksum = 0 # (i.e. 2 bytes)

    #below is 'rest of header'
    ICMP_identifier = 12345  # identifier allows sender (this program) to know which echo reply came in (i.e. 2 bytes)
    #above is 'rest of header'


    # ! for big endian, first 'B' because "ICMP_type" is 8 bits (and 'B' means 8 bits)
    # ICMP_code is 8 bits, so we use a second 'B'. 'H' is unsigned short (16 bits)
    # thus we use first 'H' for checksum, second 'H' for 16 bit ICMP_identifier
    # and third 'H' for 16-bit icmp_sequence
    ICMP_checksum=calc_chksum(struct.pack('!BBHHH', ICMP_type,ICMP_code,initial_checksum,ICMP_identifier,ICMP_sequence_num)+data_to_send)

    # creates the ICMP packet by concatenating everything together in byte and bytebyte form
    ICMP_packet = struct.pack('!BBHHH', ICMP_type, ICMP_code, ICMP_checksum,ICMP_identifier,ICMP_sequence_num) + data_to_send

    ICMP_socket.sendto(ICMP_packet, (dest_IP, 0))

    ICMP_socket.close()  # closes the connection of the socket

def receive_echo_reply(received_IP):
    ICMP_socket = socket.socket(socket.AF_INET, socket.SOCK_RAW, socket.IPPROTO_ICMP)
    #artificially setting timeout to three seconds
    ICMP_socket.settimeout(3)

    ICMP_packet = ICMP_socket.recv(1024) #the received ICMP packetIdentifier (BE): 12345 (0x3039)
    IP_header = ICMP_packet[:20] #IP header is first 20 bytes
    #inet_ntoa converts 32 bit packed IP address into byte.byte.byte.byte form
    incoming_ip = socket.inet_ntoa(struct.unpack("!4s", IP_header[12:16])[0])
    ICMP_header = ICMP_packet[20:28]
    icmp_type, icmp_code, icmp_checksum, icmp_id, icmp_seq = struct.unpack("bbHHH", ICMP_header)
    # icmp data is wrong endianess so need to flip

    received_data = ICMP_packet[28:]

    ICMP_socket.close()
    return incoming_ip

def find_duration(start_time):
    duration = time.time() - start_time
    duration_ms_decimal = duration * 1000
    split_list = str(duration_ms_decimal).split(".")
    duration_ms_no_decimal = split_list[0] + "." + split_list[1][:3]
    return duration_ms_no_decimal

def print_first_line(dest_ip, hostname, max_hops):
    #sending 64 byte ICMP packets. This is hardcoded
    print("Traceroute to " + str(hostname) + " (" + str(dest_ip) + "), " + str(max_hops) + " hops max, 64 byte packets" )

def start_traceroute(arg_dict):
    max_hops = 30 #hardcoded max hop number
    dest_ip, hostname = return_ip_and_hostname(arg_dict["ping"], arg_dict)
    print_first_line(dest_ip, hostname, max_hops)
    ICMP_data = create_data()

    seq_num = 1
    time_to_live = 1
    incoming_IP = ""
    if "-q" in arg_dict:
        probe_count = int(arg_dict["-q"])
    else:
        probe_count = 3
    list_for_summary = []
    not_answered_count = 0
    while incoming_IP != dest_ip:
        for x in range(0, probe_count):
            start_time = time.time()
            echo_request(dest_ip, ICMP_data, seq_num, time_to_live)
            try:
                incoming_IP = receive_echo_reply(dest_ip)
                if "-n" not in arg_dict:
                    try:
                        hostname = socket.gethostbyaddr(incoming_IP)[0]
                    except socket.herror:
                        hostname = incoming_IP
                    if x == 0:
                        print(str(time_to_live), end="   ")
                        print(str(hostname) + " (" + str(incoming_IP) + ") ", end="")
                else:
                    if x == 0:
                        print(str(time_to_live), end="   ")
                        print(str(incoming_IP) + " ", end="")
            except socket.timeout:
                if x == 0:
                    print(str(time_to_live), end="   ")
                print("* ", end="") #cuts off rest of probes to this IP address
                not_answered_count = not_answered_count + 1
                continue

            seq_num = seq_num + 1
            duration = find_duration(start_time)
            print(str(duration) + "ms ", end="")

        print("")
        list_for_summary.append([time_to_live, not_answered_count])
        not_answered_count = 0
        time_to_live = time_to_live + 1

    if "-S" in arg_dict:
        print()
        print_summary(list_for_summary)


def print_summary(summary_list):
    print("Summary: ")
    for x in range(0, len(summary_list)):
        print("Hop " + str(summary_list[x][0])+ " probes not answered: " + str(summary_list[x][1]))

def print_help_message():
    print("usage: [nameOfThisFile].py [-h] [-n] [-q Q] [-S] destination")
    print()
    print("options: ")
    print("-h, --help   Show this help message and exit")
    print("-n           Print hop addresses numerically rather than symbolically and numerically")
    print("-q Q         Set the number of probes per `ttl' to nqueries")
    print("-S           Print a summary of how many probes were not answered for each hop")

def main():
    argument_dictionary = parse_args()
    if (("-h" in argument_dictionary["ping"]) or ("--help" in argument_dictionary["ping"])):
        print_help_message()
    else:
        start_traceroute(argument_dictionary)


if __name__ == '__main__':
    main()
