import asyncio
import json
import websockets

from .log import logger
from .encoding import TextEncoding


class Connection:
    """The Connection is used to connect to the Interactive server. It connects
    to a provided socket address and provides an interface for making RPC
    calls. Example usage::

        connection = Connection(
            address=get_interactive_address(),
            authorization="Bearer {}".format(my_oauth_token),
            interactive_version_id=1234)
    """

    def __init__(self, address=None, authorization=None,
                 interactive_version_id=None, extra_headers={},
                 loop=asyncio.get_event_loop(), socket=None,
                 protocol_version="2.0", start=True):

        if authorization is not None:
            extra_headers['Authorization'] = authorization
        if interactive_version_id is not None:
            extra_headers['X-Interactive-Version'] = interactive_version_id
        extra_headers['X-Protocol-Version'] = protocol_version

        self._socket = socket or websockets.client.connect(
            address, loop=loop, extra_headers=extra_headers)
        self._loop = loop
        self._encoding = TextEncoding()
        self._awaiting_replies = {}
        self._call_counter = 0

        self._recv_queue = asyncio.Queue()
        self._recv_task = None

        if start:
            self.start()

    def _fallback_to_plain_text(self):
        if isinstance(self._encoding, TextEncoding):
            return  # we're already falling back

        self._encoding = TextEncoding()
        asyncio.ensure_future(
            self.set_compression(TextEncoding()), loop=self._loop)

    def _decode(self, data):
        """Converts the packet data to a string,
        decompressing it if necessary. Always returns a string.
        """
        if isinstance(data, str):
            return data

        try:
            return self._encoding.decode(data)
        except Exception as e:
            self._fallback_to_plain_text()
            logger.info("error decoding Interactive message, falling back to"
                        "plain text", extra=e)

    def _encode(self, data):
        """Converts the packet data to a string or byte array,
        compressing it if necessary.
        """
        try:
            return self._encoding.encode(data)
        except Exception as e:
            self._fallback_to_plain_text()
            logger.warn("error encoding Interactive message, falling back to"
                        "plain text", extra=e)

        return data

    def _handle_recv(self, data):
        """Handles a received packets using internal hooks. Returns true
        if the packet was handled and does not need to be bubbled to the
        caller, false otherwise.
        """

        if data['type'] == 'reply':
            if data['id'] in self._awaiting_replies:
                self._awaiting_replies[data['id']]. \
                    set_result(data['result'])
                del self._awaiting_replies[data['id']]

            return True

        return False

    def start(self):
        """ Starts the socket 'read' loop. Mostly for testing, this is done
        automatically for you otherwise."""
        self._recv_task = asyncio.ensure_future(self._read(), loop=self._loop)

    @asyncio.coroutine
    def _read(self):

        while True:
            try:
                raw_data = yield from self._socket.recv()
            except asyncio.CancelledError:
                break
            except websockets.ConnectionClosed as e:
                self._recv_queue.put_nowait(e)
                break

            data = json.loads(self._decode(raw_data))
            if not self._handle_recv(data):
                self._recv_queue.put_nowait(data)

    async def set_compression(self, scheme):
        """Updates the compression used on the websocket this should be
        called with an instance of the Encoding class, for example::

            connection.set_compression(GzipEncoding())

        You can, optionally, await on the resolution of method, though
        doing so it not at all required. Returns True if the server agreed
        on and executed the switch.
        """
        result = await self.call("setCompression", {'scheme': [scheme.name()]})
        if result['scheme'] == scheme.name():
            self._encoding = scheme
            return True

        return False

    async def call(self, method, params, discard=False, timeout=10):
        """Sends a method call to the interactive socket. If discard
        is false, we'll wait for a response before returning, up to the
        timeout duration in seconds, at which point it raises an
        asyncio.TimeoutError. If the timeout is None, we'll wait forever.
        """
        id = self._call_counter
        encoded = self._encode(json.dumps({
            'type': 'method',
            'method': method,
            'params': params,
            'discard': discard,
            'id': id
        }))

        self._call_counter += 1
        self._socket.send(encoded)

        if discard:
            return None

        future = asyncio.Future(loop=self._loop)
        self._awaiting_replies[id] = future

        try:
            return await asyncio.wait_for(future, timeout, loop=self._loop)
        except Exception as e:
            del self._awaiting_replies[id]
            raise e

    async def recv(self):
        """Yields method calls that come down from the Interactive connection.
        Throws a ``websockets.exceptions.ConnectionClosed`` if the socket
        is closed. Calls can be easily retrieved like so:

            while True:
                call = await connection.recv()
                dispatch_call(call)
        """

        item = await self._recv_queue.get()
        if isinstance(item, Exception):
            self._recv_queue.put_nowait(item)
            raise item

        return item

    async def close(self):
        """Closes the socket connection gracefully"""
        self._recv_task.cancel()
        await self._socket.close()
