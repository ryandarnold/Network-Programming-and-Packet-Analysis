import scapy.utils
from scapy.all import *
from scapy.layers.inet import IP, ICMP, UDP, TCP
from scapy.layers.l2 import Ether
import sys
import socket

def parse_args():
    argument_dictionary = {}
    for x in range(len(sys.argv)):
        if sys.argv[x] == "-r":
            argument_dictionary["-r"] = sys.argv[x+1]
        if sys.argv[x] == "-host":
            argument_dictionary["-host"] = sys.argv[x+1]
        if sys.argv[x] == "-port":
            argument_dictionary["-port"] = sys.argv[x+1]
        if sys.argv[x] == "-ip":
            argument_dictionary["-ip"] = sys.argv[x]
        if sys.argv[x] == "-tcp":
            argument_dictionary["-tcp"] = sys.argv[x]
        if sys.argv[x] == "-udp":
            argument_dictionary["-udp"] = sys.argv[x]
        if sys.argv[x] == "-icmp":
            argument_dictionary["-icmp"] = sys.argv[x]
        if sys.argv[x] == "-net":
            argument_dictionary["-net"] = sys.argv[x+1]
        if sys.argv[x] == "-c":
            argument_dictionary["-c"] = sys.argv[x+1]

    packet_list = scapy.utils.rdpcap(argument_dictionary["-r"])
    return argument_dictionary, packet_list

def parse_ethernet_packet(packet, arg_dict):
    # 34525 = 0x86DD = IPv6;;; 2048 = 0x800 = IPv4
    if (((len(arg_dict) == 1) or ("-c" in arg_dict.keys())) and ("-tcp" not in arg_dict.keys())
          and ("-udp" not in arg_dict.keys()) and ("-icmp" not in arg_dict.keys()) and ("-ip" not in arg_dict.keys())
            and ("-net" not in arg_dict.keys())):
        ether = "ETHER: "
        print(ether + " ----- Ether Header -----")
        print(ether)
        print(ether + "Packet size = " + str(len(packet)) + " bytes")
        print(ether + "Destination = " + str(packet.dst))
        print(ether + "Source = " + str(packet.src))
        type_to_print = ""
        if packet.type == 34525:
            type_to_print = "86DD"
        elif packet.type == 2048:
            type_to_print = "0800"
        print(ether + "Ethertype = " + type_to_print + " (IP)")
        print(ether)


def get_DSCP_bits(DSCP_value: int) -> list[int]:
    bit0 = DSCP_value & 1
    bit1 = (DSCP_value >> 1) & 1
    bit2 = (DSCP_value >> 2) & 1
    bit3 = (DSCP_value >> 3) & 1
    bit4 = (DSCP_value >> 4) & 1
    bit5 = (DSCP_value >> 5) & 1
    bit6 = (DSCP_value >> 6) & 1
    bit7 = (DSCP_value >> 7) & 1
    list_to_return = [bit7, bit6, bit5, bit4, bit3, bit2, bit1, bit0]
    return list_to_return

def get_IP_bits(flag_value: int) -> list[int]:
    #note: bit0 is reserved and must be zero
    bit1 = (flag_value >> 1) & 1
    bit2 = (flag_value >> 2) & 1
    list_to_return = [bit2, bit1, 0]
    return list_to_return

def get_IP_flag(packet):
    ip = "IP: "
    flag_value = packet.flags.value  # is the correct flag value
    hex_value = "0x" + format(flag_value, '01x')
    print(ip + "Flags = " + hex_value)
    list_of_bits = get_IP_bits(flag_value)
    print(ip + "   ." + str(list_of_bits[2]) + ".. .... = ", end="")
    if list_of_bits[2] == 1:
        print("do not fragment")
    if list_of_bits[2] == 0:
        print("can fragment")
    print(ip + "   .." + str(list_of_bits[1]) + ". .... = ", end="")
    if list_of_bits[1] == 1:
        print("not last fragment")
    if list_of_bits[1] == 0:
        print("last fragment")

def find_IP_protocol(packet):
    ip = "IP: "
    print(ip + "Protocol = ", end="")
    if packet.proto == 6:
        print("6 (TCP)")
    if packet.proto == 17:
        print("17 (UDP)")
    if packet.proto == 1:
        print("1 (ICMP)")

def find_IP_source_and_dest_addr(packet):
    ip = "IP: "
    print(ip + "Source address = " + str(packet.src) +", ", end="")
    try:
        host_name = socket.gethostbyaddr(str(packet.src))[0]
        print(host_name)
    except:
        print("(hostname unknown)")

    print(ip + "Destination address = " + str(packet.dst) + ", ", end="")
    try:
        host_name = socket.gethostbyaddr(str(packet.dst))[0]
        print(host_name)
    except:
        print("(hostname unknown)")

