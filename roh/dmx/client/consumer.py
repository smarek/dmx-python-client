import os
import termios

import serial
from serial import PARITY_NONE, STOPBITS_TWO


class Consumer:
    def __init__(self, sport: str):
        self.ser = serial.Serial(
            sport,
            baudrate=250000,
            parity=PARITY_NONE,
            stopbits=STOPBITS_TWO,
            xonxoff=True,
        )

        self.fd = self.ser.fd
        # self.fd = os.open(sport, os.O_RDWR | os.O_NOCTTY | os.O_NONBLOCK)

        iflag, oflag, cflag, lflag, ispeed, ospeed, cc = termios.tcgetattr(self.fd)
        iflag |= termios.PARMRK
        iflag &= ~termios.IGNBRK
        termios.tcsetattr(self.fd, termios.TCSANOW, [iflag, oflag, cflag, lflag, ispeed, ospeed, cc])

    def get_sync(self):
        print('GETTING SYNC')
        breakbytes = b'\xFF\x00\x00'

        while True:
            b: bytes = os.read(self.fd, 3)
            if b == breakbytes:
                print("SYNC")
                break
            print(b.hex(), end='', flush=True)

    def run(self):
        # self.get_sync()
        correct_tail = b'\xFF\x00\x00'

        while True:
            b: bytes = self.ser.read(516)
            if b[513:] != correct_tail:
                print("tail %s" % b[513:].hex())
                self.get_sync()
                continue

            for i in range(0, 513):
                if b[i] != 0:
                    print("idx:%d val:%d" % (i, b[i]))


if __name__ == '__main__':
    c: Consumer = Consumer('/dev/ttyUSB0')
    c.run()
