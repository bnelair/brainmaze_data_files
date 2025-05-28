
from zlib import crc32

def get_crc32(fid):
    """
    Calculate the CRC32 checksum of a file.

    Args:
        fid (str): The path to the file.

    Returns:
        int: The CRC32 checksum of the file.
    """
    with open(fid, 'rb') as f:
        crc_val = 0
        while chunk := f.read(65536):  # Read in 64 KB chunks
            crc_val = crc32(chunk, crc_val)
    return crc_val

__all__ = [
    "get_crc32"
]