def find_IP_options(packet):
    ip = "IP: "
    if packet.options:
        print(ip + "Has options")
    else:
        print(ip + "No options")

def print_IP_packet(packet):
    ip = "IP: "
    print(ip + " ----- IP Header -----")
    print(ip)
    print(ip + "Version = " + str(packet.version))
    # ihl is internet header length
    length_of_IPvFour = 32  # 32 bits is IPv4 length
    num_of_bits_in_one_bite = 8  # eight bits in one byte
    header_length_bytes = packet.ihl * length_of_IPvFour // num_of_bits_in_one_bite
    print(ip + "Header length = " + str(header_length_bytes) + " bytes")
    hex_value = "0x" + format(packet.tos, '02x')  # hex(packet.tos)
    print(ip + "Type of service = " + hex_value)

    list_of_bits = get_DSCP_bits(packet.tos)
    print(ip + "   xxx. .... = 0 (precedence)")
    print(ip + "   ..." + str(list_of_bits[3]) + " ...." + " = normal delay")
    print(ip + "   .... " + str(list_of_bits[4]) + "..." + " = normal throughput")
    print(ip + "   .... ." + str(list_of_bits[5]) + ".." + " = normal reliability")

    print(ip + "Total length = " + str(len(packet)) + " bytes")
    print(ip + "Identification = " + str(packet.id))
    get_IP_flag(packet)
    print(ip + "Fragment offset = " + str(packet.frag * 8) + " bytes")  # * 8 because its in bits
    print(ip + "Time to live = " + str(packet.ttl) + " seconds/hops")
    find_IP_protocol(packet)
    print(ip + "Header checksum = " + str(hex(packet.chksum)))
    find_IP_source_and_dest_addr(packet)
    find_IP_options(packet)
    print(ip)

def check_all_zeros(arg_dict) -> bool:
    z_or_zp = re.fullmatch("0[\.]?", arg_dict["-net"]) #"0" or "0."
    if z_or_zp is not None:
        return True
    zpz_or_zpzp  = re.fullmatch("0\.0[\.]?", arg_dict["-net"]) # "0.0" or "0.0."
    if zpz_or_zpzp is not None:
        return True
    zpzpz_or_zpzpzp = re.fullmatch("0\.0\.0[\.]?", arg_dict["-net"]) # "0.0.0" or "0.0.0."
    if zpzpz_or_zpzpzp is not None:
        return True
    zpzpzpz =  re.fullmatch("0\.0\.0\.0", arg_dict["-net"]) #only 0.0.0.0
    if zpzpzpz is not None:
        return True
    return False # not all zeros, so need to look for actual address in all of IP packets


def find_IP_to_print(packet, address: str):
    if "." not in address:
        #i.e. "123"
        if (packet.src[0:len(address)] == address) or (packet.dst[0:len(address)] == address):
            print_IP_packet(packet)
    if "." in address:
        #i.e. "123." or "123.0" or "123.0.54" or "123.5.6.7"
        list_of_bytes = address.split(".")
        if (len(list_of_bytes) == 2) and (list_of_bytes[1] == ""):
            #i.e. "123."
            if (packet.src[0:len(address)] == address) or (packet.dst[0:len(address)] == address):
                print_IP_packet(packet)
                return
        if ((len(list_of_bytes) == 2) and (list_of_bytes[1] != "")) or ((len(list_of_bytes)==3) and (list_of_bytes[2] == "")):
            #i.e. "123.54" or "123.54."
            if (packet.src[0:len(address)] == address) or (packet.dst[0:len(address)] == address):
                print_IP_packet(packet)
                return
        if ((len(list_of_bytes) == 3) and (list_of_bytes[2] != "")) or ((len(list_of_bytes)==4) and (list_of_bytes[3] == "")):
            #i.e. "123.21.125" or "123.21.125."
            if (packet.src[0:len(address)] == address) or (packet.dst[0:len(address)] == address):
                print_IP_packet(packet)
                return
        if (len(list_of_bytes) == 4) and (list_of_bytes[3] != ""):
            #i.e. "123.21.125.70"
            if (packet.src[0:len(address)] == address) or (packet.dst[0:len(address)] == address):
                print_IP_packet(packet)
                return


def find_net_command(packet, arg_dict):
    all_zeros = check_all_zeros(arg_dict)
    if all_zeros == True:
        print_IP_packet(packet)
        return
    find_IP_to_print(packet, arg_dict["-net"])


