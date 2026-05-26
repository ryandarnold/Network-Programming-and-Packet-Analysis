import socket
import struct
import sys
import time
import statistics
import signal



def parse_args():
    argument_dictionary = {}
    #first argument is always either IP address or website URL
    argument_dictionary["ping"] = sys.argv[1]
    for x in range(2, len(sys.argv)):
        if sys.argv[x] == "-c":
            argument_dictionary["-c"] = sys.argv[x+1]
        if sys.argv[x] == "-i":
            argument_dictionary["-i"] = sys.argv[x+1]
        if sys.argv[x] == "-s":
            argument_dictionary["-s"] = sys.argv[x+1]
        if sys.argv[x] == "-t":
            argument_dictionary["-t"] = sys.argv[x+1]
        if sys.argv[x] == "-h":
            argument_dictionary["-h"] = "-h"
        if sys.argv[x] == "--help":
            argument_dictionary["--help"] = "--help"
    return argument_dictionary

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

    # Convert checksum to network byte order (big endian)
    byte_1 = (ones_complement_16_bits >> 8) & 0x00FF
    byte_2 = (ones_complement_16_bits << 8) & 0xFF00
    reversed_checksum = byte_1 | byte_2
    return reversed_checksum

def print_first_line(ip_or_URL, arg_dict):
    if "www" in ip_or_URL: #user entered normal URL
        try:
            URL = ip_or_URL
            ip_addr = socket.gethostbyname(ip_or_URL)
            print("PING " + str(URL) + " " + "(" + str(ip_addr) + ")", end="")
        except socket.error as e:
            print(e)
    else: #raw IPv4 address
        try:
            ip_addr = ip_or_URL
            hostname = socket.gethostbyaddr(ip_addr)[0]
            print("PING " + str(ip_addr) + " " + "(" + str(ip_addr) + ") ", end="")
        except socket.error as e:
            print(e)

    if "-s" in arg_dict:
        size_of_header = 8 #8 bytes
        size_of_data = int(arg_dict["-s"])
        size_of_data_plus_header = size_of_data + size_of_header
        print(str(size_of_data) + "(" + str(size_of_data_plus_header) + ") bytes of data." )
    else: #standard ICMP packet size is 56 bytes of data and 64 bytes in total
        print("56(64) bytes of data")
    return ip_addr

def echo_request(dest_IP, data_to_send, ICMP_sequence_num):
    # create the raw ICMP socket
    ICMP_socket = socket.socket(socket.AF_INET, socket.SOCK_RAW, socket.IPPROTO_ICMP)
    ICMP_socket.setsockopt(socket.IPPROTO_IP, socket.IP_TTL, 63) #TTL originally 63?

    ICMP_type = 8  # 8 is for echo request (i.e. 1 byte)
    ICMP_code = 0  # all echo requests and replies have code type of zero (i.e. 1 byte)
    initial_checksum = 0 # (i.e. 2 bytes)

    #below is 'rest of header'
    ICMP_identifier = 12345  # identifier allows sender (this program) to know which echo reply came in (i.e. 2 bytes)
    #ICMP_sequence = 2  # allows sender to match incoming echo replies with previously sent echo requests (i.e 2 bytes)
    #above is 'rest of header'


    # ! for big endian, first 'B' because "ICMP_type" is 8 bits (and 'B' means 8 bits)
    # ICMP_code is 8 bits, so we use a second 'B'. 'H' is unsigned short (16 bits)
    # thus we use first 'H' for checksum, second 'H' for 16 bit ICMP_identifier
    # and third 'H' for 16-bit icmp_sequence
    ICMP_checksum=calc_chksum(struct.pack('!BBHHH', ICMP_type,ICMP_code,initial_checksum,ICMP_identifier,ICMP_sequence_num)+data_to_send)
    #print("ICMP checksum: " + str(ICMP_checksum))
    # creates the ICMP packet by concatenating everything together in byte and bytebyte form
    ICMP_packet = struct.pack('!BBHHH', ICMP_type, ICMP_code, ICMP_checksum,ICMP_identifier,ICMP_sequence_num) + data_to_send
    #print("size of icmp packet " + str(len(ICMP_packet)))
    #print("sent ICMP packet: " + str(ICMP_packet))

    start_time = time.time()
    ICMP_socket.sendto(ICMP_packet, (dest_IP, 0))

    #print("after sent ICMP packet: " + str(ICMP_packet))
    ICMP_socket.close()  # closes the connection of the socket
    return start_time

