import threading as _threading

"""eventcalls -- a threaded way for achieving event callbacks."""

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

class EventHandler:
    """the interface for an event handler."""
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
        self.source   = src
        self.handler  = handler
        self.__thread = _threading.Thread(target=self.run)
        if start == True:
            self.__thread.start()

    def start(self):
        """starts the thread, if not yet."""
        if not self.__thread.is_alive():
            self.__thread.start()

    def run(self):
        """runs its EventSource object."""
        status = self.source.initialize()
        self.handler.initialized(status)

        try:
            for evt in self.source:
                self.handler.handle(evt)
        finally:
            try:
                status = self.source.finalize()
            except Exception as e:
                status = e
            finally:
                self.handler.done(status)