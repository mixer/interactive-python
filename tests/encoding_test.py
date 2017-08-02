import unittest
from interactive_python import GzipEncoding
from ._util import fixture

samples = 3


class TestGzipEncoding(unittest.TestCase):
    def test_round_trip(self):
        encoder = GzipEncoding()
        for i in range(samples):
            sample = fixture('sample{}_decoded'.format(i))
            encoded = encoder.encode(sample)
            decoded = encoder.decode(encoded)
            self.assertEqual(sample, decoded)

    def test_against_tetrisd(self):
        """ tests against 'real' tetrisd output """
        encoder = GzipEncoding()
        for i in range(samples):
            go_decoded = fixture('sample{}_decoded'.format(i))
            py_decoded = encoder.decode(
                fixture('sample{}_encoded'.format(i), 'rb'))
            self.assertEqual(py_decoded, go_decoded)

