import sys

# Get all the information we need out of the file
def processFile(filename):
    with open(filename, "rb") as f:
        # Read byte 10 to 13 which holds bfOffBits, the offset to the pixel data in little endian
        f.seek(10)
        pixel_offset = f.read(4)
        pixel_offset = int.from_bytes(pixel_offset, 'little')
        
        # Read byte 14 to 17 which hold the size of the DIB header in little endian
        palette_offset = f.read(4)
        palette_offset = int.from_bytes(palette_offset, 'little')
        print(palette_offset)
                
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
        #print(palette_list)
        
        # Get pixel data and count occurences of each palette entry
        pixel_data = f.read()
        pixel_counts = [0] * (number_of_colors)
        try:
            for byte in pixel_data:
                pixel_counts[byte] += 1
        except:
            print("Too many colors. Maybe the inFile isnt a pallete bmp")
            sys.exit(1)
            
    #print(pixel_counts)
    #print(len(pixel_counts))
    print("pixel_offset:", pixel_offset)
    print("palette_start:", palette_start)
    print("palette_size bytes:", palette_size)
    print("computed number_of_colors:", palette_size // 4)
    print("len(palette_list):", len(palette_list))
    print("number_of_colors passed in:", number_of_colors)
    
    
    return palette_list, number_of_colors, pixel_data, palette_start, header
        
# Duplicate the palette, this orders them like [OG,DUP,OG,DUP,...]
def duplicatePalette(original_palette, number_of_colors):    
    duplicate_palette = bytearray()
    for chunk in original_palette:
        duplicate_palette.extend(chunk)  # first copy of the 4-byte entry
        duplicate_palette.extend(chunk)
        
    #print(duplicate_palette)
    return bytes(duplicate_palette)
        
# Put the new palette into the image. Along with changing the palette you also have to change the file size at byte 2-5, palette offset at byte 10-13, colors used at byte 46-49
def embedPalette(duplicate_palette, pixel_data, header, palette_start):
    # Get new  palette offset
    duplicate_palette_offset = palette_start + len(duplicate_palette)
    header = header[:10] + duplicate_palette_offset.to_bytes(4, 'little') + header[14:]
    print(len(duplicate_palette))
    
    dib_header_size = int.from_bytes(header[14:18], 'little')
    if dib_header_size >= 40:
        bi_clr_used_offset = 14 + 32
        new_colors_used = len(duplicate_palette) // 4
        header[bi_clr_used_offset:bi_clr_used_offset+4] = new_colors_used.to_bytes(4, 'little')
    
    # Change indexes used in the image to account for new duplicates and get new file size
    new_pixels = bytes((original_index * 2) for original_index in pixel_data)
    file_size = duplicate_palette_offset + len(new_pixels)
    header[2:6] = file_size.to_bytes(4, 'little')
    
    new_file = header + duplicate_palette + new_pixels
    
    with open("out.bmp", "wb") as f:
        f.write(new_file)
      
def getLSB(byte):
    return byte & 1
      
def embedMessage(messageFile, pixel_data, location):
    # calculate size of messageFile and convert to binary
    # Convert messageFile to binary, prepend the size in binary to the binary message data
    # go through pixel data starting at location 
    # if message_binary[i] is 1
    #   pixel_data[location+j] is switched to its duplicate index
    # else nothing happens
    pass
    
def extractMessage(location):
    # go to location in sorce file and extract the lsb from the indexes used by the first 32 pixels. convert to decimal and that is the size of the message
    # Read the number of bytes you just calculated and extract the lsbs of the indexs referenced by the pixels you just read
    # convert to hex and write to a file
    pass
      
def usage():
    print("""
    Usage
    ------------------------------
    python palette_duplication.py operation sourceFile messageFile location
    
    python palette_duplication.py embed infile.bmp message.txt 5000
    
    A file named out.bmp will be created with the new image
    """)
      
def main():
    if len(sys.argv) < 4:
        usage()
        return 1
        
    operation = sys.argv[1]
    sourceFile = sys.argv[2]
    messageFile = sys.argv[3]
    location = sys.argv[4]
    
    if operation == 'embed':
        palette_list, number_of_colors, pixel_data, palette_start, header = processFile(sourceFile)
        duplicate_palette = duplicatePalette(palette_list, number_of_colors)
        embedPalette(duplicate_palette, pixel_data, header, palette_start)
        embedMessage(messageFile, pixel_data, location)
        
    if operation == 'extract':
        extractMessage(location)
        
main()