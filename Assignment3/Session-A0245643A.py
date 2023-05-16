import os.path
import sys
from socket import socket, AF_INET, SOCK_STREAM

from Cryptodome.PublicKey import RSA
from Cryptodome.Cipher import PKCS1_v1_5, AES

rsa_key_len = int(2048 / 8)


def load_rsa_key(f_name_key="test/rsa_key.bin"):
    """
    load the public RSA key
    :return: RSA key
    """
    # TODO
    with open(f_name_key, "rb") as file:
        key = RSA.importKey(file.read())
    file.close()
    return key


# connect ot the server
if len(sys.argv) < 5:
    print("Usage: python3 ", os.path.basename(__file__), "key_file_name data_file_name hostname/IP port")
else:
    key_file_name = sys.argv[1]
    data_file_name = sys.argv[2]
    serverName = sys.argv[3]
    serverPort = int(sys.argv[4])
    print(serverName, serverPort)

    rsa_key = load_rsa_key()

    # connect to the server
    clientSocket = socket(AF_INET, SOCK_STREAM)
    clientSocket.connect((serverName, serverPort))

    modifiedSentence = clientSocket.recv(256)

    # get the session key
    # first 256 bytes sent by the server is the RSA encrypted session key
    cipher_rsa = PKCS1_v1_5.new(rsa_key)
    # TODO
    sentinel = b'1' * 16
    ciphertext = modifiedSentence
    session_key = cipher_rsa.decrypt(ciphertext, sentinel)
    # write the session key to the file "key_file_name"
    with open(key_file_name, "wb") as key_file:
        key_file.write(session_key)
    key_file.close()

    # TODO
    # get the data from server
    # TODO
    # decrypt the data in blocks of size 16B
    # size of data from the server is guaranteed to be a multiple of 16B
    # TODO
    cipher_aes = AES.new(session_key, AES.MODE_ECB)
    with open(data_file_name, "wb") as data_file:
        while True:
            data = clientSocket.recv(16)
            if not data:
                break
            plaintext = cipher_aes.decrypt(data)
            data_file.write(plaintext)
