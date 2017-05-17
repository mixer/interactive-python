import json
from http import client

from .errors import DiscoveryError, NoServersAvailableError


class Discovery:
    """Discovery is a simple service discovery class which retrieves an
    Interactive host to connect to.
    """
    def __init__(self, secure=True, host='beam.pro',
                 path='/api/v1/interactive/hosts', timeout=10):
        self._secure = secure
        self._host = host
        self._path = path
        self._timeout = timeout

    async def find(self):
        """Returns the websocket address of an interactive server to connect
        to, or raises a NoServersAvailableError.
        """

        # Technically it might be nice to asyncio this, but I'm not eager to
        # add another dependency and Python doesn't seem to have an asyncio
        # http client in its standard library yet.

        if self._secure:
            cnx = client.HTTPSConnection(self._host, timeout=self._timeout)
        else:
            cnx = client.HTTPConnection(self._host, timeout=self._timeout)

        cnx.request('GET', self._path, headers={'Accept': 'encoding/json'})
        res = cnx.getresponse()
        if res.status >= 300:
            raise DiscoveryError("Expected a 2xx status code, but got {}"
                                 .format(res.status))

        servers = json.loads(res.read())
        if len(servers) == 0:
            raise NoServersAvailableError()

        return servers[0]
