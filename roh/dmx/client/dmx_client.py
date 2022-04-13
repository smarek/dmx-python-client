import termios
from typing import List, Optional, Dict

import serial
from serial import PARITY_NONE, STOPBITS_TWO

import time

from roh.dmx.client.dmx_client_callback import DmxClientCallback, DummyDmxClientCallback


class DmxClient:
    def __init__(
            self,
            serial_port: str,
            monitored_addresses: List[int],
            callback: Optional[DmxClientCallback] = None,
    ):
        """

        :param serial_port: path to serial port, such as /dev/ttyUSB0
        :param monitored_addresses: list of addresses which will be monitored and sent to callback, or empty list
        :param callback: implementation of callback, if none provided
        """
        self.correct_break = b'\xFF\x00\x00'
        self.has_sync = True
        self.has_lost_sync = False
        self.has_istrip = False
        self.callback: Optional[DmxClientCallback] = callback if callback else DummyDmxClientCallback()
        self.monitored_addresses: List[int] = monitored_addresses if isinstance(monitored_addresses, list) else []

        # init serial.Serial first, so the port is configured with default attributes in library
        # before setting PARMRK
        self.ser = serial.Serial(
            serial_port,
            baudrate=250000,
            parity=PARITY_NONE,
            stopbits=STOPBITS_TWO,
            xonxoff=True,
            rtscts=False,
            dsrdtr=False
        )

        # hook serial.Serial file-descriptor as our own
        self.fd = self.ser.fd
        self.set_iflag(istrip=False)

    def set_iflag(self, istrip: bool):
        # get current attributes, set originaly by serial.Serial
        iflag, oflag, cflag, lflag, ispeed, ospeed, cc = termios.tcgetattr(self.fd)
        # set flag PARMRK (Parity Mark) and unset IGNBRK (Ignore Break)
        # Causes BREAK event to be read as 3-bytes \377\0\0 (aka FF0000) to be able to detect sync
        iflag |= termios.PARMRK
        if istrip:
            iflag |= termios.ISTRIP
        iflag &= ~(termios.IGNBRK | termios.IGNPAR | termios.BRKINT | termios.INPCK | termios.IGNPAR)
        if not istrip:
            iflag &= ~termios.ISTRIP
        # set modified params to serial port
        termios.tcsetattr(self.fd, termios.TCSANOW, [iflag, oflag, cflag, lflag, ispeed, ospeed, cc])
        # indicate
        self.has_istrip = istrip

    def read_serial_data(self, length=516):
        bdata: bytes = b''
        odd: bytes = b''
        # read data up until break
        while (len(odd) + len(bdata)) < (length - 3):
            bdata += (odd + self.ser.read(length - len(bdata) - len(odd) - 3)).replace(b'\xFF\xFF', b'\xFF')
            if len(bdata) % 2:
                bdata, odd = bdata[:-1], bdata[-1:]
            else:
                odd = b''
        # read break sequence
        bdata += (odd + self.ser.read(3)).replace(b'\xFF\xFF', b'\xFF')
        bdata += self.ser.read(length - len(bdata))
        #if self.has_lost_sync:
        #    print("no sync data", len(bdata), bdata.hex())
        assert len(bdata) == length, f"mismatch expected {length} retrieved {len(bdata)} odd {odd.hex()} bdata {bdata.hex()}"
        return bdata, bdata[-3:] == b'\xFF\x00\x00'

    def obtain_sync(self) -> bool:
        # remove ISTRIP to distinguish from FFOOOO sequences in data from BREAK sequence
        self.set_iflag(istrip=True)
        # reset buffers
        self.ser.reset_input_buffer()
        # buffer
        bdata = b''
        parts = []
        while True:
            bdata, is_correct_dmx_frame = self.read_serial_data(516)
            parts = bdata.split(b'\xFF')
            if len(parts) == 2:
                break
        assert len(parts) == 2, f"in 516 bytes there should not be more than 2 parts, got {len(parts)} in {bdata.hex()} got {bdata.split(bytes.fromhex('FF'))}"
        # balance out buffer/position difference
        bdata, is_correct_dmx_frame = self.read_serial_data(518 - len(parts[1]))
        bdata, is_correct_dmx_frame = self.read_serial_data()
        self.set_iflag(istrip=False)
        return True

    def run(self):
        counter: int = 0
        while True:
            # dmx[0] + 512 + break sequence = 516 bytes
            frame, sync_correct = self.read_serial_data()
            if not sync_correct:
                # notify callback
                self.has_lost_sync = True
                if self.has_sync:
                    self.callback.sync_lost()
                # obtain sync
                self.has_sync = self.obtain_sync()
                continue

            if self.has_lost_sync:
                self.callback.sync_found()
                self.has_lost_sync = False

            self.callback.full_data_received(data=frame[1:513])

            if len(self.monitored_addresses) > 0:
                monitored: Dict[int, int] = {}
                for i in self.monitored_addresses:
                    monitored[i] = frame[i]
                self.callback.data_received(monitored_data=monitored)


if __name__ == '__main__':
    # prototype watching only dmx address 1
    c: DmxClient = DmxClient('/dev/serial0', [1], DummyDmxClientCallback())
    c.run()
