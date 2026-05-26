import socket
import sys
import pickle
import time
import statistics


class Reliable_Transmitter:
    __slots__ = ("IP_dest", "sending_port_num", "receiving_port_num", "sequence_num",
                 "catch_up_pointer", "far_pointer", "sent_seq_nums_waiting_for_ack",
                 "copy_of_data_in_transit", "transmit_socket", "receive_socket",
                 "received_acks_dict", "sent_first_packet", "cwnd_size", "cwnd_list", "cwnd_fraction",
                 "ordered_packet_list", )
    IP_dest: str
    sending_port_num: int
    receiving_port_num: int
    sequence_num: int
    catch_up_pointer: int
    far_pointer: int
    sent_seq_nums_waiting_for_ack: list
    copy_of_data_in_transit: list
    transmit_socket: socket
    receive_socket: socket
    received_acks_dict: dict
    sent_first_packet: bool
    cwnd_size: int
    cwnd_list: list
    cwnd_fraction: float
    ordered_packet_list: list

    def __init__(self, IP_Destination, sending_port_number, receiving_port_number):
        self.IP_dest = IP_Destination
        self.sending_port_num = sending_port_number  # 5005
        self.receiving_port_num = receiving_port_number  # 5006
        self.sequence_num = 1  # always start with 1 because its the first packet sent
        self.catch_up_pointer = 0  # data_to_send[catch_up_pointer] to data_to_send[far_pointer] is amount of unsent packets
        self.far_pointer = 0  # window size is from data_to_send[0] to data_to_send[far_pointer]
        self.sent_seq_nums_waiting_for_ack = []
        self.copy_of_data_in_transit = []
        self.received_acks_dict = {}
        self.sent_first_packet = False
        self.cwnd_size = 0
        self.cwnd_list = []
        self.cwnd_fraction = 0
        self.ordered_packet_list = []

    def find_checksum(self, seq_num: int, total_seq_count: int, ack_num: int, data_payload: str):
        # checksum verification composed of: [curr-sequence number][total seq count][acknowledgement number][data]
        # NOTE: 'Tutorials Point' website says:
        # "The checksum is calculated by taking the binary value of all the fields
        # in the TCP header and the data, treating them as a large integer,
        # and then performing a bit-wise ones complement on that integer". then
        # you take the 16 LSBs and these 16 LSBs are the checksum

        # So i'm just gonna do what it says for the TCP header checksum
        concatenation = str(seq_num) + str(total_seq_count) + str(ack_num) + data_payload
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

    def receive_packet(self) -> list:
        #basically just receives a single packet from receiver and returns the unpickled data
        # order of data header: [curr-sequence number][total seq count][acknowledgement number][checksum?][data]
        data, addr = self.receive_socket.recvfrom(1024)  # buffer size is 1024 bytes
        unpickled_data = str(pickle.loads(data)).split("@")
        return unpickled_data


    def create_sockets(self):
        #this just creates the two transmit and receive sockets and returns pointers to them
        hostname = socket.gethostname()
        IPAddr = socket.gethostbyname(hostname)  # default IP dest is this same machine
        self.transmit_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)  # UDP datagram
        self.receive_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)  # UDP
        self.receive_socket.bind((IPAddr, int(self.receiving_port_num)))
        #return transmit_socket, receive_socket

    def increase_window_size(self, data_to_send):
        # basically this attempts to increase window size by 2 for each received ack packet
        # i.e. "slow start" (BUT DOES NOT DECREASE SIZE, ONLY INCREASES SIZE!!!)
        # now need to decrease window size by one (data to send length), but increase by two
        # also need to decrease catch-up pointer by one, and decrease far_pointer by one
        self.sent_seq_nums_waiting_for_ack.pop(0)  # removes temp seq number waiting for acknowledgment
        data_to_send.pop(0)  # decreases window size by one because another ack was received
        data_len = len(data_to_send)
        if (self.catch_up_pointer - 1) >= 0:  # dont want to have negative catch up pointer
            self.catch_up_pointer = self.catch_up_pointer - 1  # accounting for decrease in data to send
        if (self.far_pointer - 1) >= 0:
            self.far_pointer = self.far_pointer - 1  # accounting for decrease in data to send
        if (self.far_pointer + 2) < data_len:  # able to increase window size by 2
            self.far_pointer = self.far_pointer + 2  # increase window size by 2
        elif (self.far_pointer + 2) >= data_len:  # not able to increase window size by 2
            if (self.far_pointer + 1) < data_len:  # able to increase window size by 1
                self.far_pointer = self.far_pointer + 1
            elif (self.far_pointer + 1) >= data_len:  # not able to increase window size at all
                self.far_pointer = self.far_pointer  # same window size bc you're nearing end of data to send

    def find_seq_index(self, seq_num_to_retransmit) -> int:
        for x in range(0, len(self.sent_seq_nums_waiting_for_ack)):
            if self.sent_seq_nums_waiting_for_ack[x] == seq_num_to_retransmit:
                return x

    def find_total_seq_count(self, data_to_send):
        return len(data_to_send) - 1

    # below method has been tested and works! yay
    def find_timeout(self, RTT_list):
        std_dev = statistics.stdev(RTT_list)
        average_RTT = sum(RTT_list)/len(RTT_list)
        official_TO_time = average_RTT + (4 * std_dev) # RTT + 4sigma
        return official_TO_time

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

    def connect_to_server(self):
        # order of data header: [curr-sequence number][total seq count][acknowledgement number][checksum?][data]
        #time for three-way handshake to 'connect' with receiver!
        #step 1: this transmitter sends SYN packet to receiver
        self.receive_socket.settimeout(4) # timeout just for the initial three-way handshake
        state = 0
        while True:
            if state == 0: #state zero is transmitter trying to get a SYN packet to the receiver
                self.send_packet_transmitter(-5, -5, "SYN")
                try:
                    received_data = self.receive_packet()
                    correct_chksum = self.received_good_checksum(received_data)
                    if correct_chksum == True:
                        data = received_data[4]
                        if data == "SYN":
                            state = 1 # receiver defintely received at least one SYN packet
                            print("transmitter received SYN packet from receiver")
                except TimeoutError:
                    #if timeout error, simply resend the SYN packet
                    pass
            elif state == 1:
                self.send_packet_transmitter(-5, -5, "ACK")
                print("sent 'ACK' packet to receiver")
                try:
                    received_data = self.receive_packet()
                    correct_chksum = self.received_good_checksum(received_data)
                    if correct_chksum == True:
                        data = received_data[4]
                        if data == "SYN":
                            # if you received any data, then ACK packet was lost and need to resend ACK to receiver
                            pass
                except TimeoutError:
                    # if a timeout occured now, this means that the receiver received the "ACK"
                    # packet from this transmitter. Now need to go back to normal program
                    print("TimeoutError occured, assuming receiver got ACK packet from transmitter")
                    return

    def record_ack(self, received_ack: int):
        #this method inserts the ack received into the dictionary
        #to later check for duplicates received
        if received_ack not in self.received_acks_dict:
            # ack wasn't received before so need to add it to dictionary
            self.received_acks_dict[received_ack] = 1
        else:
            #found a duplicate ack
            self.received_acks_dict[received_ack] += 1

    def find_dup_ack(self) -> tuple[bool, int]:
        #print("sequence numbers in dict? @@@")
        for x in self.received_acks_dict:
            if self.received_acks_dict[x] > 1:
                #found a dupAck
                return True, x
        return False, -5


    def slow_start(self, seq_num, total_seq_cnt, data) -> int:
        #this method sends one to two packets, and adjusts the cwnd size and its contents
        #NOTE: THIS METHOD IS FOR SLOW START!!!!
        if seq_num != total_seq_cnt:
            if self.sent_first_packet == False:
                #send the very first packet, so only send one
                print("v-----------------v")
                self.send_packet_transmitter(seq_num, total_seq_cnt, data[seq_num])  # correct!
                self.sent_first_packet = True
                self.cwnd_size = self.cwnd_size + 1
                self.cwnd_list.append(seq_num)
                print("sent pkt " + str(seq_num) + " data: " + str(data[seq_num]))
                print("cwnd size: " + str(self.cwnd_size))
                print("cwnd list: " + str(self.cwnd_list))
                print("^-----------------^")
                return seq_num + 1
            elif self.sent_first_packet == True:
                #send two packets because received non-duplicate acknowledgment
                print("v-----------------v")
                for _ in range(0, 2):
                    self.send_packet_transmitter(seq_num, total_seq_cnt, data[seq_num])  # correct!
                    self.cwnd_size = self.cwnd_size + 1
                    self.cwnd_list.append(seq_num)
                    print("sent pkt " + str(seq_num) + " data: " + str(data[seq_num]))
                    print("cwnd size: " + str(self.cwnd_size))
                    print("cwnd list: " + str(self.cwnd_list))
                    if seq_num == total_seq_cnt:
                        #stop sending data if you've sent all the data
                        # you just need to wait for acks/dupAcks from receiver
                        print("sent all data to receiver at least once! (123)")
                        print("^-----------------^")
                        break
                    seq_num = seq_num + 1

                print("^-----------------^")
                return seq_num
        else:
            print("v-----------------v")
            print("sent all data to receiver at least once! (456)")
            print("cwnd size: " + str(self.cwnd_size))
            print("cwnd list: " + str(self.cwnd_list))
            print("^-----------------^")
            return seq_num

    def found_dupAck_logic(self):
        # already got one dupAck, now need to wait for two more
        for _ in range(0, 2):
            received_data_list = self.receive_packet()  # received packet from receiver
            self.cwnd_list.pop(0)

    def remove_duplicates(self):
        for x in self.received_acks_dict:
            if self.received_acks_dict[x] > 1:
                #found a dupAck
                self.received_acks_dict[x] = 1


    def fast_retransmit(self, dup_ack_num, total_seq_count, data_to_send,curr_ack_from_receiver) -> int:
        ssthresh = int(self.cwnd_size / 2)  # floor of the cwndsize / 2
        self.found_dupAck_logic()  # waits for two more acknowledgments
        # now have received 3 dupAcks
        # now to resend the lost packet
        resend_seq_num = dup_ack_num - 1
        self.send_packet_transmitter(resend_seq_num, total_seq_count, data_to_send[resend_seq_num])
        self.cwnd_size = 1
        self.cwnd_list.clear()
        self.cwnd_list.append(dup_ack_num - 1)
        # now to ignore any additional duplicates until a new non-dup ack arrives
        #Note: timeout might occur but in timeout you resend the last two packets
        #then you can determine if you still get dupacks by what comes back
        while curr_ack_from_receiver == dup_ack_num:
            received_data_list = self.receive_packet()  # received packet from receiver
            correct_chksum = self.received_good_checksum(received_data_list)
            if correct_chksum == True:
                curr_ack_from_receiver = int(received_data_list[2])
                if curr_ack_from_receiver == dup_ack_num:
                    self.cwnd_list.pop(0)
                    self.cwnd_size = self.cwnd_size - 1
        # got a good acknowledgment number!
        # now to transmit the data corresponding to the current received
        #I.E reenter slow start!
        return ssthresh

    def congestion_avoidance(self, seq_num, total_seq_cnt, data)->int:
        #simply send one packet
        fraction = 1 / self.cwnd_size
        self.cwnd_fraction = self.cwnd_fraction + fraction
        #original_cwnd_size = self.cwnd_size
        #copy_of_seq_num = copy_of_seq_num + self.cwnd_fraction
        if int(self.cwnd_size + self.cwnd_fraction) >= self.cwnd_size:
            #time to increase cwnd size because the fraction has overtaken the original size
            #since you increase cwnd size you must send two packets
            self.send_packet_transmitter(seq_num, total_seq_cnt, data[seq_num])
            self.cwnd_size = self.cwnd_size + 1
            self.cwnd_list.append(seq_num)
            seq_num = seq_num + 1
            self.send_packet_transmitter(seq_num,total_seq_cnt,data[seq_num])
            self.cwnd_list.append(seq_num)
        else:
            self.send_packet_transmitter(seq_num, total_seq_cnt, data[seq_num])
            self.cwnd_list.append(seq_num)
        return seq_num + 1

    def send_to_dest(self, user_command, data_to_send: list):
        # data_to_send must be a list of all the data in order
        # order of data header: [curr-sequence number][total seq count][acknowledgement number][checksum][data]
        if user_command == "connect":
            self.create_sockets()
            self.connect_to_server()
            print("created sockets and connected to server")
            return

        #first send a message to the receiver for "put" or "get"
        self.send_packet_transmitter(-5, -5, "put")

        timeout_val = 1  # default timeout value is 1 and will be updated later

        total_seq_count = self.find_total_seq_count(data_to_send)  # correct one!
        print("total sequence count: " + "")
        self.receive_socket.settimeout(timeout_val)
        #self.receive_socket.settimeout(None)
        curr_ack_from_receiver = 0  # initially 1 then gets updated in below while loop
        seq_num_to_send = 0
        RTT_list = []
        sent_time = 0
        found_official_RTT_time = False
        ssthresh = 123456789 # some very large number to start with
        seq_num_to_send = self.slow_start(seq_num_to_send, total_seq_count, data_to_send)
        while curr_ack_from_receiver != total_seq_count + 1:  # send while you haven't received final ack from receiver
            # below is for testing if ack from receiver works
            #print("timeout value: " + str(timeout_val))
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
                    RTT = received_time - sent_time # RTT in SECONDS
                    RTT_list.append(RTT)
                correct_chksum = self.received_good_checksum(received_data_list)
                if correct_chksum == True:
                    curr_ack_from_receiver = int(received_data_list[2])
                    print("current_ack_from_receiver: " + str(curr_ack_from_receiver))
                    self.record_ack(curr_ack_from_receiver)
                    found_dupAck, dup_ack_num = self.find_dup_ack()
                    if found_dupAck == False:
                        #time to send two more packets because a non-dupAck arrived
                        if self.cwnd_size < ssthresh:
                            #do slow start while you haven't reached ssthresh yet
                            seq_num_to_send=self.slow_start(seq_num_to_send,total_seq_count,data_to_send)
                        elif self.cwnd_size >= ssthresh:
                            # need to do congestion avoidance here
                            seq_num_to_send=self.congestion_avoidance(seq_num_to_send,total_seq_count,data_to_send)

                    elif found_dupAck == True:
                        #found a dupack! which means a packet was lost. Therefore must wait until 2 more dupAcks come
                        ssthresh = self.fast_retransmit(dup_ack_num, total_seq_count, data_to_send, curr_ack_from_receiver)
                        #restart slow start here
                        self.cwnd_fraction = 0
                        seq_num_to_send = self.slow_start(seq_num_to_send, total_seq_count, data_to_send)



                elif correct_chksum == False:
                    raise TimeoutError #TCP times out if the received checksum is incorrect
            except TimeoutError:
                #time to resend the previously sent packet (and later reduce the sending rate)
                #if timeout occurs, then need to reset cw
                seq_num_to_send = seq_num_to_send - 2 #resend the last two packets? TCP-Tahoe doesn't specify
                #i think i also need to remove the duplicates in the dict or else its possible
                #you may never get another 3 duplicates after fast retransmit
                self.cwnd_fraction = 0
                self.remove_duplicates()
                self.slow_start(seq_num_to_send,total_seq_count, data_to_send)
                print("timeout error occured!!")


        self.transmit_socket.close()
        self.receive_socket.close()

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

    def send_packet_receiver(self, seq_num: int, total_seq_cnt: int, ack_num: int, data_payload: str):
        # order of data header: [curr-sequence number][total seq count][acknowledgement number][checksum][data]
        #print("sending ack to transmitter in send_ack: " + str(ack_num))
        checksum = self.find_checksum(seq_num, total_seq_cnt, ack_num, data_payload)
        data_to_send_str = str(seq_num)+"@"+str(total_seq_cnt)+"@"+str(ack_num)+"@"+str(checksum)+"@"+data_payload
        data_to_send_in_bytes = pickle.dumps(data_to_send_str)
        print("sending ack to transmitter: " + str(ack_num))
        self.transmit_socket.sendto(data_to_send_in_bytes, (self.IP_dest, int(self.sending_port_num)))


    def send_ack(self, total_seq_count: int, ack_num_to_send: int):
        # need to have unpickled data because the receiver needs to verify the packet wasn't corrupted from checksum
        # order of data header: [curr-sequence number][total seq count][acknowledgement number][checksum][data]
        seq_num = ack_num_to_send - 1  # transmitter won't use this
        sending_ack_num = ack_num_to_send
        data = ""  # transmitter won't use this
        #print("sending ack to transmitter in send_ack: " + str(sending_ack_num))
        self.send_packet_receiver(seq_num, total_seq_count, sending_ack_num, data)

    def receive_from_dest(self, name_of_file):
        self.create_sockets()
        self.connect_to_server()
        print("connected to server!")
        self.receive_socket.settimeout(None)

        self.send_packet_transmitter(-5, -5, "get")
        self.send_packet_transmitter(-5, -5, name_of_file)

        #everthing below here is from reliable-receiver.py file
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


