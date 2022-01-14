import os
import termios
from typing import List, Optional, Dict

import serial
from serial import PARITY_NONE, STOPBITS_TWO

from roh.dmx.client.dmx_client_callback import DmxClientCallback, DummyDmxClientCallback


class DmxClient:
    def __init__(
            self,
            serial_port: str,
            monitored_addresses: List[int],
            callback: Optional[DmxClientCallback] = None
    ):
        """

        :param serial_port: path to serial port, such as /dev/ttyUSB0
        :param monitored_addresses: list of addresses which will be monitored and sent to callback, or empty list
        :param callback: implementation of callback, if none provided
        """
        self.correct_break = b'\xFF\x00\x00'
        self.callback: Optional[DmxClientCallback] = callback if callback else DummyDmxClientCallback()
        self.monitored_addresses: List[int] = monitored_addresses if isinstance(monitored_addresses, list) else []

        # init serial.Serial first, so the port is configured with default attributes in library
        # before setting PARMRK
        self.ser = serial.Serial(
            serial_port,
            baudrate=250000,
            parity=PARITY_NONE,
            stopbits=STOPBITS_TWO,
            xonxoff=False,
            rtscts=True,
            dsrdtr=True
        )

        # hook serial.Serial file-descriptor as our own
        self.fd = self.ser.fd

        # get current attributes, set originaly by serial.Serial
        iflag, oflag, cflag, lflag, ispeed, ospeed, cc = termios.tcgetattr(self.fd)
        # set flag PARMRK (Parity Mark) and unset IGNBRK (Ignore Break)
        # Causes BREAK event to be read as 3-bytes \377\0\0 (aka FF0000) to be able to detect sync
        iflag |= termios.PARMRK
        iflag &= ~termios.IGNBRK
        # set modified params to serial port
        termios.tcsetattr(self.fd, termios.TCSANOW, [iflag, oflag, cflag, lflag, ispeed, ospeed, cc])

    def get_sync(self):
        # reset input buffer, so we don't have to deal with historic buffer, which might be quite huge
        self.ser.reset_input_buffer()
        while True:
            # continuously read up to 3 bytes from input buffer until sync is found
            b: bytes = os.read(self.fd, 1)
            if b == b'\xFF':
                b = os.read(self.fd, 2)
                if b == b'\x00\x00':
                    self.callback.sync_found()
                    break

    def run(self):
        while True:
            # from SYNC/BREAK pattern it's [0x00] (dmx index 0), then 512 addressed value bytes and 3 sync/break bytes
            # totaling 516 bytes
            b: bytes = self.ser.read(516)
            if b[513:] != self.correct_break:
                # notify callback of sync being lost
                self.callback.sync_lost()
                # try to sync to stream
                self.get_sync()
                continue

            # Provide first 512 bytes (full dmx512 packet) to callback
            self.callback.full_data_received(data=b[:512])

            if len(self.monitored_addresses) > 0:
                monitored: Dict[int, int] = {}
                # walk monitored addresses and read out values only for those
                for i in self.monitored_addresses:
                    monitored[i] = b[i]
                # notify callback of monitored addresses
                self.callback.data_received(monitored_data=monitored)


if __name__ == '__main__':
    # prototype watching only dmx address 1
    try:
        c: DmxClient = DmxClient('/dev/ttyUSB0', [1], DummyDmxClientCallback())
        c.run()
    except KeyboardInterrupt:
        print("interrupted by keyboard")