def reverse_endianess(data_to_reverse):
    byte_1 = (data_to_reverse >> 8) & 0x00FF
    byte_2 = (data_to_reverse << 8) & 0xFF00
    reversed_data = byte_1 | byte_2  # correct
    return reversed_data

def receive_echo_reply(received_IP, start_time):
    received_packet = False
    ICMP_socket = socket.socket(socket.AF_INET, socket.SOCK_RAW, socket.IPPROTO_ICMP)
    try:
        ICMP_packet = ICMP_socket.recv(1024,0) #the received ICMP packetIdentifier (BE): 12345 (0x3039)

        duration_time = (time.time() - start_time) * 1000
        duration_time_string = str(duration_time)
        split_list = duration_time_string.split(".")
        concatenated_time = split_list[0] + "." + split_list[1][0]

        received_packet = True

        ICMP_header = ICMP_packet[20:28]
        icmp_type, icmp_code, icmp_checksum, icmp_id, icmp_seq = struct.unpack("bbHHH", ICMP_header)
        # icmp data is wrong endianess so need to flip
        real_icmp_seq = reverse_endianess(icmp_seq)
        ttl = struct.unpack("B", ICMP_packet[8:9])[0] #extracts the time to live from IP encasing

        # 20 bytes come from ethernet and IP packet enclosings, so must subtract ICMP_packet length by 20 bytes
        print(str(len(ICMP_packet) - 20) + " bytes from " + str(received_IP) + ": ", end="")
        print("icmp_seq=" + str(real_icmp_seq) + " ", end="")
        print("ttl=" + str(ttl) + " ", end="")
        print("time=" + str(concatenated_time) + " ms")
        ICMP_socket.close()
        return received_packet, duration_time
    except socket.error as error:
        duration_time = (time.time() - start_time) * 1000
        print(error)
        return received_packet, duration_time
    except KeyboardInterrupt:

        raise KeyboardInterrupt



def create_data(arg_dict):
    if "-s" in arg_dict:
        data_size = int(arg_dict["-s"]) #data size in bytes
    else:
        data_size = 56 #56 bytes if data size not specified
    data_to_send = b''
    if data_size % 2 == 0:
        add_this_to_data = b'A' #'A' is for even length
    else:
        add_this_to_data = b'B' #'B is for odd length
    for x in range(0, data_size):
        data_to_send = data_to_send + add_this_to_data

    return data_to_send

def find_overall_duration(overall_start_time) -> str:
    duration = time.time() - overall_start_time
    return duration

def timeout_handler(signum, frame):
    raise TimeoutError("Timeout occurred")

def start_ping(arg_dict, timeout_occurs, timeout_sec):
    if timeout_occurs == True:
        start_time_test = time.time()
        signal.signal(signal.SIGALRM, timeout_handler)  # timeout_handler throws the custom exception
        signal.setitimer(signal.ITIMER_REAL, timeout_sec)


    if "-i" in arg_dict:
        wait_time = int(arg_dict["-i"]) #wait for user specified number of seconds
    else:
        wait_time = 1 #1 second is default

    dest_ip = print_first_line(arg_dict["ping"], arg_dict)
    ICMP_data = create_data(arg_dict)
    if "-c" in arg_dict:
        count = int(arg_dict["-c"])
    else:
        count = - 1
    try:
        if count != -1:  # only send and receive up to 'count' times since user specified it
            total_received = 0
            overall_start_time = time.time()
            list_of_duration_times = []
            for seq_num in range(1, count + 1):

                start_time = echo_request(dest_ip, ICMP_data, seq_num)
                received_packet, icmp_duration = receive_echo_reply(dest_ip, start_time)
                list_of_duration_times.append(icmp_duration)
                if received_packet == True:
                    total_received = total_received + 1
                time.sleep(wait_time)
            overall_duration = find_overall_duration(overall_start_time)

            find_and_print_ICMP_statistics(dest_ip, count, total_received, overall_duration, list_of_duration_times)
        elif count == -1:
            # this continuously sends ICMP requests (and receives replies) until the user executes a keyboard interrupt
            total_received = 0
            overall_start_time = time.time()
            list_of_duration_times = []
            seq_num = 1
            count = 0
            try:
                while True:
                    start_time = echo_request(dest_ip, ICMP_data, seq_num)
                    count = count + 1
                    received_packet, icmp_duration = receive_echo_reply(dest_ip, start_time)
                    list_of_duration_times.append(icmp_duration)
                    if received_packet == True:
                        total_received = total_received + 1
                    seq_num = seq_num + 1
                    time.sleep(wait_time)
            except KeyboardInterrupt:
                overall_duration = find_overall_duration(overall_start_time)
            except TimeoutError:
                overall_duration = find_overall_duration(overall_start_time)
                find_and_print_ICMP_statistics(dest_ip, count, total_received, overall_duration, list_of_duration_times)
                duration = time.time() - start_time_test
                print("duration: " + str(duration))
                return
                # raise TimeoutError
            find_and_print_ICMP_statistics(dest_ip, count, total_received, overall_duration, list_of_duration_times)
    except TimeoutError:
        overall_duration = find_overall_duration(overall_start_time)
        find_and_print_ICMP_statistics(dest_ip, count, total_received, overall_duration, list_of_duration_times)
        return


