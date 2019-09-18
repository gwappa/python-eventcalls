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
import selectors as _selectors

class StreamIsClosed(OSError):
    def __init__(self, msg):
        super().__init__(msg)

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

    def __getattr__(self, name):
        if name == 'canceled':
            return self.__canceled.is_set()
        else:
            return super().__getattr__(name)

    def __iter__(self):
        try:
            while True:
                yield self.read_single()
        except:
            if not self.canceled:
                raise

    def cancel(self):
        self.__canceled.set()
        # close the endpoint anyway
        try:
            self.close()
        except OSError:
            pass

class DatagramIO(InputStream):
    """an EventSource that keeps reading from the paired UDP endpoint.
    the endpoint can be either listening socket, or the one used for
    sending packets.

    its event is the return value of socket.recv i.e. in the form of
    (bytes, address).

    the size of the buffer can be changed using the `buffersize` parameter
    on initialization.
    """
    timeout = .5 # 0.5-sec timeout for `select` call

    @classmethod
    def bind(cls, port, buffersize=1024):
        """creates a Reader using a listening port
        bound to the specified host and port."""
        endpoint = _socket.socket(_socket.AF_INET, _socket.SOCK_DGRAM, _socket.IPPROTO_UDP)
        endpoint.setsockopt(_socket.SOL_SOCKET, _socket.SO_REUSEADDR, 1)
        endpoint.settimeout(cls.DEFAULT_TIMEOUT_SEC)
        endpoint.bind(('localhost', port))
        return cls(endpoint, buffersize=buffersize, port=port)

    def __init__(self, endpoint, buffersize=1024, port="(unknown)"):
        """endpoint: datagram port to read from"""
        super().__init__()
        self.__port     = port
        self.__endpoint = endpoint
        self.__selector = _selectors.DefaultSelector()
        self.__selector.register(self.__endpoint, _selectors.EVENT_READ, 'ready')
        self.buffersize = 1024

    def __repr__(self):
        return f"DatagramIO(port={self.__port})"

    def write(self, data):
        if isinstance(data, str):
            data = data.encode('utf-8')
        self.__endpoint.write(data)

    def read_single(self):
        """calls recvfrom() using the attached endpoint."""
        try:
            events = self.__selector.select(self.timeout)
            if self.canceled:
                self.close()
                raise StreamIsClosed(f"UDP port {self.__port}")
            for key, mask in events:
                if key.data == 'ready':
                    return self.__endpoint.recvfrom(self.buffersize)
        except OSError:
            self.__endpoint = None
            raise

    def close(self):
        if self.__endpoint:
            try:
                self.__endpoint.close()
                self.__endpoint = None
            except OSError:
                pass

try:
    import serial as _serial # pyserial

    class SerialIO(InputStream):
        """an event source that keeps reading from the paired serial port.
        this class is available only when PySerial (or a `serial` module) is
        properly installed.
        """
        @classmethod
        def open(cls, addr, line_oriented=True, **kwargs):
            endpoint = _serial.Serial(addr, **kwargs)
            return cls(endpoint, line_oriented=line_oriented)

        def __init__(self, endpoint, line_oriented=True):
            super().__init__()
            self.__endpoint      = endpoint
            self.__line_oriented = line_oriented

        def write(self, data):
            if isinstance(data, str):
                data = str.encode('utf-8')
            if (self.__line_oriented == True) and (data[-1] != b'\n'):
                data = data + b'\r\n'
            self.__endpoint.write(data)

        def read_single(self):
            msg = self.__endpoint.read(1)
            if self.__line_oriented == False:
                return msg
            while not msg.endswith(b'\n'):
                msg = msg + self.__endpoint.read(1)
            return msg

        def close(self):
            try:
                self.__endpoint.close()
                self.__endpoint = None
            except OSError:
                pass

except ImportError:
    pass
