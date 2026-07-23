"""Compare .mo file entries for the two problematic strings"""
import struct
import os

mo_path = os.path.join(r'e:\Python\PROJECT\website\locale', 'fr', 'LC_MESSAGES', 'django.mo')

with open(mo_path, 'rb') as f:
    data = f.read()

# Parse the .mo file header
magic = struct.unpack('@I', data[0:4])[0]
print(f"Magic: {hex(magic)}")

revision = struct.unpack('@I', data[4:8])[0]
print(f"Revision: {revision}")

nstrings = struct.unpack('@I', data[8:12])[0]
print(f"Number of strings: {nstrings}")

orig_table_offset = struct.unpack('@I', data[12:16])[0]
trans_table_offset = struct.unpack('@I', data[16:20])[0]
hash_table_size = struct.unpack('@I', data[20:24])[0]
hash_table_offset = struct.unpack('@I', data[24:28])[0]

print(f"Orig table offset: {orig_table_offset}")
print(f"Trans table offset: {trans_table_offset}")
print(f"Hash table size: {hash_table_size}")
print(f"Hash table offset: {hash_table_offset}")

# Read original strings (msgid)
print("\nSearching for problematic msgids...")
o = orig_table_offset
for i in range(min(nstrings, 115)):
    length = struct.unpack('@I', data[o:o+4])[0]
    offset = struct.unpack('@I', data[o+4:o+8])[0]
    msgid = data[offset:offset+length].decode('utf-8', errors='replace')
    if 'Higher light' in msgid or 'Proprietary glass' in msgid or 'we\u2019ve' in msgid:
        print(f"  Entry {i}: length={length}, msgid={repr(msgid[:60])}")
    o += 8

# Check if hash table has valid entries
print(f"\nHash table entries:")
h = hash_table_offset
hash_nonzero = 0
for i in range(hash_table_size):
    val = struct.unpack('@I', data[h:h+4])[0]
    if val != 0:
        hash_nonzero += 1
print(f"  Non-zero hash entries: {hash_nonzero}/{hash_table_size}")
