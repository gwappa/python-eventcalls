# eventcalls

a threaded way for achieving event callbacks.

## Dependency

- Python 3 (I have not taken care of the issues related to `str` and `bytes`)
- (optional) the `pyserial` library: it presumably comes with the default Anaconda distribution. You can obtain it via `conda` or `pip`.

## Installation

Use of pip would be straightforward:

```
$ pip install git+https://github.com/gwappa/python-eventcalls.git
```

Alternatively, you can first clone the repository and then perform installation:

```
$ git clone https://github.com/gwappa/python-eventcalls.git
$ cd python-eventcalls
$ pip install .
```

## How it works

## EventSource

All the I/O functionality comes with the `eventcalls.EventSource` interface.
The default I/O includes:

- `eventcalls.io.DatagramIO`: for UDP communication
- `eventcalls.io.SerialIO`: for serial communication (requires `pyserial`)

## Routine

The `eventcalls.Routine` class wraps the `EventSource` and manages the I/O routines.
It runs a python thread internally to keep reading data from the underlying `EventSource`,
while accepting the `write` method calls to write data into it.

- `Routine.start()`: starts the underlying event thread (if not yet started).
- `Routine.stop()`: closes the underlying `EventSource`, and stops running the event thread.
- `Routine.is_running()`: returns `True` if the underlying thread is running.
- `Routine.write(data)`: attempts to write data (binary or string) into the endpoint.
  Note this method _never_ checks whether the endpoint is (still) open or not.

## EventHandler

You can receive the data from the event source by implementing the `eventcalls.EventHandler` interface.
The interface includes several one-argument methods:

1. `initialized(self, evt)`: called when the event source becomes useable. Usually, `evt` is `None`
  (it is left this way for implementing a specialized I/O interface that may provide some configuration parameters).
2. `handle(self, evt)`: called when the event source received (a portion of) binary data.
  For a UDP packet, it is comprised of the packet contents.
  For serial communication, you can choose from either one-byte data or a newline-terminating line of binary string.
3. `finalized(self, evt)`: called when the I/O becomes unusable anymore.
  `evt` is `None` by default, but may contain an exception instance in case the I/O was closed because of an error.

You can set your handler to the `Routine` instance upon initialization.
Note it only accepts one single `Handler` instance for a single `Routine` object.

## License

(c) 2019 Keisuke Sehara, the MIT license