def create_file():
    name_of_file = "File Name 1 - from Transmitter.txt"
    file = open(name_of_file, "w")  # 'w' both creates new files and overwrites the same-named file
    file.write("\n")  # /n makes next file.write go to next line
    file.write("\n")
    file.write("hehe \n")
    file.write("\n")
    file.write("blink-182 is pretty good :)")
    file.write("\n")
    # f.writelines(["Hello World ", "You are welcome to Fcc\n"])
    file.close()


def read_and_return_created_file(name_of_file_to_read_and_send):
    with open(name_of_file_to_read_and_send) as file:
        raw_list = list(file)
    #print(raw_list)
    raw_list.insert(0, name_of_file_to_read_and_send)
    #print("data to send to receiver: " + str(raw_list))
    return raw_list

def compress_to_512_packets_size(raw_data_list) -> list:
    print("incoming raw data list: " + str(raw_data_list))
    # title_of_file = raw_data_list[0]
    # print("title of file from compress to 512 packet method: " + str(title_of_file))
    one_huge_string = ""
    for x in range(1, len(raw_data_list)):
        #appending all data into one string so its easier to split into 512 bytes
        one_huge_string = one_huge_string + raw_data_list[x]
    #one_huge_bytes =
    #length_hehe = len(one_huge_string[512:1024])
    compressed_list = [raw_data_list[0]]
    low_pointer = 0 # used for splitting data into 512 chunks
    high_index = 512 # used for splitting data into 512 chunks
    current_idx_to_print = 1
    #print("length one_huge_string = " + str(len(one_huge_string[low_pointer:high_index])))
    while len(one_huge_string[low_pointer:]) > 512: #while rest of data is more than 512 bytes
        compressed_list.append(one_huge_string[low_pointer: high_index])
        print("length of stored 512 chunk: " + str(len(compressed_list[current_idx_to_print])))
        current_idx_to_print = current_idx_to_print + 1
        low_pointer = high_index
        high_index = high_index + 512 # increase high pointer by the 512 chunk
    compressed_list.append(one_huge_string[low_pointer:])
    print("length of final 512 chunk: " + str(len(compressed_list[current_idx_to_print])))
    #print("length of stored 512 chunk: " + str(len(compressed_list[current_idx_to_print])))
    return compressed_list