def find_rtt_min(list_of_times):
    smallest = list_of_times[0]
    for x in list_of_times:
        if x < smallest:
            smallest = x
    smallest_string = str(smallest)
    split_list = smallest_string.split(".")
    string_official_smallest = split_list[0] + "." + split_list[1][:3]
    return float(string_official_smallest)

def find_rtt_avg(list_of_times):
    size = len(list_of_times)
    total_time = 0
    for x in list_of_times:
        total_time = total_time + x
    average_time = total_time / size
    average_time_string = str(average_time)
    split_list = average_time_string.split(".")
    string_official_average = split_list[0] + "." + split_list[1][:3]
    return float(string_official_average)

def find_rtt_max(list_of_times):
    biggest = list_of_times[0]
    for x in list_of_times:
        if x > biggest:
            biggest = x
    biggest_string = str(biggest)
    split_list = biggest_string.split(".")
    string_official_biggest = split_list[0] + "." + split_list[1][:3]
    return float(string_official_biggest)

def find_mdev(list_of_times):
    std_dev = statistics.stdev(list_of_times)
    std_dev_string = str(std_dev)
    split_list = std_dev_string.split(".")
    string_official_std_dev = split_list[0] + "." + split_list[1][:3]
    return float(string_official_std_dev)

def find_and_print_ICMP_statistics(dest_ip, total_sent, total_received, overall_duration, list_of_times):
    loss_decimal = total_received / total_sent

    loss_percentage = (1 - loss_decimal) * 100
    split_thing = str(loss_percentage).split(".")
    loss_percentage_no_decimal = split_thing[0]

    duration_ms_decimal = overall_duration * 1000
    split_list = str(duration_ms_decimal).split(".")
    duration_ms_no_decimal = split_list[0]

    rtt_min = find_rtt_min(list_of_times)
    rtt_avg = find_rtt_avg(list_of_times)
    rtt_max = find_rtt_max(list_of_times)
    mdev = find_mdev(list_of_times)
    print("--- " + str(dest_ip) + " ping statistics ---")
    print(str(total_sent) + " packets transmitted, ", end="")
    print(str(total_received) + " received, ", end="")
    print(str(loss_percentage_no_decimal) + "% packet loss, ", end="")
    print("time " + str(duration_ms_no_decimal) + "ms")
    print("rtt min/avg/max/mdev = ", end="")
    print(str(rtt_min) + "/" + str(rtt_avg) + "/" + str(rtt_max) + "/" + str(mdev) )

def print_help_message():
    print("usage: [nameOfThisFile].py [-h] [-s S] [-c C] [-i I] [-t T] destination")
    print()
    print("positional arguments: ")
    print("  destination target host address")
    print()
    print("options: " )
    print("-h, --help   show this help message and exit")
    print("-s S         packet size")
    print("-c C         number of times packets should be sent")
    print("-i I         wait time between successive pings")
    print("-t T         timeout in seconds after which program terminates")

def main():
    #maximum data size you can do is 68 bytes
    #i.e. you can only do up to "-s 68" otherwise it stops working
    argument_dictionary = parse_args()
    if ("-h" in argument_dictionary) or ("--help" in argument_dictionary):
        print_help_message()
    else:
        if "-t" in argument_dictionary:
            timeout_sec = int(argument_dictionary["-t"])
        else:
            timeout_sec = -1

        if timeout_sec == -1:
            timeout_occurs = False
            start_ping(argument_dictionary, timeout_occurs, timeout_sec) #no timeout; fully dependent on count and keyboard interrupt to stop program
        else:

            timeout_occurs = True

            start_ping(argument_dictionary, timeout_occurs, timeout_sec)





if __name__ == '__main__':
    main()
