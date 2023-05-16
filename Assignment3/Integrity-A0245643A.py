# !/usr/bin/env python3
import os
import sys
from Cryptodome.Hash import SHA256

if len(sys.argv) < 3:
    print("Usage: python3 ", os.path.basename(__file__), "key_file_name document_file_name")
    sys.exit()

key_file_name   = sys.argv[1]
file_name       = sys.argv[2]

# get the authentication key from the file
# TODO
with open(key_file_name, "rb") as mac_file:
    mac_key = mac_file.read()
mac_file.close()

# read the input file
with open(file_name, "rb") as data_file:
    mac_code = data_file.read(32)
    data = data_file.read()
data_file.close()

# First 32 bytes is the message authentication code
# TODO
mac_from_file = mac_code

# Use the remaining file content to generate the message authentication code
# TODO
h = SHA256.new(data)
h.update(mac_key)
mac_generated = h.digest()

if mac_from_file == mac_generated:
    print ('yes')
else:
    print ('no')