def test_reliable_transmitter(transmitter_obj, user_command, name_of_file):
    # note: comment-out this function when working on Part 2 of this project
    # NOTE: all this function should do is call upon the TCP send and data it wants to send, nothing else
    # create_file() #simply for testing, won't be used when user wants to send/receive a file
    #name_of_file = "File Name 1 - from Transmitter.txt"
    raw_data_array = read_and_return_created_file(name_of_file)
    compressed_data_array = compress_to_512_packets_size(raw_data_array)
    transmitter_obj.send_to_dest(user_command, compressed_data_array)  # this will eventually send a file
    # need to make another method HERE to receive a file from receiver


def find_user_inputs():
    user_command = ""
    user_file_name = ""
    raw_user_input = input("Enter input here: ")
    if "connect" in raw_user_input:
        user_command = "connect"
        user_file_name = None
    elif "quit" in raw_user_input:
        user_command = "quit"
        user_file_name = None
    elif "?" in raw_user_input:
        user_command = "?"
        user_file_name = None
    elif "put" in raw_user_input:
        #"put name of file"
        user_command = "put"
        user_file_name = raw_user_input[4:]
    elif "get" in raw_user_input:
        user_command = "get"
        user_file_name = raw_user_input[4:]
    #print("user command: " + user_command + " and file: " + str(user_file_name))
    return user_command, user_file_name


