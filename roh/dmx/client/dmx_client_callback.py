from typing import Dict


class DmxClientCallback:
    """
    Callback class for roh.dmx.client.DmxClient
    """

    def sync_lost(self) -> None:
        """
        This callback is invoked every time sync is lost, can be used to monitor stability of connection
        :return:
        """
        pass

    def sync_found(self) -> None:
        """
        This callback is invoked once the sync is achieved, can be used to monitor stability of connection
        :return:
        """
        pass

    def data_received(self, monitored_data: Dict[int, int]) -> None:
        """
        If monitored addresses were set, this callback receives only monitored data (even if not changed)
        :param monitored_data:
        :return:
        """
        pass

    def full_data_received(self, data: bytes) -> None:
        """
        Every time new packet is received and is valid, this callback gets invoked, getting all 512 bytes of DMX data
        :param data:
        :return:
        """
        pass


class DummyDmxClientCallback(DmxClientCallback):
    """
    Dummy (printing) implementation of DmxClientCallback
    """

    def sync_lost(self) -> None:
        print("SYNC LOST")

    def sync_found(self) -> None:
        print("SYNC FOUND")

    def data_received(self, monitored_data: Dict[int, int]) -> None:
        print("VALID MONITORED DATA: %s" % monitored_data)

    def full_data_received(self, data: bytes) -> None:
        print("FULL DMX512 PACKET RECEIVED")
