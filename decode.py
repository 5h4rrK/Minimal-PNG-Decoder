import zlib 
import numpy as np
from PIL import Image

def read_file(file_name): return open(file_name,"rb")

def read_Png_Signature(f): return f.read(8) # 8 bytes b'\x89\x50\x4e\x47\x0d\x0a\x1a\x0a'

def set_IDAT_Attributes(data):
    global HEIGHT, WIDTH ,BIT_DEPTH, COLOR_TYPE , COMPRESSION_TYPE, FILTER_METHOD, INTERLACE_METHOD, no_of_planes , scanline_data
    WIDTH = to_Int(data[:4])
    HEIGHT = to_Int(data[4:8])
    BIT_DEPTH = to_Int(data[8:9])
    COLOR_TYPE = to_Int(data[9:10])
    COMPRESSION_TYPE = to_Int(data[10:11])
    FILTER_METHOD = to_Int(data[11:12])
    INTERLACE_METHOD = to_Int(data[12:13])

    if(COLOR_TYPE != 6 and BIT_DEPTH != 8 and FILTER_METHOD != 0 and INTERLACE_METHOD != 0 and COMPRESSION_TYPE != 0): 
        print("IDAT Attributes Error")
        exit(1)
    
    if(COLOR_TYPE == 6): no_of_planes  = 4 
    elif (COLOR_TYPE == 2): no_of_planes  = 3

    scanline_data = no_of_planes  * WIDTH

    return HEIGHT, WIDTH ,BIT_DEPTH, COLOR_TYPE , COMPRESSION_TYPE, FILTER_METHOD, INTERLACE_METHOD, no_of_planes , scanline_data


def zlib_decompressIDAT(comp_data):
    return zlib.decompress(comp_data)


def to_Int(r): return int.from_bytes(r,byteorder='big', signed=False)

def read_chunk_part(file):
    chunk_size, chunk_name = file.read(4) , file.read(4)
    chunk_data = file.read(to_Int(chunk_size))
    chunk_crc = file.read(4)
    return chunk_size, chunk_name , chunk_data, chunk_crc

def read_chunk(file, func = read_chunk_part, IDAT_BUFFER = bytes()):
    _ = func(file)
    while _[1] != b'IEND':
        if(_[1] == b'IHDR'): set_IDAT_Attributes(_[2])
        elif (_[1] == b'IDAT'): IDAT_BUFFER += _[2]
        _ = func(file)
    return IDAT_BUFFER

def paeth_Predictor(a,b,c):    #  |  | c | b |  |
#                                 |  | a | x |  |
    p = a + b - c
    d_a = abs(p-a)
    d_b = abs(p-b)
    d_c = abs(p-c)

    if(d_a <= d_b and d_a <= d_c): return a 
    elif (d_b <= d_b): return b 
    else: return c 

def recon_A(r,c): 
    if(c >= no_of_planes ): return Recon[r * scanline_data + c - no_of_planes ]
    else : return 0

def recon_B(r,c): 
    if(r > 0): return Recon[(r-1) * scanline_data +c]
    else: return 0

def recon_C(r,c):  
    if(r > 0 and c >= no_of_planes ): return Recon[(r-1) * scanline_data + c -no_of_planes ]
    else : return 0

def decompressIDAT():
    i = 0
    pixel_val = 0
    for r in range(HEIGHT):
        filter_type = IDAT_BUFFER[i]
        i += 1
        for c in range(scanline_data):
            idat_val = IDAT_BUFFER[i]
            i += 1
            if(filter_type == 0): pixel_val = idat_val                  # None
            elif(filter_type == 1): pixel_val = idat_val + recon_A(r,c) # Sub
            elif(filter_type == 2): pixel_val = idat_val + recon_B(r,c) # Up 
            elif(filter_type == 3): pixel_val = idat_val + (recon_A(r,c) + recon_B(r,c))//2 # Average
            elif(filter_type == 4): pixel_val = idat_val + paeth_Predictor(recon_A(r,c), recon_B(r,c),recon_C(r,c)) # Paeth
            else:
                raise Exception("Unkown Filter  Type --> ", filter_type)

            Recon.append(pixel_val & 0xff) # pixel_val = pixel_val % 256

def save_Image():
    Image.fromarray(np.array(Recon).reshape(HEIGHT,WIDTH,no_of_planes ).astype(np.uint8)).save("decoded/decoded.png")

def main():
    file = read_file("images/sample.png")
    assert read_Png_Signature(file) == b'\x89\x50\x4e\x47\x0d\x0a\x1a\x0a'
    global IDAT_BUFFER
    IDAT_BUFFER = read_chunk(file)
    global Recon 
    Recon = []
    IDAT_BUFFER = zlib_decompressIDAT(IDAT_BUFFER)
    decompressIDAT()
    save_Image()

if __name__ == "__main__" : 
    main()
