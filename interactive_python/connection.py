import asyncio
import json
import websockets
import collections

from .log import logger
from .encoding import Encoding, TextEncoding
from ._util import json_encoder


class Call:
    def __init__(self, connection, payload):
        """
        A Call is an incoming message from the Interactive service.
        :param connection: the connection
        :param payload:
        """
        self._connection = connection
        self._payload = payload

    @property
    def name(self):
        """
        :return: The name of the method being called.
        :rtype: str
        """
        return self._payload['method']

    @property
    def data(self):
        """
        :return: The payload of the method being called.
        :rtype: dict
        """
        return self._payload['params']

    def reply_error(self, result):
        """
        Submits a successful reply for the call.
        :param result: The result to send to tetrisd
        """
        self._connection.reply(self._id, result=result)

    def reply_error(self, error):
        """
        Submits an errorful reply for the call.
        :param error: The error to send to tetrisd
        """
        self._connection.reply(self._id, error=error)


class Connection:
    """
    The Connection is used to connect to the Interactive server. It connects
    to a provided socket address and provides an interface for making RPC
    calls. Example usage::

        connection = Connection(
            address=get_interactive_address(),
            authorization="Bearer {}".format(my_oauth_token),
            interactive_version_id=1234)
    """

    def __init__(self, address=None, authorization=None,
                 project_version_id=None, project_sharecode=None,
                 extra_headers={}, loop=asyncio.get_event_loop(), socket=None,
                 protocol_version="2.0"):

        if authorization is not None:
            extra_headers['Authorization'] = authorization
        if project_version_id is not None:
            extra_headers['X-Interactive-Version'] = project_version_id
        if project_sharecode is not None:
            extra_headers['X-Interactive-Sharecode'] = project_sharecode
        extra_headers['X-Protocol-Version'] = protocol_version

        self._socket_or_connector = socket or websockets.client.connect(
            address, loop=loop, extra_headers=extra_headers)
        self._socket = None

        self._loop = loop
        self._encoding = TextEncoding()
        self._awaiting_replies = {}
        self._call_counter = 0
        self._last_sequence_number = 0

        self._recv_queue = collections.deque()
        self._recv_await = None
        self._recv_task = None

    async def connect(self):
        """
        Connects to the Interactive server, waiting until the connection
        if fully established before returning. Can throw a ClosedError
        if something, such as authentication, fails.
        """

        if not hasattr(self._socket_or_connector, '__await__'):
            self._socket = self._socket_or_connector
        else:
            self._socket = await self._socket_or_connector

        # await a hello event
        while True:
            packet = await self._read_single()
            if packet['type'] == 'method' and packet['method'] == 'hello':
                break

            self._recv_queue.append(packet)

        self._recv_task = asyncio.ensure_future(self._read(), loop=self._loop)

    def _fallback_to_plain_text(self):
        if isinstance(self._encoding, TextEncoding):
            return  # we're already falling back

        self._encoding = TextEncoding()
        asyncio.ensure_future(
            self.set_compression(TextEncoding()), loop=self._loop)

    def _decode(self, data):
        """
        Converts the packet data to a string,
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
        """
        Converts the packet data to a string or byte array,
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
        """
        Handles a single received packet from the Interactive service.
        """

        if 'seq' in data:
            self._last_sequence_number = data['seq']

        if data['type'] == 'reply':
            if data['id'] in self._awaiting_replies:
                self._awaiting_replies[data['id']]. \
                    set_result(data['result'])
                del self._awaiting_replies[data['id']]

            return

        self._recv_queue.append(Call(self, data))
        if self._recv_await is not None:
            self._recv_await.set_result(True)
            self._recv_await = None

    def _send(self, payload):
        """
        Encodes and sends a dict payload.
        """
        future = self._socket.send(self._encode(json_encoder.encode(payload)))
        asyncio.ensure_future(future, loop=self._loop)

    async def _read_single(self):
        """
        Reads a single event off the websocket.
        """
        try:
            raw_data = await self._socket.recv()
        except (asyncio.CancelledError, websockets.ConnectionClosed) as e:
            if self._recv_await is None:
                self._recv_await = asyncio.Future(loop=self._loop)
            self._recv_await.set_result(False)
            raise e

        return json.loads(self._decode(raw_data))

    async def _read(self):
        """
        Endless read loop that runs until the socket is closed.
        """
        while True:
            try:
                data = await self._read_single()
            except (asyncio.CancelledError, websockets.ConnectionClosed):
                break  # will already be handled
            except Exception as e:
                logger.error("error in interactive read loop", extra=e)
                break

            if isinstance(data, list):
                for item in data:
                    self._handle_recv(item)
            else:
                self._handle_recv(data)

    async def set_compression(self, scheme):
        """Updates the compression used on the websocket this should be
        called with an instance of the Encoding class, for example::

            connection.set_compression(GzipEncoding())

        You can, optionally, await on the resolution of method, though
        doing so it not at all required. Returns True if the server agreed
        on and executed the switch.

        :param scheme: The compression scheme to use
        :type scheme: Encoding
        :return: Whether the upgrade was successful
        :rtype: bool
        """
        result = await self.call("setCompression", {'scheme': [scheme.name()]})
        if result['scheme'] == scheme.name():
            self._encoding = scheme
            return True

        return False

    def reply(self, call_id, result=None, error=None):
        """
        Sends a reply for a packet id. Either the result or error should
        be fulfilled.

        :param call_id: The ID of the call being replied to.
        :type call_id: int
        :param result: The successful result of the call.
        :param error: The errorful result of the call.
        """
        packet = {'type': 'reply', 'id': call_id}

        if result is not None:
            packet['result'] = result
        if error is not None:
            packet['error'] = result

        self._send(packet)

    async def call(self, method, params, discard=False, timeout=10):
        """
        Sends a method call to the interactive socket. If discard
        is false, we'll wait for a response before returning, up to the
        timeout duration in seconds, at which point it raises an
        asyncio.TimeoutError. If the timeout is None, we'll wait forever.

        :param method: Method name to call
        :type method: str
        :param params: Parameters to insert into the method, generally a dict.
        :param discard: ``True`` to not request any reply to the method.
        :type discard: bool
        :param timeout: Call timeout duration, in seconds.
        :type timeout: int
        :return: The call response, or None if it was discarded.
        :raises: asyncio.TimeoutError
        """

        packet = {
            'type': 'method',
            'method': method,
            'params': params,
            'id': self._call_counter,
            'seq': self._last_sequence_number,
        }

        if discard:
            packet['discard'] = True

        self._call_counter += 1
        self._send(packet)

        if discard:
            return None

        future = asyncio.Future(loop=self._loop)
        self._awaiting_replies[packet['id']] = future

        try:
            return await asyncio.wait_for(future, timeout, loop=self._loop)
        except Exception as e:
            del self._awaiting_replies[packet['id']]
            raise e

    def get_packet(self):
        """
        Synchronously reads a packet from the connection. Returns None if
        there are no more packets in the queue. Example::

            while await connection.has_packet():
                dispatch_call(connection.get_packet())

        :rtype: Call
        """
        if len(self._recv_queue) > 0:
            return self._recv_queue.popleft()

        return None

    async def has_packet(self):
        """
        Blocks until a packet is read. Returns true if a packet is then
        available, or false if the connection is subsequently closed. Example::

            while await connection.has_packet():
                dispatch_call(connection.get_packet())

        :rtype: bool
        """
        if len(self._recv_queue) > 0:
            return

        if self._recv_await is None:
            self._recv_await = asyncio.Future(loop=self._loop)

        return await self._recv_await

    async def close(self):
        """Closes the socket connection gracefully"""
        self._recv_task.cancel()
        await self._socket.close()
