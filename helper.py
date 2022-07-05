import struct

def float_to_bits(val):
    s = struct.pack('>f', val)
    return struct.unpack('>l', s)[0]

def bits_to_float(val):
    s = struct.pack('>l', val)
    return struct.unpack('>f', s)[0]

def byte_unpacker(byte_list):
    return (byte_list[0] << 24) | (byte_list[1] << 16) | (byte_list[2] << 8) | (byte_list[3])

def byte_packer(value_to_pack):
    try:
        value_to_pack = int(value_to_pack)
    except ValueError:
        value_to_pack = float_to_bits(float(value_to_pack))

    return (value_to_pack >> 24) & 0xFF, (value_to_pack >> 16) & 0xFF, (
        value_to_pack >> 8) & 0xFF, value_to_pack & 0xFF