def print_help_info():
    print("Enter your commands below. Commands are:")
    print("'connect'                  which officially connects your computer to the server")
    print("'put' [name_of_file]'      which sends a file with the specified name to the server")
    print("'get' [name_of_file]'      which receives a file with the specified name from the server")
    print("'quit'                     which ends this program immediately")
    print("'?'                        which prints this help message")

def main():
    hostname = socket.gethostname()
    IPAddr = socket.gethostbyname(hostname)  # default IP dest is this same machine
    print("transmitter's IP: " + str(IPAddr))
    arg_dict = parse_args()
    #print(arg_dict)
    print("sending port num=" + str(arg_dict["-sending_port"]))
    print("receiving port num=" + str(arg_dict["-receiving_port"]))

    ip_dest = arg_dict["-dest"]
    sending_port_num = arg_dict["-sending_port"]
    receiving_port_num = arg_dict["-receiving_port"]
    transmitter_obj = Reliable_Transmitter(ip_dest, sending_port_num, receiving_port_num)
    print_help_info()
    user_command = ""
    while True:  # (user_command != "put") or (user_command != "get") or (user_command != "connect"):
        # this is only for processing the "quit" and "?" commands
        user_command, file_name = find_user_inputs()
        if user_command == "quit":
            return
        if user_command == "?":
            print_help_info()
        else:
            break
    connected_to_server = False
    while True:
        if (user_command == "connect") and (connected_to_server == False):
            useless_list = []
            transmitter_obj.send_to_dest(user_command, useless_list)
            connected_to_server = True
        elif (user_command == "connect") and (connected_to_server == True):
            #already connected to server
            print("You already connected to the server!")
        elif (user_command == "put") and (connected_to_server == True):
            test_reliable_transmitter(transmitter_obj, user_command, file_name)
            # basically end program
            return
        elif (user_command == "get") and (connected_to_server == True):
            transmitter_obj.receive_from_dest(file_name)
            #end the program after receiving a file
            return

        user_command, file_name = find_user_inputs()






if __name__ == '__main__':
    main()
