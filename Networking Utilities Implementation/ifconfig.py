import psutil
import netifaces


def findMTU(net_list: list):
    #MTU is 3rd index
    MTU_value = net_list[3]
    print("mtu " + str(MTU_value))

def printLineOne(current_interface:str, new_dict: dict):
    #UP = 0x1, LOOPBACK = 0X8, BROADCAST = 0x2, RUNNING = 0x40, MULTICAST = 0x1000
    UP = 1 #0x1
    LOOPBACK = 8 #0x8
    BROADCAST = 2 #0x2
    RUNNING = 64 #0x40
    MULTICAST = 4096 #0x1000
    print(current_interface + ": flags=", end="")
    net_list = list(new_dict[current_interface])
    sum = 0
    flag_string = ""
    if "up" in net_list[4]:
        sum = sum + UP
        flag_string = flag_string + "UP"
    if "loopback" in net_list[4]:
        sum = sum + LOOPBACK
        flag_string = flag_string + ",LOOPBACK"
    if "broadcast" in net_list[4]:
        sum = sum + BROADCAST
        flag_string = flag_string + ",BROADCAST"
    if "running" in net_list[4]:
        sum = sum + RUNNING
        flag_string = flag_string + ",RUNNING"
    if "multicast" in net_list[4]:
        sum = sum + MULTICAST
        flag_string = flag_string + ",MULTICAST"
    print(str(sum) + "<" + flag_string + ">" + " " ,end="")
    findMTU(net_list)

def printLineTwo(current_interface: str):
    # [2] has network interface, broadcast and netmask address
    addresses = netifaces.ifaddresses(current_interface)[2]
    addresses_list = str(addresses)
    addresses_list = addresses_list.replace("[{", "")
    addresses_list = addresses_list.replace("}]", "")
    addresses_list = addresses_list.replace("'", "")
    addresses_list = addresses_list.replace(":", "")
    addresses_list = addresses_list.replace("addr", "inet")
    addresses_list = addresses_list.split(",")
    string_to_print = ""
    for x in range(0, len(addresses_list)):
        if "peer" not in addresses_list[x]:
            string_to_print = string_to_print + addresses_list[x]
    string_to_print = "\t" + string_to_print
    print(string_to_print)

def printLineThree(current_interface: str):
    interface_list = netifaces.ifaddresses(current_interface)[10]
    inet_6_address = str(interface_list[0]['addr'])
    inet_6_address_list = inet_6_address.split("%")
    inet_6_address = inet_6_address_list[0]

    print("\tinet6 " + inet_6_address + " ", end="")
    if current_interface == "enp0s3":
        print("prefixlen 64 ", end="")  
    elif current_interface == "lo":
        print("prefixlen 128 ", end="")  

    if current_interface == "enp0s3":
        print("scopeid 0x20<link>") 
    elif current_interface == "lo":
        print("scopeid 0x10<host>") 

def printLineFour(current_interface: str):
    MAC_address = netifaces.ifaddresses(current_interface)[17][0]['addr']
    line_four_to_print = "\t"
    if "en" in current_interface:
        line_four_to_print = line_four_to_print + "ether " + MAC_address + " "
    if current_interface == "lo":
        line_four_to_print = line_four_to_print + "loop "
    print(line_four_to_print)

def printLineFive(current_interface: str):
    interface_info = psutil.net_io_counters(pernic=True)[current_interface]
    line_five_to_print = "\tRX packets "
    interface_list = list(interface_info)
    line_five_to_print = line_five_to_print + str(interface_list[3]) + " " #RX packets
    line_five_to_print = line_five_to_print + "bytes " + str(interface_list[1]) + " "
    print(line_five_to_print)


def printLineSix(current_interface):
    interface_info = psutil.net_io_counters(pernic=True)[current_interface]
    interface_list = list(interface_info)
    line_six = "\tRX errors " + str(interface_list[4]) + " "
    line_six = line_six + "dropped " + str(interface_list[6]) + " "
    print(line_six)


def printLineSeven(current_interface):
    interface_info = psutil.net_io_counters(pernic=True)[current_interface]
    interface_list = list(interface_info)
    line_seven = "\tTX packets " + str(interface_list[2]) + " "
    line_seven = line_seven + "bytes " + str(interface_list[0]) + " "
    line_seven = line_seven + str(interface_list[5]) + " "
    print(line_seven)

def printLineEight(current_interface):
    interface_info = psutil.net_io_counters(pernic=True)[current_interface]
    interface_list = list(interface_info)
    line_eight = "\tTX errors " + str(interface_list[5]) + " "
    line_eight = line_eight + "dropped " + str(interface_list[7])
    print(line_eight)

def printAllIfconfigLines():
    original_net_if_stats_dict = psutil.net_if_stats()
    new_net_if_stats_dict = {}

    #reverses the dictionary to be in the form "enp0s3" and then "lo"
    while original_net_if_stats_dict:
        key, value = original_net_if_stats_dict.popitem()
        new_net_if_stats_dict[key] = value

    for current_interface in new_net_if_stats_dict:
        printLineOne(current_interface, new_net_if_stats_dict)
        printLineTwo(current_interface)
        printLineThree(current_interface)
        printLineFour(current_interface)
        printLineFive(current_interface)
        printLineSix(current_interface)
        printLineSeven(current_interface)
        printLineEight(current_interface)
        print()

def main():

    printAllIfconfigLines()


if __name__ == '__main__':
    main()