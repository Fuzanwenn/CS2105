#!/usr/bin/env python3
import os
import sys
import time
import zlib

from _socket import SHUT_RDWR
from socket import socket, AF_INET, SOCK_STREAM


class IceHelper:
    _debug_level = 1  # used to decide what level of debug messages need to be printed

    modes = [0, 1, 2]

    sever_packet_size = 1024  # num bytes
    client_packet_size = 64  # num bytes

    @classmethod
    def print_unreliability_mode_info(cls, mode_p=-1):
        def _helper(x):
            if x == 0:
                print(x, ": no error")
            elif x == 1:
                print(x, ": packet corruption/drop")
            elif x == 2:
                print(x, ": packet reorder")
            else:
                print("Fatal error: print_unreliability_mode_info")
                exit(-1)

        if mode_p == -1:
            for mode in cls.modes:
                _helper(mode)
        else:
            _helper(mode_p)

    @classmethod
    def get_n_bytes(cls, conn_socket, n):
        _data = cls.get_n_bytes_raw(conn_socket, n)
        if len(_data) < n:
            ret = ''
        else:
            ret = _data.decode()
        return ret

    @classmethod
    def get_integer_from_socket(cls, conn_socket):
        num_str = ''
        while True:
            c = cls.get_n_bytes(conn_socket, 1)
            if c == '_':
                break
            elif c == '':
                print("The connection terminated")
                return None
            else:
                num_str += c
        return int(num_str)

    @classmethod
    def get_n_bytes_raw(cls, conn_socket, n):
        _data = b''
        while len(_data) < n:
            try:
                _m = conn_socket.recv(n - len(_data))
                if not _m:
                    # client has disconnected
                    _data = b''
                    break
                _data += _m
            except OSError:
                break
        if len(_data) < n:
            _data = b''
        return _data


