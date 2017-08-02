from unittest.mock import Mock
import asyncio
import websockets

from interactive_python import Connection, GzipEncoding
from ._util import AsyncTestCase, async_test, resolve, fixture


sample_method = '{"id":0,"type":"method","method":"some_method",' \
                '"params":{"foo": 42}}'


class TestInteractiveConnection(AsyncTestCase):

    def setUp(self):
        super(TestInteractiveConnection, self).setUp()
        self._mock_socket = Mock()
        self._mock_socket.close = asyncio.Future(loop=self._loop)
        self._mock_socket.close.set_result(None)
        send_future = asyncio.Future(loop=self._loop)
        send_future.set_result(None)
        self._mock_socket.send.return_value = send_future
        self._queue = asyncio.Queue(loop=self._loop)
        self._connection = Connection(socket=self._mock_socket, loop=self._loop)
        self._mock_socket.recv = self._queue.get
        self._queue.put_nowait('{"type":"method","method":"hello","seq":1}')

    def tearDown(self):
        if self._connection._recv_task is not None:
            self._connection._recv_task.cancel()
        super(TestInteractiveConnection, self).tearDown()

    async def _upgrade_to_gzip(self):
        result = await asyncio.gather(
            self._connection.set_compression(GzipEncoding()),
            self._queue.put(
                '{"id":0,"type":"reply","result":{"scheme":"gzip"},"seq":2}'),
            loop=self._loop)

        self.assertTrue(result[0])
        self.assertEqual('gzip', self._connection._encoding.name())

    @async_test
    def test_sends_method_calls(self):
        yield from self._connection.connect()
        results = yield from asyncio.gather(
            self._connection.call('square', 2),
            self._queue.put('{"id":0,"type":"reply","result":4,"seq":2}'),
            loop=self._loop)

        self.assertEqual(4, results[0])
        self.assertJsonEqual(
            self._mock_socket.send.call_args[0][0],
            {'type': 'method', 'method': 'square',
             'params': 2, 'id': 0, 'seq': 0}
        )

    @async_test
    def test_times_out_calls(self):
        yield from self._connection.connect()
        with self.assertRaises(asyncio.TimeoutError):
            yield from self._connection.call('square', 2, timeout=0.1)

    @async_test
    def test_upgrades_compression(self):
        yield from self._connection.connect()
        yield from self._upgrade_to_gzip()
        result = yield from asyncio.gather(
            self._connection.call('square', 2),
            self._queue.put(fixture('gzipped_square_reply', 'rb')),
            loop=self._loop)

        self.assertEquals(4, result[0])
        self.assertIsInstance(self._mock_socket.send.call_args[0][0], bytes)

    @async_test
    def test_does_not_upgrade_if_the_server_denies(self):
        yield from self._connection.connect()
        result = yield from asyncio.gather(
            self._connection.set_compression(GzipEncoding()),
            self._queue.put(
                '{"id":0,"type":"reply","result":{"scheme":"text"},"seq":2}'),
            loop=self._loop)

        self.assertFalse(result[0])
        self.assertEqual('text', self._connection._encoding.name())

    @async_test
    def test_falls_back_if_given_unknown_bytes(self):
        yield from self._connection.connect()
        yield from self._upgrade_to_gzip()
        self.assertEqual('gzip', self._connection._encoding.name())
        yield from self._queue.put(fixture('gzipped_square_reply', 'rb')[::-1])
        yield from asyncio.sleep(0, loop=self._loop)
        yield from self._queue.put('{"id":0,"type":"reply",'
                                   '"result":{"scheme":"text"},"seq":2}')
        yield from asyncio.sleep(0, loop=self._loop)

        self.assertEqual('text', self._connection._encoding.name())
        self.assertJsonEqual(
            self._mock_socket.send.call_args[0][0],
            {'type': 'method', 'method': 'setCompression', 'params': {
                'scheme': ['text']}, 'id': 1, 'seq': 2})

    @async_test
    def test_queues_packets(self):
        yield from self._connection.connect()
        self._queue.put_nowait(sample_method)
        has_packet = yield from self._connection.has_packet()
        self.assertTrue(has_packet)
        self.assertJsonEqual(self._connection.get_packet().data, '{"foo":42}')
        self.assertIsNone(self._connection.get_packet())

    @async_test
    def test_handles_connection_closed(self):
        yield from self._connection.connect()

        def raise_closed():
            raise websockets.ConnectionClosed(4000, "")

        yield from asyncio.sleep(0)
        self._mock_socket.recv = raise_closed
        self._queue.put_nowait(sample_method)

        has_packet = yield from self._connection.has_packet()
        self.assertTrue(has_packet)  # reads what we pushed to get unblocked
        has_packet = yield from self._connection.has_packet()
        self.assertFalse(has_packet)  # gets a connection closed
