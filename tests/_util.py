import unittest
import asyncio
import os
import functools
import json
from nose.tools import nottest

file_path = os.path.dirname(os.path.realpath(__file__))


def fixture(path, mode='r'):
    with open(os.path.join(file_path, 'fixture', path), mode) as content_file:
        contents = content_file.read()
        if isinstance(contents, str):
            contents = contents.strip()

        return contents


@nottest
def async_test(fn):
    coroutine = asyncio.coroutine(fn)

    @functools.wraps(fn)
    def run(self, *args, **kwargs):
        future = coroutine(self, *args, **kwargs)
        self._loop.run_until_complete(future)

    return run


def resolve(value):
    future = asyncio.Future()
    future.set_result(value)
    return future


class AsyncTestCase(unittest.TestCase):

    def setUp(self):
        self._loop = asyncio.new_event_loop()

    def tearDown(self):
        self._loop.close()
        del self._loop

    def assertJsonEqual(self, a, b):
        if isinstance(a, str):
            a = json.loads(a)
        if isinstance(b, str):
            b = json.loads(b)
        self.assertEqual(a, b)
