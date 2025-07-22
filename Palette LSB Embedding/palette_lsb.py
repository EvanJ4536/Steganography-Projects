
# TODO:  add choice for multiple bits of hiding per byte

import sys

# Get all the information we need out of the file
def processFile(filename):
    with open(filename, "rb") as f:
        # Read byte 10 to 14 which holds bfOffBits, the offset to the pixel data in little endian
        f.seek(10)
        pixel_offset = f.read(4)
        pixel_offset = int.from_bytes(pixel_offset, 'little')
        
        # Read byte 14 to 18disc which hold the size of the DIB header in little endian
        palette_offset = f.read(4)
        palette_offset = int.from_bytes(palette_offset, 'little')
                
        # Get start of palette and size
        palette_start = 14 + palette_offset
        palette_size = pixel_offset - palette_start
        
        f.seek(0)
        header = f.read(palette_start)
        header = bytearray(header)
        
        # Read palette and put it in a list
        palette_data = f.read(palette_size)
        palette_list = [palette_data[i:i+4] for i in range(0, len(palette_data), 4)]
        number_of_colors = palette_size // 4
        print("There are {} palette entries".format(number_of_colors))
        
        capacity = number_of_colors * 3 // 8
        print("Capacity is: {} bytes".format(capacity))
        
        # Get pixel data and count occurences of each palette entry
        pixel_data = f.read()
        pixel_counts = [0] * (number_of_colors)
        try:
            for byte in pixel_data:
                pixel_counts[byte] += 1
        except:
            print("Too many colors. Maybe the inFile isnt a pallete bmp")
            sys.exit(1)

    print("pixel offset:", pixel_offset)
    print("palette start:", palette_start)
    print("palette size bytes:", palette_size)
    print("number of colors:", palette_size // 4)
    
    return palette_list, pixel_data, header
    
# Takes palette list as a parameter and converts RGB bytes to binary
def paletteToBinary(palette_list):
    binary_palette_list = []
    for color in palette_list:
        for byte in color[:3]:
            binary_palette_list.append(format(byte, '08b'))
          
    return binary_palette_list
    
# Takes a file as parameter and converts it to binary
def messageToBinary(messageFile):
    with open(messageFile, 'rb') as f:
        message_bytes = f.read()
    
    binary_message = ''
    for byte in message_bytes:
        binary_message += ''.join(format(byte, '08b'))
        
    return binary_message

# Embed the message into the palette
def embedMessage(binary_palette_list, binary_message, header, pixel_data):    
    # Get number of bytes in message in decimal
    message_size = len(binary_message) // 8
    
    # convert message size to hex in big endian then to binary string
    message_size_bytes = message_size.to_bytes(2, byteorder='big')
    binary_message_size = ''.join(format(byte, '08b') for byte in message_size_bytes)
    
    # Prepend binary size to binary message so the size is stored in the first 16 bytes
    binary_message = binary_message_size + binary_message
    
    # Embed lsb of message into RGB values in palette
    modified_palette_colors = []
    ctr = 0
    for byte in binary_palette_list:
        if ctr >= len(binary_message):
            modified_palette_colors.append(byte)
            continue
            
        modified_palette_colors.append(byte[:7] + binary_message[ctr])
        ctr += 1
    
    # convert new modified palette into hex
    embedded_palette = []
    for byte in modified_palette_colors:
        embedded_palette.append(int(byte, 2))
        
    embedded_palette = bytes(embedded_palette)
    
    # Take new palette back to normal 4 byte format by appending the reserved byte onto each palette entry
    palette_list = b''.join(embedded_palette[i:i+3] + b'\x00' for i in range(0, len(embedded_palette), 3))
        
    # Combine image data back together
    file_data = header + palette_list + pixel_data
    
    print("Original message length in bytes: {}".format(len(binary_message) // 8))
    print("Size embedded: {}".format(int.from_bytes(message_size_bytes, 'big')))
    
    with open('out.bmp', 'wb') as f:
        f.write(file_data)
    
# Extract a message from an image
def extractMessage(inFile, header):
    # extract pixel offset and palette offset from header
    pixel_offset = int.from_bytes(header[10:14], 'little')
    palette_offset = int.from_bytes(header[14:18], 'little')

    # Get start and size of palette
    palette_start = 14 + palette_offset
    palette_size = (pixel_offset - palette_start)
    
    with open(inFile, 'rb') as f:
        f.seek(palette_start)
        palette_data = list(f.read(palette_size))
        
    # Remove all the reserved bytes from the palette
    relevant_bytes = [palette_data[i] for i in range(len(palette_data)) if (i % 4) != 3]
    
    # create a binary string of the LSBs of each byte left in the list
    binary_message = ''.join(str(byte & 1) for byte in relevant_bytes)
    
    # First 16 bytes hold the size
    binary_size = binary_message[:16]
    
    # Convert size to hex
    message_size = int(binary_size, 2)
    
    # slice out the size header and save the rest of the message data
    binary_message = binary_message[16 : 16 + (message_size * 8)]
    
    # Format binary message string into 8 bit segments and convert each to 0-255 integer
    message_byte_list = [int(binary_message[i:i+8], 2) for i in range(0, len(binary_message), 8)]
    
    # Creates immutable byte sequence ready to be written to file
    message_bytes = bytes(message_byte_list)
    print("Extracted message_size: {} bytes".format(message_size))
    with open("out.txt", 'wb') as f:
        f.write(message_bytes)
    
def usage():
    print("""
    Usage
    ------------------------------
    python hide_in_palette.py operation sourceFile messageFile
    
    python hide_in_palette.py embed infile.bmp message.txt
    
    A file named out.bmp will be created with the new image
    """)
      
def main():
    if len(sys.argv) < 3:
        usage()
        return 1
        
    operation = sys.argv[1]
    sourceFile = sys.argv[2]
    
    if operation == 'embed':
        messageFile = sys.argv[3]
        
    palette_list, pixel_data, header = processFile(sourceFile)
    
    if operation == 'embed':
        binary_palette_list = paletteToBinary(palette_list)
        binary_message = messageToBinary(messageFile)
        embedMessage(binary_palette_list, binary_message, header, pixel_data)
        
    elif operation == 'extract':
        extractMessage(sourceFile, header)
        
main()