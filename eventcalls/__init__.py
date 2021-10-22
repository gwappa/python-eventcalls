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

import logging as _logging
import threading as _threading
from traceback import print_exc as _print_exc

"""eventcalls -- a threaded way for achieving event callbacks."""

VERSION_STR = "1.0.3"
DETAILED_ERROR = False

_logging.basicConfig(level=_logging.INFO,
                     format="[%(asctime)s %(name)s] %(levelname)s: %(message)s")
LOGGER = _logging.getLogger(__name__)
LOGGER.setLevel(_logging.INFO)

class EventSource:
    """the interface for an event generator."""

    def setup(self):
        """the setup routine for this event source.

        the handler's `initialized` event will be called from its corresponding Routine
        after the end of this method.

        may return some value to be passed on to the EventHandler.
        """
        pass

    def __iter__(self):
        """returns an event iterator.

        values for next(iterator) are used as the argument
        for the event callback."""
        pass

    def cancel(self):
        """cancels the iteration of the iterator."""
        pass

    def finalize(self):
        """shutdown routine after cancel()/__iter__(), if any.

        the `done` method in the EventHandler will be called from the corresponding
        Routine after the end of this method call.

        may return some value to be passed on to the EventHandler.
        """
        pass

class Writable:
    """the interface for a writable EventSource."""
    def write(self, data):
        """writes `data` to its endpoint."""
        pass

class EventHandler:
    """the interface for an event handler.
    EventHandler subclasses can be made to implement a protocol.
    """
    def initialized(self, evt=None):
        """called in the Routine thread after the corresponding EventSource
        finishes its initialization.

        some status object may be passed to it, depending on the EventSource.
        """
        pass

    def handle(self, evt):
        """called in the Routine thread for handling the generated event."""
        pass

    def done(self, evt=None):
        """called in the Routine thread after finalizing the EventSource
        to perform any required cleanup jobs for this handler.

        some status object may be passed to it, depending on the EventSource.
        """
        pass


class EventHandlerProxy(EventHandler):
    """the EventHandler object to be used with fixed callback functions."""
    def __init__(self, fhandle=None, finit=None, fdone=None):
        if finit is not None:
            self.initialized = finit
        if fhandle is not None:
            self.handle = fhandle
        if fdone is not None:
            self.done = fdone

class Routine:
    """the class implemented with the thread loop for event generation."""
    def __init__(self, src, handler, start=True):
        """initializes the routine.

        parameters
        ----------
        src     -- a EventSource object.
        handler -- a EventHandler object.
        start   -- whether to start the thread immediately.
        """
        self._source   = src
        self._handler  = handler
        self.__thread  = _threading.Thread(target=self.run)
        self.__running = False
        if start == True:
            self.__thread.start()
            self.__running = True

    @property
    def source(self):
        return self._source

    @property
    def handler(self):
        return self._handler

    def start(self):
        """starts the thread, if not yet."""
        if not self.__thread.is_alive():
            self.__thread.start()
            self.__running = True

    def run(self):
        """runs its EventSource object."""
        status = self.source.setup()
        self.handler.initialized(status)

        status = None
        try:
            for evt in self.source:
                self.handler.handle(evt)
        except OSError as e:
            if DETAILED_ERROR == True:
                LOGGER.error("***error in reading from {self.source}:")
                _print_exc()
            else:
                LOGGER.error(f"***failed to read from source for {self.source}: {e}")
            status = e
            self.__running = False
        finally:
            try:
                self.source.finalize()
                self.__running = False
            except Exception as e:
                status = e
                self.__running = False
            finally:
                self.handler.done(status)

    def is_running(self):
        return self.__running

    def write(self, data):
        """passes `data` to its underlying `EventSource`.
        raises AttributeError if the `EventSource` object is not `Writable`."""
        if isinstance(self.source, Writable):
            self.source.write(data)
        else:
            raise AttributeError(f"source {self.source} does not seem to be writable")

    def stop(self):
        """cancels its underlying EventSource routine, and joins its thread."""
        self.source.cancel()
        self.__thread.join()

from . import io
