import os
import termios

import serial
from serial import PARITY_NONE, STOPBITS_TWO


class Consumer:
    def __init__(self):
        pass

    def run(self, sport: str):
        ser = serial.Serial(
            sport,
            baudrate=250000,
            parity=PARITY_NONE,
            stopbits=STOPBITS_TWO,
            xonxoff=True,
        )

        fd = os.open(sport,  os.O_RDWR | os.O_NOCTTY | os.O_NONBLOCK)
        iflag, oflag, cflag, lflag, ispeed, ospeed, cc = termios.tcgetattr(fd)
        iflag |= termios.PARMRK
        iflag &= ~termios.IGNBRK
        termios.tcsetattr(fd, termios.TCSANOW, [iflag, oflag, cflag, lflag, ispeed, ospeed, cc])
        # termios.tcdrain(ser.fd)

        breakbytes = b'\x00\xFF\x00'

        while True:
            b: bytes = os.read(fd, 3)
            if b == breakbytes:
                print("SYNC")
                break
            print(b.hex(), end='', flush=True)

        while True:
            b: bytes = ser.read(516)
            for i in range(0, 514):
                if b[i] != 0:
                    print("%d val %d" % (i, b[i]))




if __name__ == '__main__':
    c: Consumer = Consumer()
    c.run('/dev/ttyUSB0')
