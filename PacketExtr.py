import sys


def main():
    stream = b''
    while True:
        curr = sys.stdin.buffer.read1(1)
        if curr == b'':
            break
        if curr == b'B':
            value = int(stream[6:])
            data = sys.stdin.buffer.read1(value)
            sys.stdout.buffer.write(data)
            sys.stdout.buffer.flush()
            stream = b''
        else:
            stream = stream + curr


if __name__ == '__main__':
    main()
