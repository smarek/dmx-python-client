# DMX-512 python serial client

Per limitation of pySerial this utility helps with properly setting the serial port on POSIX/LINUX and detecting
SYNC/BREAK within the stream of data

## Usage

```python
from roh.dmx.client.dmx_client import DmxClient
from roh.dmx.client.dmx_client_callback import DmxClientCallback
from typing import Dict

# define callback, you can override even just one method, for example data_received

class MyDmxCallback(DmxClientCallback):
    """
    Example implementation of all available callback methods
    """
    def sync_lost(self) -> None:
        print("SYNC LOST")

    def sync_found(self) -> None:
        print("SYNC FOUND")

    def data_received(self, monitored_data: Dict[int, int]) -> None:
        print("VALID MONITORED DATA: %s" % monitored_data)

    def full_data_received(self, data: bytes) -> None:
        pass

# use client with /dev/ttyUSB0 port and monitor dmx address no. 1 for values
c: DmxClient = DmxClient('/dev/ttyUSB0', [1], MyDmxCallback())
c.run()
```

## References

  - https://github.com/pyserial/pyserial/issues/539 - Issue about pySerial limitation when consuming DMX-512
  - [Using a Raspberry Pi as a PC-DMX interface (Florian Edelmann) - PDF](https://www.mnm-team.org/pub/Fopras/edel17/PDF-Version/edel17.pdf)
  - https://man7.org/linux/man-pages/man3/termios.3.html - documentation of PARMRK, IGNBRK and BRKINT settings of virtual terminal