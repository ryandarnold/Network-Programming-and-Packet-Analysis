import socket
import sys
import pickle
import time


class Reliable_Receiver:
    __slots__ = ("IP_dest", "sending_port_num", "receiving_port_num", "ordered_packet_list",
                 "transmit_socket", "receive_socket")
    IP_dest: str
    sending_port_num: int
    receiving_port_num: int
    # ordered_seq_nums_list: list
    # ordered_data_list: list
    ordered_packet_list: list
    transmit_socket: socket
    receive_socket: socket

    def __init__(self, IP_Destination, sending_port_number, receiving_port_number):
        self.IP_dest = IP_Destination
        self.sending_port_num = sending_port_number  # 5006
        self.receiving_port_num = receiving_port_number  # 5005
        self.ordered_packet_list = []  # ordering entire packet, not their seq # and data separately

    def create_sockets(self):
        hostname = socket.gethostname()
        this_computers_IP_Addr = socket.gethostbyname(hostname)  # default IP dest is this same machine
        print("This computer's IP: " + str(this_computers_IP_Addr))
        #receiving_port_num = self.receiving_port_num
        self.receive_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)  # UDP
        self.receive_socket.bind((this_computers_IP_Addr, int(self.receiving_port_num)))

        self.transmit_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)  # UDP datagram
        #return transmit_socket, receive_socket

    def send_packet_receiver(self, seq_num: int, total_seq_cnt: int, ack_num: int, data_payload: str):
        # order of data header: [curr-sequence number][total seq count][acknowledgement number][checksum][data]
        #print("sending ack to transmitter in send_ack: " + str(ack_num))
        checksum = self.find_checksum(seq_num, total_seq_cnt, ack_num, data_payload)
        data_to_send_str = str(seq_num)+"@"+str(total_seq_cnt)+"@"+str(ack_num)+"@"+str(checksum)+"@"+data_payload
        data_to_send_in_bytes = pickle.dumps(data_to_send_str)
        print("sending ack to transmitter: " + str(ack_num))
        self.transmit_socket.sendto(data_to_send_in_bytes, (self.IP_dest, int(self.sending_port_num)))

    def find_checksum(self, seq_num: int, total_seq_cnt: int, sending_ack_num: int, data_to_send: str):
        # don't think I need seq num or data to send. They can be hardcoded to zero I guess
        # order of data header: [curr-sequence number][total seq count][acknowledgement number][checksum][data]
        concatenation = str(seq_num) + str(total_seq_cnt) + str(sending_ack_num) + data_to_send
        bytes_string = bytes(concatenation, 'utf-8')
        byte_list = list(bytes_string)
        xor_final_list = []
        for byte in byte_list:  # goes through each 'character' in the byte_list and finds the complement of each byte
            xor_full_byte = 0
            for curr_bit_idx in range(0, 8):  # 0 to 8 because each byte has 8 bits
                bit_value = (byte >> curr_bit_idx) & 1
                new_complemented_bit = bit_value ^ 1
                xor_full_byte = xor_full_byte | (new_complemented_bit << curr_bit_idx)
            xor_final_list.append(xor_full_byte)
        xor_concatenated_string = ""
        for x in xor_final_list:
            xor_concatenated_string = xor_concatenated_string + str(x)
        xor_bytes = bytes(xor_concatenated_string, 'utf-8')
        last_two_bytes = xor_bytes[len(xor_bytes) - 2:len(xor_bytes)]
        return last_two_bytes

    def received_good_checksum(self, unpickled_data) -> bool:
        # order of data header: [curr-sequence number][total seq count][acknowledgement number][checksum][data]
        seq_num = unpickled_data[0]
        total_seq_cnt = unpickled_data[1]
        ack_num = unpickled_data[2]
        data_str = unpickled_data[4]
        received_verified_chksum = str(self.find_checksum(seq_num, total_seq_cnt, ack_num, data_str))
        chksum_from_packet = unpickled_data[3]
        if received_verified_chksum == chksum_from_packet:
            #print("got correct checksum!!!!!!!@@@@@@@@@@@")
            return True
        else:
            print("GOT INCORRECT CHECKSUM :( SAD FACE")
            return False

    def send_ack(self, total_seq_count: int, ack_num_to_send: int):
        # need to have unpickled data because the receiver needs to verify the packet wasn't corrupted from checksum
        # order of data header: [curr-sequence number][total seq count][acknowledgement number][checksum][data]
        seq_num = ack_num_to_send - 1  # transmitter won't use this
        sending_ack_num = ack_num_to_send
        data = ""  # transmitter won't use this
        #print("sending ack to transmitter in send_ack: " + str(sending_ack_num))
        self.send_packet_receiver(seq_num, total_seq_count, sending_ack_num, data)

    # below method has been tested and works! yay
    def order_incoming_data(self, unpickled_data):
        # need to reorder the packets by seq number in ascending order in case packets come in wrong order
        # NOTE: this method simply orders the incoming packet into the previously received packets
        # --> we still may be missing packets after this method finishes, but will be in order

        # order of data header: [curr-sequence number][total seq count][acknowledgement number][checksum][data]
        seq_num_to_insert = int(unpickled_data[0])
        inserted_pkt = False
        current_idx = 0
        max_index_possible = len(self.ordered_packet_list) - 1
        if max_index_possible == -1:  # if inserting the very first packet into list
            self.ordered_packet_list.insert(current_idx, unpickled_data)
            return

        seq_num_already_in_list = False  # False means packet hasn't been received before
        for x in self.ordered_packet_list:
            if x[0] == seq_num_to_insert:
                seq_num_already_in_list = True
                break
        if seq_num_already_in_list == False:  # only want to add new sequence numbers to list
            # received a non-duplicate packet
            while inserted_pkt == False:
                if seq_num_to_insert < int(self.ordered_packet_list[current_idx][0]):
                    self.ordered_packet_list.insert(current_idx, unpickled_data)
                    inserted_pkt = True
                elif (seq_num_to_insert >= int(self.ordered_packet_list[current_idx][0])) and (
                        current_idx != max_index_possible):
                    current_idx = current_idx + 1
                elif (seq_num_to_insert >= int(self.ordered_packet_list[current_idx][0])) and (
                        current_idx == max_index_possible):
                    # reached end of ordered list and need to insert packet
                    current_idx = current_idx + 1
                    self.ordered_packet_list.insert(current_idx, unpickled_data)
                    inserted_pkt = True



    #below method has been tested and works! yay
    def find_next_ack_num(self) -> int:
        # returns the next packet the transmitter needs to send
        if len(self.ordered_packet_list) > 0:
            if int(self.ordered_packet_list[0][0]) != 0:
                # check if very first packet is missing
                ack_to_send = 0  # sending 0 because receiver needs next packet with seq_num = 0
                return ack_to_send
            else:  # you have the very first packet correct
                current_idx = 0
                for curr_pkt in self.ordered_packet_list:
                    if int(curr_pkt[0]) != current_idx:
                        # found a missing packet in the ordered packet list
                        return current_idx
                    elif int(curr_pkt[0]) == current_idx:
                        pass  # do nothing because the packets are in order so far
                    current_idx = current_idx + 1
                return current_idx
        else:
            return 0

    def terminate_connection(self, total_seq_cnt, ack_to_send):
        # order of data header: [curr-sequence number][total seq count][acknowledgement number][checksum][data]
        # receiver runs in a loop once all data has been received. Only the transmitter program will end
        # receive program cannot end unless the receiver has a very long timeout ~ 30 seconds or so
        #NOTE: DONT DO THREE-WAY END HANDSHAKE UNTIL I'VE DONE MOST OF MY PROGRAM BECAUSE IT ISN'T CRITICAL
        # step 1: need to send final acknowledgement to transmitter (this was skipped in the caller to this method)
        # step 2
        print("entered terminate connection")
        # print("data received: ")
        # for x in self.ordered_packet_list:
        #     print(x[4] + " ", end="")
        while True:
            print("", end="")
        #NOTE: THIS METHOD ISN'T FINISHED YET!!!!

    def write_received_data(self):
        # order of data header: [curr-sequence number][total seq count][acknowledgement number][checksum][data]
        # note: the 0th index of the data is the file name
        name_of_file = self.ordered_packet_list[0][4]
        new_name = "69420 " + name_of_file # simply for testing on a single computer
        # for x in range(1, len(self.ordered_packet_list)):
        #     print("huh" + self.ordered_packet_list[x][4])
        #print("got to write_received_data")
        file = open(new_name, "w")  # 'w' both creates new files and overwrites the same-named file
        #print("name of file at receiver, from transmitter: " + str(new_name))
        for x in range(1, len(self.ordered_packet_list)):
            file.write(self.ordered_packet_list[x][4])
        file.close()


    def end_program(self, curr_seq_num, total_seq_count, ack_to_send):
        #know we have received all data from transmitter, now to write this data to a file on this computer

        end_program = False
        if len(self.ordered_packet_list) > 0:  # first check if you can index into packet list
            # now need to check if you've received all packets needed for full file transfer
            if (curr_seq_num == int(self.ordered_packet_list[0][1])) and (ack_to_send == (curr_seq_num + 1)):
                # time to stop communicating with transmitter bc all data received
                self.write_received_data()
                end_program = self.terminate_connection(total_seq_count, ack_to_send)
        return end_program

    def find_timeout_when_receiving_file(self, transmit_socket, receive_socket):
        #NOTE: this method is called when the receiver (this program) is receiving a file from transmitter
        #all this method does it receive a packet and resend it immediately
        #to help the transmitter determine its timeout time
        x = 0
        #while x
        pass

    def receive_packet(self) -> list:
        #basically just receives a single packet from receiver and returns the unpickled data
        # order of data header: [curr-sequence number][total seq count][acknowledgement number][checksum?][data]
        data, addr = self.receive_socket.recvfrom(1024)  # buffer size is 1024 bytes
        unpickled_data = str(pickle.loads(data)).split("@")
        return unpickled_data

    def connect_to_client(self):
        # three-way handshake
        # no timeout initially because need to give user time to connect
        state = 0
        while True:
            if state == 0:
                received_data = self.receive_packet()
                #if you got here, then you received some data from transmitter
                correct_chksum = self.received_good_checksum(received_data)
                if correct_chksum == True:
                    data = received_data[4]
                    if data == "SYN":
                        #got a SYN packet from transmitter
                        print("got a SYN packet from transmitter!")
                        state = 1
                        #NOTE@@@@@: need to send a packet to the transmitter here!!!!!!!!!!!!!!!@@@@@@@@
                        self.send_packet_receiver(-5, -5,-5, "SYN" )
                        self.receive_socket.settimeout(1) #needs to be lower than the transmit timeout
            elif state == 1:
                try:
                    received_data = self.receive_packet()
                    # if you got here, then you received some data from transmitter
                    correct_chksum = self.received_good_checksum(received_data)
                    if correct_chksum == True:
                        data = received_data[4]
                        if data == "ACK":
                            # got a SYN packet from a client
                            return #time to go back to normal waiting to receive data from transmitter
                except TimeoutError:
                    #time to resend the SYN packet
                    self.send_packet_receiver(-5, -5, -5, "SYN")
                    print("had to resend the SYN packet rip")

    def testing_dup_ack_on_transmitter(self):
        return 5

    def find_total_seq_count(self, data_to_send):
        return len(data_to_send) - 1

    def send_packet_transmitter(self, seq_num: int, total_seq_cnt: int, data_payload: str):
        # all this method should do is send a single packet with a single payload
        # and appends the sequence number, ack number, checksum, and data together and then sends it
        # data_to_send_in_bytes = data_payload.encode('utf-8')
        # order of data header: [curr-sequence number][total seq count][acknowledgement number][checksum?][data]

        # need a copy of beginning sequence number in case acknowledgements fail from receiver
        # start_sequence_number = self.sequence_num
        ack_num = 0 #transmitter doesn't need to send ack so its hardcoded to zero
        chksum = self.find_checksum(seq_num, total_seq_cnt, ack_num, data_payload) #correct!
        #chksum = -63
        #print("chksum from Transmitter: " + str(chksum))
        data_to_send_str = str(seq_num) + "@" + str(total_seq_cnt) + "@" + str(ack_num) + "@" + str(chksum) + "@" + data_payload
        data_to_send_in_bytes = pickle.dumps(data_to_send_str)
        self.transmit_socket.sendto(data_to_send_in_bytes, (self.IP_dest, int(self.sending_port_num)))

    def read_and_return_created_file(name_of_file_to_read_and_send):
        with open(name_of_file_to_read_and_send) as file:
            raw_list = list(file)
        # print(raw_list)
        raw_list.insert(0, name_of_file_to_read_and_send)
        # print("data to send to receiver: " + str(raw_list))
        return raw_list

    def compress_to_512_packets_size(raw_data_list) -> list:
        print("incoming raw data list: " + str(raw_data_list))
        # title_of_file = raw_data_list[0]
        # print("title of file from compress to 512 packet method: " + str(title_of_file))
        one_huge_string = ""
        for x in range(1, len(raw_data_list)):
            # appending all data into one string so its easier to split into 512 bytes
            one_huge_string = one_huge_string + raw_data_list[x]
        # one_huge_bytes =
        # length_hehe = len(one_huge_string[512:1024])
        compressed_list = [raw_data_list[0]]
        low_pointer = 0  # used for splitting data into 512 chunks
        high_index = 512  # used for splitting data into 512 chunks
        current_idx_to_print = 1
        # print("length one_huge_string = " + str(len(one_huge_string[low_pointer:high_index])))
        while len(one_huge_string[low_pointer:]) > 512:  # while rest of data is more than 512 bytes
            compressed_list.append(one_huge_string[low_pointer: high_index])
            print("length of stored 512 chunk: " + str(len(compressed_list[current_idx_to_print])))
            current_idx_to_print = current_idx_to_print + 1
            low_pointer = high_index
            high_index = high_index + 512  # increase high pointer by the 512 chunk
        compressed_list.append(one_huge_string[low_pointer:])
        print("length of final 512 chunk: " + str(len(compressed_list[current_idx_to_print])))
        # print("length of stored 512 chunk: " + str(len(compressed_list[current_idx_to_print])))
        return compressed_list

    def send_to_dest(self, name_of_file: str):


        raw_data_array = self.read_and_return_created_file(name_of_file)
        data_to_send = self.compress_to_512_packets_size(raw_data_array)

        timeout_val = 1  # default timeout value is 1 and will be updated later

        total_seq_count = self.find_total_seq_count(data_to_send)  # correct one!
        print("total sequence count: " + "")
        self.receive_socket.settimeout(timeout_val)
        # self.receive_socket.settimeout(None)
        curr_ack_from_receiver = 0  # initially 1 then gets updated in below while loop
        seq_num_to_send = 0
        RTT_list = []
        sent_time = 0
        found_official_RTT_time = False
        ssthresh = 123456789  # some very large number to start with
        seq_num_to_send = self.slow_start(seq_num_to_send, total_seq_count, data_to_send)
        while curr_ack_from_receiver != total_seq_count + 1:  # send while you haven't received final ack from receiver
            # below is for testing if ack from receiver works
            # print("timeout value: " + str(timeout_val))
            if seq_num_to_send < 3:
                # only update for first 3 packets sent (seq num 0-2)
                sent_time = time.time()
            elif (seq_num_to_send >= 3) and (found_official_RTT_time == False):
                found_official_RTT_time = True
                # timeout_val = self.find_timeout(RTT_list)
                # self.receive_socket.settimeout(timeout_val) # comment this out when testing

            try:
                received_data_list = self.receive_packet()  # received packet from receiver
                self.cwnd_list.pop(0)
                self.cwnd_size = self.cwnd_size - 1
                if seq_num_to_send < 3:
                    received_time = time.time()
                    RTT = received_time - sent_time  # RTT in SECONDS
                    RTT_list.append(RTT)
                correct_chksum = self.received_good_checksum(received_data_list)
                if correct_chksum == True:
                    curr_ack_from_receiver = int(received_data_list[2])
                    print("current_ack_from_receiver: " + str(curr_ack_from_receiver))
                    self.record_ack(curr_ack_from_receiver)
                    found_dupAck, dup_ack_num = self.find_dup_ack()
                    if found_dupAck == False:
                        # time to send two more packets because a non-dupAck arrived
                        if self.cwnd_size < ssthresh:
                            # do slow start while you haven't reached ssthresh yet
                            seq_num_to_send = self.slow_start(seq_num_to_send, total_seq_count, data_to_send)
                        elif self.cwnd_size >= ssthresh:
                            # need to do congestion avoidance here
                            seq_num_to_send = self.congestion_avoidance(seq_num_to_send, total_seq_count, data_to_send)

                    elif found_dupAck == True:
                        # found a dupack! which means a packet was lost. Therefore must wait until 2 more dupAcks come
                        ssthresh = self.fast_retransmit(dup_ack_num, total_seq_count, data_to_send,
                                                        curr_ack_from_receiver)
                        # restart slow start here
                        self.cwnd_fraction = 0
                        seq_num_to_send = self.slow_start(seq_num_to_send, total_seq_count, data_to_send)



                elif correct_chksum == False:
                    raise TimeoutError  # TCP times out if the received checksum is incorrect
            except TimeoutError:
                # time to resend the previously sent packet (and later reduce the sending rate)
                # if timeout occurs, then need to reset cw
                seq_num_to_send = seq_num_to_send - 2  # resend the last two packets? TCP-Tahoe doesn't specify
                # i think i also need to remove the duplicates in the dict or else its possible
                # you may never get another 3 duplicates after fast retransmit
                self.cwnd_fraction = 0
                self.remove_duplicates()
                self.slow_start(seq_num_to_send, total_seq_count, data_to_send)
                print("timeout error occured!!")

        self.transmit_socket.close()
        self.receive_socket.close()

    def receive_message(self):
        self.create_sockets()
        self.connect_to_client()
        print("connected to client!")
        self.receive_socket.settimeout(None)

        received_data_list = self.receive_packet() #transmitter will send the directions for receiving/putting data
        if received_data_list[4] == "get":
            received_data_list = self.receive_packet()
            name_of_file = received_data_list[4]
            self.send_to_dest(name_of_file)
        elif received_data_list[4] == "put":
            testing_var = 0
            while True:
                # order of data header: [curr-sequence number][total seq count][acknowledgement number][checksum][data]
                # data, addr = self.receive_socket.recvfrom(1024)  # buffer size is 1024 bytes
                # unpickled_data = str(pickle.loads(data)).split("@")
                received_data_list = self.receive_packet()
                total_seq_count = int(received_data_list[1])
                curr_seq_num = int(received_data_list[0])

                correct_chksum = self.received_good_checksum(received_data_list)
                if correct_chksum == True:
                    # orders incoming packets by seq number bc packet was NOT corrupted
                    print("received packet data: " + str(received_data_list[4]))
                    self.order_incoming_data(received_data_list)
                # after ordering the incoming data, need to scan sequence list to make sure that
                # everything is in order one at a time. If there isn't proper order even after ordering, then need to
                # send incorrect acknowledgment to transmitter because we are missing packets

                ack_to_send = self.find_next_ack_num()  # REAL ONE HERE!!!

                end_program = self.end_program(curr_seq_num, total_seq_count, ack_to_send)
                if end_program == True:
                    self.transmit_socket.close()
                    self.receive_socket.close()
                    return

                self.send_ack(total_seq_count, ack_to_send)


def parse_args():
    argument_dictionary = {}
    for x in range(0, len(sys.argv)):
        if sys.argv[x] == "-dest":
            argument_dictionary["-dest"] = sys.argv[x + 1]
        if sys.argv[x] == "-sending_port":
            argument_dictionary["-sending_port"] = sys.argv[x + 1]
        if sys.argv[x] == "-receiving_port":
            argument_dictionary["-receiving_port"] = sys.argv[x + 1]
    return argument_dictionary


def main():
    arg_dict = parse_args()
    dest_ip = arg_dict["-dest"]
    sending_port_num = arg_dict["-sending_port"]
    receiving_port_num = arg_dict["-receiving_port"]
    print("sending port: " + sending_port_num)
    print("receiving port: " + receiving_port_num)
    receiver_obj = Reliable_Receiver(dest_ip, sending_port_num, receiving_port_num)
    receiver_obj.receive_message()


if __name__ == '__main__':
    main()