class ServerClient:
    ice_helper = IceHelper()
    packet_size_server = ice_helper.sever_packet_size
    packet_size_client = ice_helper.client_packet_size

    debug_level = 1

    def ice_debug(self, level, *arg):
        if level <= self.debug_level:
            for a in arg:
                print(a, end=' ')
            print()

    def ice_print(self, *arg):
        # ANSI colors
        _c = (
            "\033[0m",  # End of color
            "\033[36m",  # Cyan
            "\033[91m",  # Red
            "\033[35m",  # Magenta
        )

        if self.is_server:
            print(_c[1] + self.secret_student_id + ' Server:' + _c[0], end=' ')
        else:
            print(_c[2] + self.secret_student_id + ' Client:' + _c[0], end=' ')
        for a in arg:
            print(a, end=' ')
        print()

    def __init__(self, argv, is_server):
        if len(argv) < 6:
            print("missing command line parameter: ip_address port_number out_filename mode Student_id")
            self.ice_helper.print_unreliability_mode_info()
            exit(-1)

        i = 1
        self.ip_address = str(sys.argv[i])
        i += 1
        self.port_number = int(sys.argv[i])
        i += 1
        self.filename = str(sys.argv[i])
        i += 1
        mode = int(sys.argv[i])
        i += 1
        self.secret_student_id = str(sys.argv[i])

        self.is_server = is_server

        # open connection
        self.clientSocket = socket(AF_INET, SOCK_STREAM)
        self.clientSocket.connect((self.ip_address, self.port_number))

        # perform handshake
        self.handshake()

        # we can start transmitting the file now
        self.mode_error = False
        self.mode_reorder = False
        self.mode_reliable = False
        if mode == 0:
            self.mode_reliable = True
        elif mode == 1:
            self.mode_error = True
        elif mode == 2:
            self.mode_reorder = True
        else:
            print("ServerClient init: invalid mode")
            exit(-1)

    '''
    This is a complete code, no need to change the function!
    '''

    def handshake(self):
        # initial handshake is to pass the secret key
        # to which the server response with an ok
        # 'C' implies client
        message = 'STID_'
        if self.is_server:
            message += self.secret_student_id + '_' + 'S'
        else:
            message += self.secret_student_id + '_' + 'C'
        self.ice_print('sending: ' + message)
        self.clientSocket.sendall(message.encode())
        # wait to get a response '0_'
        self.ice_print("waiting for server response")
        while True:
            waiting_list_num = self.ice_helper.get_integer_from_socket(self.clientSocket)
            if waiting_list_num is None:
                exit(-1)
            self.ice_print("waiting_list_num: ", waiting_list_num)

            if waiting_list_num == 0:
                # we can start transmitting the file now
                break

    '''
    This is a complete code, no need to change the function!
    '''

    def send_file(self):
        if not self.is_server:
            self.ice_print("Client cannot send file")
            return

        if self.mode_reliable:
            self.send_file_reliable_channel()
        elif self.mode_reorder:
            self.send_file_reorder_channel()
        elif self.mode_error:
            self.send_file_error_channel()
        else:
            print("ServerClient send_file: invalid_mode")
            exit(-1)

    '''
    This is a complete code, no need to change the function!
    '''

    def recv_file(self):
        if self.is_server:
            self.ice_print("Server cannot receive file")
            return

        # time taken estimated
        tic = time.time()

        if self.mode_reliable:
            self.recv_file_reliable_channel()
        elif self.mode_reorder:
            self.recv_file_reorder_channel()
        elif self.mode_error:
            self.recv_file_error_channel()
        else:
            print("ServerClient recv_file: invalid_mode")
            exit(-1)

        elapsed_time = time.time() - tic
        print("\n\n Elapsed time: ", elapsed_time, " Sec\n\n")

    '''
    File reception over Channel with packet errors
    '''

    def recv_file_error_channel(self):
        # TODO
        error_message = b"0" * 64
        errorSeqList = []
        bodyList = []

        with open(self.filename, "wb") as f_out:
            recvFile = self.get_one_packet()
            i = 0
            while len(recvFile) != 0:
                body = recvFile[0:1020]
                curr_checksum = ServerClient.checksum(body)
                checksum = recvFile[1020:1024]
                print("a" + str(int.from_bytes(curr_checksum, "big")))
                print("b" + str(int.from_bytes(checksum, "big")))
                if curr_checksum != checksum:
                    errorSeqList.append(i)
                bodyList.append(body)
                i = i + 1
                self.clientSocket.settimeout(0.2)
                recvFile = self.get_one_packet()

            while True:
                if len(errorSeqList) == 0:
                    break
                self.clientSocket.send(error_message)
                recvFile = self.get_one_packet()
                i = 0
                while True:
                    if len(recvFile) == 0:
                        break
                    body = recvFile[0:1020]
                    curr_checksum = ServerClient.checksum(body)
                    checksum = recvFile[1020:1024]
                    if curr_checksum == checksum and (i in errorSeqList):
                        bodyList[i] = body
                        errorSeqList.remove(i)

                    i = i + 1
                    recvFile = self.get_one_packet()

            length = int.from_bytes(bodyList[len(bodyList) - 1][0:4], "big")
            reminder = bodyList[len(bodyList) - 2][0:length]
            m = 0
            while m < len(bodyList) - 2:
                f_out.write(bodyList[m])
                f_out.flush()
                m = m + 1
            f_out.write(reminder)
            f_out.flush()

    '''
    File transmission over Channel with packet errors
    '''

    def send_file_error_channel(self):
        # TODO
        file_size = os.path.getsize(self.filename)
        times = int(file_size / 1020)
        reminder = int(file_size % 1020)
        bodyList = []
        i = 0
        with open(self.filename, "rb") as f_in:
            while i < times:
                # read the bytes from the file
                bytes_read = f_in.read(1020)
                checksum = ServerClient.checksum(bytes_read)
                bytes_read = bytes_read + checksum
                bodyList.append(bytes_read)
                self.clientSocket.send(bytes_read)
                i = i + 1

            if reminder != 0:
                reminder_read = f_in.read(reminder)
                reminder_read = reminder_read + b"0" * (1020 - reminder)
                checksum1_int = zlib.crc32(reminder_read)
                checksum1 = checksum1_int.to_bytes(4, "big")
                reminder_read = reminder_read + checksum1
                bodyList.append(reminder_read)
                self.clientSocket.send(reminder_read)

            bytes_length = reminder.to_bytes(4, "big")
            bytes_length = bytes_length + b"0" * 1016
            checksum2 = ServerClient.checksum(bytes_length)
            # print("length " + str(int.from_bytes(checksum2, "big")))
            bytes_length = bytes_length + checksum2
            bodyList.append(bytes_length)
            self.clientSocket.send(bytes_length)

            recvMessage = self.get_one_packet()
            while len(recvMessage) != 0:
                for p in bodyList:
                    self.clientSocket.send(p)
                recvMessage = self.get_one_packet()
            f_in.flush()

    '''
    File reception over Channel which Reorders packets
    '''

    def recv_file_reorder_channel(self):
        # TODO
        with open(self.filename, "wb") as f_out:
            recvFile = self.get_one_packet()
            seqList = []
            while len(recvFile) != 0:
                seq = int.from_bytes(recvFile[1020:1024], "big")
                body = recvFile[0:1020]
                seqList.append([seq, body])
                recvFile = self.get_one_packet()

            seqList.sort(key=lambda p: p[0])

            i = 0
            while i < len(seqList) - 2:
                curr = seqList[i][1]
                i = i + 1
                f_out.write(curr)
                f_out.flush()
            length = int.from_bytes(seqList[len(seqList) - 1][1][0:4], "big")
            curr = seqList[i][1][0:length]
            f_out.write(curr)
            f_out.flush()

    '''
    File transmission over Channel which Reorders packets
    '''

    def send_file_reorder_channel(self):
        # TODO
        file_size = os.path.getsize(self.filename)
        times = int(file_size / 1020)
        reminder = int(file_size % 1020)
        i = 1
        with open(self.filename, "rb") as f_in:
            while i < times + 1:
                # read the bytes from the file
                bytes_read = f_in.read(1020)
                seq = i.to_bytes(4, "big")
                bytes_read = bytes_read + seq
                self.clientSocket.send(bytes_read)
                i = i + 1

            if reminder != 0:
                reminder_read = f_in.read(reminder)
                reminder_read = reminder_read + b"0" * (1020 - reminder)
                seq = i.to_bytes(4, "big")
                reminder_read = reminder_read + seq
                self.clientSocket.send(reminder_read)

            reminder_length = reminder.to_bytes(4, "big")
            reminder_length = reminder_length + b"0" * 1016
            i = i + 1
            seq = i.to_bytes(4, "big")
            reminder_length = reminder_length + seq
            self.clientSocket.send(reminder_length)
            f_in.flush()

    '''
    File reception over Reliable Channel
    '''

    def recv_file_reliable_channel(self):
        # TODO
        with open(self.filename, "wb") as f_out:
            recvFile = self.get_one_packet()
            bytes_list = []
            while len(recvFile) != 0:
                bytes_list.append(recvFile)
                # print(recvFile)
                recvFile = self.get_one_packet()
            length = int.from_bytes(bytes_list[len(bytes_list) - 1][0:4], "big")
            # print(length)
            bytes_list[len(bytes_list) - 2] = bytes_list[len(bytes_list) - 2][0:length]
            # print(bytes_list[len(bytes_list) - 2])
            i = 0
            while i < len(bytes_list) - 1:
                # print(i)
                f_out.write(bytes_list[i])
                f_out.flush()
                i = i + 1

    '''
    File transmission over Reliable Channel
    '''

    def send_file_reliable_channel(self):
        # TODO
        file_size = os.path.getsize(self.filename)
        times = int(file_size / 1024)
        reminder = int(file_size % 1024)
        i = 1
        with open(self.filename, "rb") as f_in:
            while i < times + 1:
                # read the bytes from the file
                bytes_read = f_in.read(1024)
                self.clientSocket.send(bytes_read)
                # print(i)
                i = i + 1
            if reminder != 0:
                bytes_read = f_in.read(reminder)
                bytes_read = bytes_read + b"0" * (1024 - reminder)
                # print(bytes_read)
                self.clientSocket.send(bytes_read)
            bytes_length = reminder.to_bytes(4, "big")
            # print(bytes_length)
            # print(reminder)
            bytes_length = bytes_length + b"0" * 1020
            self.clientSocket.send(bytes_length)
            f_in.flush()

    # ######## Helper #############
    # This is a complete code, no need to change the function!
    def get_one_packet(self):
        # server receives packet from client and vice versa
        if self.is_server:
            packet = self.ice_helper.get_n_bytes_raw(self.clientSocket, self.packet_size_client)
        else:
            packet = self.ice_helper.get_n_bytes_raw(self.clientSocket, self.packet_size_server)

        return packet

    @staticmethod
    # This is a complete code, no need to change the function!
    def _print_data_hex(data, delay=0.0):
        print('-----', len(data), '-------')
        print(data.hex())
        time.sleep(delay)

    @staticmethod
    def checksum(byte):
        result = zlib.crc32(byte)
        return result.to_bytes(4, "big")

    # This is a complete code, no need to change the function!
    def terminate(self):
        try:
            self.clientSocket.shutdown(SHUT_RDWR)
            self.clientSocket.close()
        except OSError:
            # the socket may be already closed
            pass


def main():
    server_client = ServerClient(sys.argv, is_server=True)
    # receive files
    server_client.send_file()
    server_client.terminate()


if __name__ == "__main__":
    main()
