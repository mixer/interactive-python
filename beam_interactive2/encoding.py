from abc import abstractmethod
from gzip import GzipFile
import varint
import io
import zlib


class EncodingException(Exception):
    """An EncodingException is raised if an error occurs in an encoding or
    decoding algorithm. Raising this exception triggers a fallback to
    plain text encoding.
    """
    pass


class Encoding:
    """Encoding is an abstract class that defines methods for decoding incoming
    and encoding outgoing websocket calls. Both encode() and decode() are
    allowed to raise EncodingExceptions, which will trigger a fallback to
    plain-text encoding.
    """

    @abstractmethod
    def name(self):
        pass

    @abstractmethod
    def encode(self, data):
        """ encode takes a string of data and returns its encoded form """
        pass

    @abstractmethod
    def decode(self, data):
        """ decode takes a byte slice of data and
        returns it decoded, string form """
        pass


def reset_buffer(buffer, value=None):
    buffer.truncate(0)
    buffer.seek(0)

    if value is not None:
        buffer.write(value)


def reset_buffer(buffer, value=None):
    buffer.truncate(0)
    buffer.seek(0)

    if value is not None:
        buffer.write(value)


class TextEncoding(Encoding):

    def name(self):
        return 'text'

    def encode(self, data):
        return data

    def decode(self, data):
        return data


class GzipEncoding(Encoding):
    def __init__(self, compression_level=6):
        super()
        self._encoder_buffer = io.BytesIO()
        self._encoder = None
        self._decoder_buffer = io.BytesIO()
        self._decoder = zlib.decompressobj(16 + zlib.MAX_WBITS)
        self._compression_level = compression_level

    def name(self):
        return 'gzip'

    def encode(self, data):
        data = data.encode('utf-8')
        self._encoder_buffer.write(varint.encode(len(data)))

        # Don't initialize the encoder before the first call to encode(), since
        # it writes the gzip header immediately and we need to insert the
        # message length prior to that happening.
        if self._encoder is None:
            self._encoder = GzipFile(fileobj=self._encoder_buffer, mode='wb',
                                     compresslevel=self._compression_level)

        self._encoder.write(data)
        self._encoder.flush()

        output = self._encoder_buffer.getvalue()
        reset_buffer(self._encoder_buffer)

        return output

    def decode(self, data):
        # Decode the varuint prefix off the data first, then smash the remaining
        # data into the decode buffer and reset it to read any previous tail.
        prefix_stream = io.BytesIO(data)
        decoded_bytes = varint.decode_stream(prefix_stream)
        self._decoder_buffer.write(data[prefix_stream.tell():])
        self._decoder_buffer.seek(0)

        decoded_data = self._decoder.decompress(
            self._decoder_buffer.getbuffer(), decoded_bytes)
        reset_buffer(self._decoder_buffer, self._decoder.unconsumed_tail)

        return decoded_data.decode('utf-8')
