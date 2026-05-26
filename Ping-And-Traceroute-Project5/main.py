

def find_checksum():
    general_string = "hello "
    yolo_swag = "world"

    contatenated_string = general_string + yolo_swag
    print("concatenated string: " + contatenated_string)
    bytes_string = bytes(contatenated_string, 'utf-8')
    print("original byte_string: " + str(bytes_string))
    byte_list = list(bytes_string)
    xor_final_list = []
    for byte in byte_list:  # goes through each 'character' in the byte_list and finds the complement of each byte
        xor_full_byte = 0
        for curr_bit_idx in range(0, 8):  # 0 to 8 because each byte has 8 bits
            bit_value = (byte >> curr_bit_idx) & 1
            new_complemented_bit = bit_value ^ 1
            xor_full_byte = xor_full_byte | (new_complemented_bit << curr_bit_idx)
        xor_final_list.append(xor_full_byte)
    # now to concatenate the xor list together and take the first 16 LSBs
    print("xor final list: " + str(xor_final_list))
    xor_concatenated_string = ""
    for x in xor_final_list:
        xor_concatenated_string = xor_concatenated_string + str(x)
    xor_bytes = bytes(xor_concatenated_string, 'utf-8')
    final_checksum = 0
    two_bytes = xor_bytes[len(xor_bytes) - 2:len(xor_bytes)]

def create_file():
    name_of_file = "solar_eclipse hehe.txt"
    file = open(name_of_file, "w") #'w' both creates new files and overwrites the same-named file
    file.write("Hello There bub\n") #/n makes next file.write go to next line
    file.write("how are you? \n")
    file.write("I'm doing well :)") #writes to th
    #f.writelines(["Hello World ", "You are welcome to Fcc\n"])
    file.close()


def main():
    #find_checksum()
    create_file()
    example_string = "Hello, this is an example string."

    encoded_bytes = example_string.encode('utf-8') #UTF-8 encoding
    lenth_of_encoded_bytes = len(encoded_bytes)
    #print("length in bytes: " + str(lenth_of_encoded_bytes))

    string_len_512_bytes = ""
    for x in range(0, 513):
        string_len_512_bytes = string_len_512_bytes + "3"
    print("length of data: " + str(len(string_len_512_bytes)))





if __name__ == '__main__':
    main()