"""
file: route.py
description: remakes the 'route' command used in the linux terminal
"""

import sys

def parse_current_line(current_line) -> list:
    current_line_no_newline = current_line.replace("\n", "")
    current_line_no_trailing_space = current_line_no_newline.strip()
    curr_line_no_spaces = current_line_no_trailing_space.replace(" ", "")
    curr_line_no_double_tabs = curr_line_no_spaces.replace("\t\t", "\t")
    current_line_list = curr_line_no_double_tabs.split("\t")
    return current_line_list

def parse_hex_into_IP(number_to_transform) -> str:
    #transforms the given /proc/net/route data into actual 'route' command look
    first_byte = str(int(number_to_transform[6:8], 16))
    second_byte = str(int(number_to_transform[4:6], 16))
    third_byte = str(int(number_to_transform[2:4], 16))
    fourth_byte = str(int(number_to_transform[0:2], 16))
    IP_to_return = first_byte + "." + second_byte + "." + third_byte + "." + fourth_byte + " "
    return IP_to_return

def get_destination_IP(IP_to_parse):
    if IP_to_parse == "00000000":
        return "default "
    elif IP_to_parse == "0000FEA9":
        return "link-local "
    else:
        destination_IP = parse_hex_into_IP(IP_to_parse)
        return destination_IP

def get_gateway_IP(IP_to_parse):
    if IP_to_parse == "0202000A":
        return "_gateway "
    else:
        IP_to_print = parse_hex_into_IP(IP_to_parse)
        return IP_to_print

def get_flags(flags: str):
    if flags == "0003":
        return "UG"
    elif flags == "0002":
        return "G"
    elif flags == "0001":
        return "U"

def get_current_line_info(line_list):
    print_this_line = ""
    # get destination IP
    destination_IP = get_destination_IP(line_list[1])
    print_this_line = print_this_line + destination_IP

    # get gateway IP
    gateway_IP = get_gateway_IP(line_list[2])
    print_this_line = print_this_line + gateway_IP

    # get genmask IP
    genMask_IP = parse_hex_into_IP(line_list[7])
    print_this_line = print_this_line + genMask_IP

    # get flags
    flags = get_flags(line_list[3])
    print_this_line = print_this_line + flags + " "

    # get metric
    metric = line_list[6]
    print_this_line = print_this_line + metric + " "

    # get ref
    ref = line_list[4]
    print_this_line = print_this_line + ref + " "

    # get use
    use = line_list[5]
    print_this_line = print_this_line + use + " "

    # get interface/iface
    interface = line_list[0]
    print_this_line = print_this_line + interface + " "
    return print_this_line


def pretty_print(line_to_print):
    #prints the output of this 'route.py' file in the same way that actual 'route' command does
    #in other words it just formats the output for easy user reading
    print_this_line = ""
    D_to_G_to_G_to_F = 18 # spaces between 'destination', 'gateway', 'Genmask', and 'Flags'
    F_to_M_to_R = 9 # spaces between 'flag', 'metric' and 'ref'
    U_to_I = 8 #spaces between 'use' and 'Iface'
    line_list = line_to_print.split(" ")

    #makes column printing for destination, gateway and genmask
    for index in range(0, 3):
        print_this_line = print_this_line + str(line_list[index])
        current_thing_length = len(line_list[index])
        spaces_to_add = D_to_G_to_G_to_F - current_thing_length
        for x in range(0, spaces_to_add):
            print_this_line = print_this_line + " "

    #makes column printing for flags, metric and ref
    for index in range(3, 6):
        print_this_line = print_this_line + str(line_list[index])
        current_thing_length = len(line_list[index])
        spaces_to_add = F_to_M_to_R - current_thing_length
        for x in range(0, spaces_to_add):
            print_this_line = print_this_line + " "
    #makes column printing for use and Iface
    for index in range(6, 8):
        print_this_line = print_this_line + str(line_list[index])
        current_thing_length = len(line_list[index])
        spaces_to_add = U_to_I - current_thing_length
        for x in range(0, spaces_to_add):
            print_this_line = print_this_line + " "
    print(print_this_line)


def start_printing_route(location_of_route: str):
    print("Kernel IP routing table")
    print("Destination       Gateway           Genmask           Flags    Metric   Ref      Use     Iface")
    with open(location_of_route, 'r') as file:
        next(file) # skips the first line
        for current_line in file: #this starts at the second line
            line_list = parse_current_line(current_line)
            print_this_line = get_current_line_info(line_list)
            pretty_print(print_this_line)


def main():
    if len(sys.argv) == 1:
        start_printing_route("/proc/net/route")
    elif len(sys.argv) == 2:
        start_printing_route(sys.argv[1])
    else:
        print("Too many arguments!")



if __name__ == '__main__':
    main()