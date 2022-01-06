import serial
from serial import PARITY_NONE, STOPBITS_TWO


class Consumer:
    """

    """

    def run(self, sport: str):
        p = serial.Serial(
            port=sport,
            baudrate=250000,
            parity=PARITY_NONE,
            stopbits=STOPBITS_TWO,
        )
        nb = bytes([0])
        c = 0
        while True:
            r = p.read()
            if r == nb:
                c += 1
                continue
            if r == bytes([0xA7]):
                print("stop at %d" % (c-7))
                c = 7
            print("%d:%s" % (c, r.hex()), flush=True)
            c += 1


if __name__ == '__main__':
    c: Consumer = Consumer()
    c.run('/dev/ttyUSB0')