def parse_IP_packet(packet, arg_dict):
    if "-host" in arg_dict.keys():
        if (packet.src == arg_dict["-host"]) or (packet.dst == arg_dict["-host"]):
            print_IP_packet(packet)
    elif "-ip" in arg_dict.keys():
        print_IP_packet(packet)
    elif "-net" in arg_dict.keys():
        find_net_command(packet, arg_dict)
    elif (((len(arg_dict) == 1) or ("-c" in arg_dict.keys())) and ("-tcp" not in arg_dict.keys())
          and ("-udp" not in arg_dict.keys()) and ("-icmp" not in arg_dict.keys())):
        print_IP_packet(packet)

def find_ICMP_type(packet):
    icmp = "ICMP: "
    print(icmp + "Type = " + str(packet.type), end="")
    if packet.type == 0:
        print(" (Echo reply)")
    elif packet.type == 3:
        print(" (Destination Unreachable)")
    elif packet.type == 5:
        print(" (Redirect Message)")
    elif packet.type == 8:
        print(" (Echo request)")
    elif packet.type == 9:
        print(" (Router Advertisement)")
    elif packet.type == 10:
        print(" (Router solicitation")
    elif packet.type == 11:
        print(" (Time exceeded")
    elif packet.type == 12:
        print(" (Parameter Problem: Bad IP header)")
    elif packet.type == 13:
        print(" (Timestamp)")
    elif packet.type == 14:
        print(" (Timestamp reply)")
    elif packet.type == 42:
        print(" (Extended Echo Request)")
    elif packet.type == 43:
        print(" (Extended Echo Reply)")
    else:
        print("unassigned/deprecated/unassigned/reserved/experimental")

def print_ICMP_packet(packet):
    icmp = "ICMP: "
    print(icmp + "----- ICMP Header -----")
    print(icmp)
    find_ICMP_type(packet)
    print(icmp + "Code = " + str(packet.code))
    print(icmp + "Checksum = " + str(hex(packet.chksum)))
    print(icmp)

def parse_ICMP_packet(packet, arg_dict):
    if "-icmp" in arg_dict.keys():
        print_ICMP_packet(packet)
    elif (((len(arg_dict) == 1) or ("-c" in arg_dict.keys())) and ("-tcp" not in arg_dict.keys())
            and ("-udp" not in arg_dict.keys()) and ("-ip" not in arg_dict.keys())
                and ("-net" not in arg_dict.keys())):
        print_ICMP_packet(packet)

def print_UDP_packet(packet):
    udp = "UDP: "
    print(udp + "----- UDP Header -----")
    print(udp + "Source port = " + str(packet.sport))
    print(udp + "Destination port = " + str(packet.dport))
    print(udp + "Length = " + str(packet.len))
    print(udp + "Checksum = " + str(hex(packet.chksum)))

def parse_UDP_packet(packet, arg_dict):
    if "-port" in arg_dict.keys():
        if (packet.sport == int(arg_dict["-port"])) or (packet.dport == int(arg_dict["-port"])):
            # now to only print UDP packets that have the specific port number
            print_UDP_packet(packet)
    elif "-udp" in arg_dict.keys():
        print_UDP_packet(packet)
    elif (((len(arg_dict) == 1) or ("-c" in arg_dict.keys())) and ("-tcp" not in arg_dict.keys())
            and ("-icmp" not in arg_dict.keys()) and ("-ip" not in arg_dict.keys())
                and ("-net" not in arg_dict.keys())):
        #now only print if there is only the "-read" argument
        #if there are any arguments other than "-read: and no "-port" command, then don't print anything
        print_UDP_packet(packet)

def find_TCP_data_offset(packet):
    tcp = "TCP: "
    #need to multiply packet.dataofs by 4 because it is measured in 32-bit chunks
    print(tcp + "Data offset = " + str(packet.dataofs*4) + " bytes")

def get_TCP_flag(TCP_value):
    bit0 = TCP_value & 1
    bit1 = (TCP_value >> 1) & 1
    bit2 = (TCP_value >> 2) & 1
    bit3 = (TCP_value >> 3) & 1
    bit4 = (TCP_value >> 4) & 1
    bit5 = (TCP_value >> 5) & 1
    bit6 = (TCP_value >> 6) & 1
    bit7 = (TCP_value >> 7) & 1
    list_to_return = [bit7, bit6, bit5, bit4, bit3, bit2, bit1, bit0]
    return list_to_return

