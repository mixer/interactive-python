from unittest.mock import Mock
import asyncio

from beam_interactive2 import Connection, GzipEncoding
from ._util import AsyncTestCase, async_test, resolve, fixture


class TestInteractiveConnection(AsyncTestCase):

    def setUp(self):
        super(TestInteractiveConnection, self).setUp()
        self._mock_socket = Mock()
        self._queue = asyncio.Queue(loop=self._loop)
        self._connection = Connection(socket=self._mock_socket, loop=self._loop,
                                      start=False)
        self._mock_socket.recv = self._queue.get
        self._connection.start()

    def tearDown(self):
        self._connection._recv_task.cancel()
        super(TestInteractiveConnection, self).tearDown()

    async def _upgrade_to_gzip(self):
        result = await asyncio.gather(
            self._connection.set_compression(GzipEncoding()),
            self._queue.put(
                '{"id":0,"type":"reply","result":{"scheme":"gzip"}}'),
            loop=self._loop)

        self.assertTrue(result[0])
        self.assertEqual('gzip', self._connection._encoding.name())

    @async_test
    def test_sends_method_calls(self):
        results = yield from asyncio.gather(
            self._connection.call('square', 2),
            self._queue.put('{"id":0,"type":"reply","result":4}'),
            loop=self._loop)

        self.assertEqual(4, results[0])
        self.assertJsonEqual(
            self._mock_socket.send.call_args[0][0],
            {'type': 'method', 'method': 'square', 'params': 2,
             'discard': False, 'id': 0})

    @async_test
    def test_times_out_calls(self):
        with self.assertRaises(asyncio.TimeoutError):
            yield from self._connection.call('square', 2, timeout=0.1)

    @async_test
    def test_upgrades_compression(self):
        yield from self._upgrade_to_gzip()
        result = yield from asyncio.gather(
            self._connection.call('square', 2),
            self._queue.put(fixture('gzipped_square_reply', 'rb')),
            loop=self._loop)

        self.assertEquals(4, result[0])
        self.assertIsInstance(self._mock_socket.send.call_args[0][0], bytes)

    @async_test
    def test_does_not_upgrade_if_the_server_denies(self):
        result = yield from asyncio.gather(
            self._connection.set_compression(GzipEncoding()),
            self._queue.put(
                '{"id":0,"type":"reply","result":{"scheme":"text"}}'),
            loop=self._loop)

        self.assertFalse(result[0])
        self.assertEqual('text', self._connection._encoding.name())

    @async_test
    def test_falls_back_if_given_unknown_bytes(self):
        yield from self._upgrade_to_gzip()
        self.assertEqual('gzip', self._connection._encoding.name())
        yield from self._queue.put(fixture('gzipped_square_reply', 'rb')[::-1])
        yield from asyncio.sleep(0, loop=self._loop)
        yield from self._queue.put('{"id":0,"type":"reply",'
                                   '"result":{"scheme":"text"}}')
        yield from asyncio.sleep(0, loop=self._loop)

        self.assertEqual('text', self._connection._encoding.name())
        self.assertJsonEqual(
            self._mock_socket.send.call_args[0][0],
            {'type': 'method', 'method': 'setCompression', 'params': {
                'scheme': ['text']}, 'discard': False, 'id': 1})

