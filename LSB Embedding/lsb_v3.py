# This script embeds data into an image using LSB steganography
# On embed the size of the data in bits is stored in the 6th to 10th bit of the header data in the image

import sys
import binascii
import random
import hashlib
import os
import math

# Embeds bits into LSB of cover file bytes
def embed(msg, filename, location, num_embed_bits):
    msg_length = len(msg) * 8
    num_bits = (msg_length + num_embed_bits - 1) // num_embed_bits
    
    # Write message size into header bytes 6 to 10
    with open(filename, 'rb+') as f:
        print("File Opened")
        f.seek(6)
        f.write(num_bits.to_bytes(4, byteorder="little"))
        
        ctr = 0
        bytes_to_mod = []
        
        f.seek(location)
        while ctr < num_bits:
            bytes_to_mod.append(f.read(1))

            ctr+=1
    
    # Convert message bytes to binary string
    binary_msg_list = []
    msg_binary_string = ''
    for byte in msg:
        msg_binary_string += bin(byte)[2:].zfill(8)
        
    # convert binary string to list
    for binary in msg_binary_string:
        binary_msg_list.append(binary)
        
    # Pad list     
    total_slots = num_bits * num_embed_bits
    if len(binary_msg_list) < total_slots:
        pad_len = total_slots - len(binary_msg_list)
        binary_msg_list.extend(['0'] * pad_len)
        
    # Convert bytes that we are going to modify to a format thats easier to modify
    mod_hex = []
    for byte in bytes_to_mod:
        mod_hex.append(binascii.hexlify(byte))
    
    # Convert bytes we are going to modify into binary and group them by 8 bits then embed a message bit in the LSB
    ctr = 0
    modified_bytes = []
    for byte in mod_hex:
        lsb_index = 7
        hide_index = num_embed_bits
        binary = bin(int(byte, 16))[2:]
        
        bin_list = list(binary)
        if len(bin_list) < 8:
            difference = 8 - len(bin_list)
            while difference > 0:
                bin_list.insert(0, '0')
                difference -= 1
        
        while hide_index > 0:
            bin_list[lsb_index] = binary_msg_list[ctr]
            #print("Hide: {}, CTR: {}".format(hide_index, ctr))
            lsb_index -= 1
            hide_index -= 1
            ctr += 1
        
        modified_binary = "".join(bin_list)
        modified_hex = hex(int(modified_binary, 2))
        modified_bytes.append(int(modified_hex, 16))
        
        
    
    # Return list of modified bytes ready for insertion
    return modified_bytes

# This function takes a list of bytes, filename and location.  Inserts the bytes into the file at location
def insert(modified_bytes, filename, location):
    # Read entire file and store it in a bytearray
    with open(filename, 'rb') as f:
        data = bytearray(f.read())
    
    # go through list of bytes and insert them into the bytearray at the target location
    for byte in modified_bytes:
        data[location] = byte
        location += 1
    
    # Remove ./ from file name in command if its there and consruct outfile name and write data
    if filename[0] == '.':
        filename = filename[2:]
        
    filename, extention = filename.split('.',1)
    out_file = "{}_mod.{}".format(filename, extention)
    with open(out_file, 'wb') as f:
        f.write(data)
        
    print("Embedded file saved as {}.".format(out_file))

# Extracts LSBs of bytes in file
def extract(location, filename, size, num_extract_bits):
    # seek to where the data is located and read bytes * 8, which gives us all the bytes that hold our embedded bits
    with open(filename, "rb") as f:
        f.seek(location)
        extracted_data = bytearray(f.read(size))
    
    # Go through extracted data and grab LSB of each byte
    extracted_lsb_list = []
    for byte in extracted_data:
        shift = 0
        num_bits = num_extract_bits
        while num_bits > 0:
            extracted_lsb_list.append((byte >> shift) & 1)
            shift += 1
            num_bits -= 1
        
    # Group bits by 8
    byte_list = []
    byte_vals = []
    byte = ""
    ctr = 0
    for bit in extracted_lsb_list:
        byte += str(bit)
        
        ctr += 1
        if ctr == 8:
            byte_list.append('0b'+byte)
            byte = ""
            ctr = 0
    
    # Comvert 8 bits to hex
    byte_vals = bytearray()
    for byte in byte_list:
        byte = int(byte, 2)
        byte_vals.append(byte)
        
    # Remove ./ from file name in command if its there and consruct outfile name and write data
    if filename[0] == '.':
        filename = filename[2:]
        
    filename, extention = filename.split('.')
    filename = "{}_extracted.{}".format(filename, extention)
    with open(filename, 'wb') as f:
        f.write(byte_vals)
        
    print("Extracted file saved as {}.".format(filename))

# print usage
def usage():
    print("Usage\n---------------------")
    print("python lsb.py [operation] [coverfile] [location] [# of bits] [msgfile/key] [key]\n")
    print("python lsb.py keygen\n")
    print("python lsb.py embed mandrill.bmp random embed_me.bmp 79664176578130264109010093313975850303\n")
    print("python lsb.py extract mandrill.bmp random 79664176578130264109010093313975850303\n\n")
    
def main():
    # Process all args
    try:
        operation = sys.argv[1]
        if operation == "keygen":
            print(random.getrandbits(128))
            return
        
        filename = sys.argv[2]
        location = sys.argv[3]
        if location != "random":
            location = int(location)
            
        num_bits = int(sys.argv[4])
            
        if operation == "embed":
            msg_file = sys.argv[5]
            if location == "random":
                key = sys.argv[6]
        else:
            try:
                key = sys.argv[5]
            except:
                pass
            
    except Exception as e:
        usage()
        print(e)
        return
    
    file_size = os.path.getsize(filename)
    
    if operation == "embed":
        with open(msg_file, 'rb') as msg_f:
            message = msg_f.read()
        
        message_size = len(message)
        carrier_bytes = math.ceil((message_size * 8) / num_bits)
    
    
    # Process random location by seeding random with a key and generating a number between 54 and (size of file - bits to embed)
    if location == "random":    
        location_min = 54
        
        if operation == "embed":
            print("Embedding {} bits into the lsb of {} bytes".format(carrier_bytes, file_size))
            
            if carrier_bytes > file_size:
                print("Too many carrier bytes to fit in the cover file.")
                return
            
            location_max = file_size - carrier_bytes
            random.seed(key)

            location = random.randint(location_min, location_max)

            print("Using key: {}".format(key))
            print("Embedding at {}".format(location))
            
        elif operation == "extract":
            # extract size of bytes to read from the 6th header byte of the coverfile this needs to be here so we can calculate location_max and get the location of the hidden data
            with open(filename, 'rb') as f:
                f.seek(6)
                message_size = bytearray(f.read(4))
                message_size = int.from_bytes(message_size, byteorder="little")
            
            print("Extracting LSBs of {} bytes".format(message_size))
            location_max = file_size - message_size
            print("File Size: {} | Msg Size: {} | max: {}".format(file_size, message_size, location_max))
            random.seed(key)
            location = random.randint(location_min, location_max)
    
    else:
        # Check if carrier_bytes is larger than hiding capacity
        if file_size - location < carrier_bytes:
            print("Too many carrier bytes to fit in the cover file.")
            return
    # Embed data
    if operation == "embed":
        modified_bytes = embed(message, filename, location, num_bits)
        insert(modified_bytes, filename, location)
        print("Done.")
        
    elif operation == "extract":
        extract(location, filename, message_size, num_bits)  
        
    else:
        usage()
        return
        
main()