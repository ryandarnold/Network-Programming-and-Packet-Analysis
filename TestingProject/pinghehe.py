import socket
import struct
import time


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


def echo_request():
    # create the raw ICMP socket
    ICMP_socket = socket.socket(socket.AF_INET, socket.SOCK_RAW, socket.IPPROTO_ICMP)

    ICMP_type = 8  # 8 is for echo request
    ICMP_code = 0  # all echo requests and replies have code type of zero
    initial_checksum = 0
    ICMP_identifier = 12345  # identifier allows sender (this program) to know which echo reply came in
    ICMP_sequence = 1  # allows sender to match incoming echo replies with previously sent echo requests
    data_to_send = b'Hello, ICMP!'
    # ! for big endian, first 'B' because "ICMP_type" is 8 bits (and 'B' means 8 bits)
    # ICMP_code is 8 bits, so we use a second 'B'. 'H' is unsigned short (16 bits)
    # thus we use first 'H' for checksum, second 'H' for 16 bit ICMP_identifier
    # and third 'H' for 16-bit icmp_sequence
    ICMP_checksum=calc_chksum(struct.pack('!BBHHH', ICMP_type,ICMP_code,initial_checksum,ICMP_identifier,ICMP_sequence)+data_to_send)

    # creates the ICMP packet by concatenating everything together in byte and bytebyte form
    ICMP_packet = struct.pack('!BBHHH', ICMP_type, ICMP_code, ICMP_checksum, ICMP_identifier,ICMP_sequence) + data_to_send
    # for x in range(0, 10):
    #
    # for x in range(0, 500):
    #     ICMP_socket.sendto(ICMP_packet, ("8.8.8.8", 0))  # 8.8.8.8 is google's IPv4 address, 0 is the port number
    #     print("sent ICMP packet")
    #     time.sleep(1)

    ICMP_socket.sendto(ICMP_packet, ("1.1.1.1", 0))
    # ICMP_socket.sendto(ICMP_packet, ("1.1.1.1", 0))
    # ICMP_socket.sendto(ICMP_packet, ("1.1.1.1", 0))
    ICMP_socket.close()  # closes the connection of the socket
    # return ICMP_socket


def echo_reply():
    ICMP_socket = socket.socket(socket.AF_INET, socket.SOCK_RAW, socket.IPPROTO_ICMP)
    #ICMP_socket.setsockopt(socket.IPPROTO_IP, socket.IP_HDRINCL, 1)
    #setsockopt(socket.IPPROTO_IP, socket.IP_HDRINCL, 1)
    ICMP_socket.bind(("127.0.0.1", 3000))
    try:
        print("gets here 8:39pm")
        ICMP_packet = ICMP_socket.recv(1024,0)
        print("hehe")
        print(ICMP_packet)
    except socket.error as error:
        print(error)
    finally:
        ICMP_socket.close()
    # ICMP header is 8 bytes
    # print(ICMP_packet)


def main():
    echo_request()

    echo_reply()


if __name__ == '__main__':
    main()