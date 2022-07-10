import struct

def float_to_bits(val):
    ''' Gets binary representation of a float
    
    Parameters
    ----------
    val : float
        input number
    
    Returns
    -------
    bytes
        binary representation of a float    
    '''
    s = struct.pack('>f', val)
    return struct.unpack('>l', s)[0]

def bits_to_float(val):
    ''' Gets float from bits
    
    Parameters
    ----------
    val : bytes
        input bits
    
    Returns
    -------
    float
        number generated from bits
    '''
    s = struct.pack('>l', val)
    return struct.unpack('>f', s)[0]

def byte_unpacker(val):
    ''' Unpacks bytes
    
    Parameters
    ----------
    val : bytes
        value to unpack
    
    Returns
    -------
    int
        unpacked number
    '''
    return (val[0] << 24) | (val[1] << 16) | (val[2] << 8) | (val[3])

def byte_packer(val):
    ''' Packs number
    
    Parameters
    ----------
    val : number
        value to pack
    
    Returns
    -------
    int
        packed number
    '''
    try:
        val = int(val)
    except ValueError:
        val = float_to_bits(float(val))

    return (val >> 24) & 0xFF, (val >> 16) & 0xFF, (
        val >> 8) & 0xFF, val & 0xFF