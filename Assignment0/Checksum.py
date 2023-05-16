import zlib
import sys


def main():
    with open(sys.argv[1], "rb") as f:
        byte = f.read()
    print(zlib.crc32(byte))


if __name__ == '__main__':
    main()