def find_TCP_flags(packet):
    #NOTE: FIN flag is the most significant bit, and CWR is the LSB
    tcp = "TCP: "
    print(tcp + "flags = " +str(hex(packet.flags.value)))
    list_of_bits = get_TCP_flag(packet.flags.value)
    if list_of_bits[7] == 1:
        print(tcp + "   1... .... = Congestion Window Reduced: Set")
    elif list_of_bits[7] == 0:
        print(tcp + "   0.... .... = Congestion Window Reduced: Not Set")
    if list_of_bits[6] == 1:
        print(tcp + "   .1.. .... = ECN-Echo: Set")
    elif list_of_bits[6] == 0:
        print(tcp + "   .0.. .... = ECN-Echo: Not Set")
    if list_of_bits[5] == 1:
        print(tcp + "   ..1. .... = Urgent Pointer: Set")
    elif list_of_bits[5] == 0:
        print(tcp + "   ..0. .... = Urgent Pointer: Not Set")
    if list_of_bits[4] == 1:
        print(tcp + "   ...1 .... = Acknowledgement: Set")
    elif list_of_bits[4] == 0:
        print(tcp + "   ...0 .... = Acknowledgement: Not Set")
    if list_of_bits[3] == 1:
        print(tcp + "   .... 1... = Push: Set")
    elif list_of_bits[3] == 0:
        print(tcp + "   .... 0... = Push: Not Set")
    if list_of_bits[2] == 1:
        print(tcp + "   .... .1.. = Reset: Set")
    elif list_of_bits[2] == 0:
        print(tcp + "   .... .0.. = Reset: Not Set")
    if list_of_bits[1] == 1:
        print(tcp + "   .... ..1. = Sync: Set")
    elif list_of_bits[1] == 0:
        print(tcp + "   .... ..0. = Sync: Not Set")
    if list_of_bits[0] == 1:
        print(tcp + "   .... ...1 = Finished: Set")
    elif list_of_bits[0] == 0:
        print(tcp + "   .... ...0 = Finished: Not Set")

def find_TCP_options(packet):
    tcp = "TCP: "
    if packet.options:
        print(tcp + "Has options: ", end="")
        print(tcp + str(packet.options))
    else:
        print(tcp + "No options")

def print_TCP_packet(packet):
    tcp = "TCP: "
    print(tcp + "----- TCP Header -----")
    print(tcp + "Source port = " + str(packet.sport))
    print(tcp + "Destination port = " + str(packet.dport))
    print(tcp + "Sequence number = " + str(packet.seq))
    print(tcp + "Acknowledgement number = " + str(packet.ack))
    find_TCP_data_offset(packet)
    find_TCP_flags(packet)
    print(tcp + "Window = " + str(packet.window))
    print(tcp + "Checksum = " + str(hex(packet.chksum)))
    print(tcp + "Urgent Pointer = " + str(packet.urgptr))
    find_TCP_options(packet)

def parse_TCP_packet(packet, arg_dict):
    if "-port" in arg_dict.keys():
        if (packet.sport == int(arg_dict["-port"])) or (packet.dport == int(arg_dict["-port"])):
            print_TCP_packet(packet)
    elif "-tcp" in arg_dict.keys():
        print_TCP_packet(packet)
    elif (((len(arg_dict) == 1) or ("-c" in arg_dict.keys())) and ("-udp" not in arg_dict.keys())
          and ("-icmp" not in arg_dict.keys()) and ("-ip" not in arg_dict.keys())
            and ("-net" not in arg_dict.keys())):
        print_TCP_packet(packet)

def parsePacketCaptureFile(packet_list, arg_dict):
    packet_num = 0
    num_to_print = -1
    print_all_packets = True
    if "-c" in arg_dict.keys():
        print_all_packets = False
        num_to_print = int(arg_dict["-c"])

    for packet in packet_list:
        if (print_all_packets == False) and (packet_num == num_to_print):
            return
        packet_num = packet_num + 1
        print("packet number " + str(packet_num) + ":")  # just for convenience
        if Ether in packet:
            parse_ethernet_packet(packet, arg_dict)
        if IP in packet:
            ip_packet = packet.getlayer(1)
            parse_IP_packet(ip_packet, arg_dict)
        if ICMP in packet:
            ICMP_packet = packet.getlayer(2)
            parse_ICMP_packet(ICMP_packet, arg_dict)
        elif UDP in packet:
            UDP_packet = packet.getlayer(2)
            parse_UDP_packet(UDP_packet, arg_dict)
        elif TCP in packet:
            TCP_packet = packet.getlayer(2)
            parse_TCP_packet(TCP_packet, arg_dict)

        print() #adds space between ethernet packets


def main():
    argument_dictionary, packet_list = parse_args()

    parsePacketCaptureFile(packet_list, argument_dictionary)



if __name__ == '__main__':
    main()