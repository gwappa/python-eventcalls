#
# MIT License
#
# Copyright (c) 2019 Keisuke Sehara
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.
#

from . import EventSource as _EventSource
import socket as _socket
import threading as _threading

class InputStream(_EventSource):
    """an EventSource that keeps reading from the underlying endpoint.
    this default implementation cancels the reading by closing the endpoint.

    subclasses are supposed to override the following methods:
    - `read_single()`: reads a message (can be in any form) and returns it.
    - `close()`: closes the endpoint.
    """
    DEFAULT_TIMEOUT_SEC = None

    def __init__(self):
        super().__init__()
        self.__canceled = _threading.Event()

    def __iter__(self):
        try:
            while True:
                yield self.read_single()
        except OSError:
            if not self.__canceled.is_set():
                raise

    def cancel(self):
        self.__canceled.set()
        # close the endpoint anyway
        try:
            self.close()
        except OSError:
            pass

class DatagramReader(InputStream):
    """an EventSource that keeps reading from the paired UDP endpoint.
    the endpoint can be either listening socket, or the one used for
    sending packets.

    its event is the return value of socket.recv i.e. in the form of
    (bytes, address).

    the size of the buffer can be changed using the `buffersize` parameter
    on initialization.
    """

    @classmethod
    def bind(cls, port, buffersize=1024):
        """creates a Reader using a listening port
        bound to the specified host and port."""
        endpoint = _socket.socket(_socket.AF_INET, _socket.SOCK_DGRAM, _socket.IPPROTO_UDP)
        endpoint.setsockopt(_socket.SOL_SOCKET, _socket.SO_REUSEADDR, 1)
        endpoint.settimeout(cls.DEFAULT_TIMEOUT_SEC)
        endpoint.bind(('localhost', port))
        return cls(endpoint, buffersize=buffersize)

    def __init__(self, endpoint, buffersize=1024):
        """endpoint: datagram port to read from"""
        super().__init__()
        self.__endpoint = endpoint
        self.buffersize = 1024

    def read_single(self):
        """calls recvfrom() using the attached endpoint."""
        return self.__endpoint.recvfrom(self.buffersize)

    def close(self):
        self.__endpoint.close()

try:
    import serial as _serial

    class SerialReader(_EventSource):
        """an event source that keeps reading from the paired serial port.
        this class is available only when PySerial (or a `serial` module) is
        properly installed.
        """
        pass
except ImportError:
    pass
