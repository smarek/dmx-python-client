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
        self.has_sync = True
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

    def obtain_sync(self) -> bool:
        # remove ISTRIP to distinguish from FFOOOO sequences in data from BREAK sequence
        self.set_iflag(istrip=True)
        # reset buffers
        self.ser.reset_input_buffer()
        self.ser.reset_output_buffer()
        # initial data
        data: bytes = b'\x00\x00\x00'
        # correct sync candidates
        candidate_positions = {}
        while True:
            newbyte: bytes = self.ser.read(1)
            if data[-1] == 0xFF and newbyte == b'\xFF':
                # 2 times 0xFF is single 0xFF
                continue
            # append
            data += newbyte
            for candidate in candidate_positions.keys():
                cut: int = 516
                cfrm: bytes = data[candidate:candidate + cut]
                if len(cfrm) == cut:
                    if cfrm[-3:] == b'\xFF\x00\x00':
                        self.has_sync = True
                        self.set_iflag(istrip=False)
                        return True
            if data[-3:] == b'\xFF\x00\x00':
                # we got break candidate
                candidate_positions[len(data)] = True
        # fallback
        return False

    def read_dmx_frame(self) -> (bytes, bool):
        frame: bytes = b''
        skipbyte: bool = False
        while len(frame) < 516:
            frame += self.ser.read(1)
            if not skipbyte and not self.has_istrip and frame[-2:] == b'\xFF\xFF':
                frame = frame[:-1]
                skipbyte = True
                continue
            skipbyte = False
        return frame, frame[-3:] == self.correct_break

    def run(self):
        counter: int = 0
        while True:
            # dmx[0] + 512 + break sequence = 516 bytes
            frame, sync_correct = self.read_dmx_frame()
            if not sync_correct:
                # notify callback
                self.callback.sync_lost()
                # obtain sync
                self.has_sync = self.obtain_sync()
                continue

            counter += 1
            if (counter % 50) == 0:
                self.ser.reset_input_buffer()
                counter = 0

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
