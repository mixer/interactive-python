import aiohttp

from .errors import DiscoveryError, NoServersAvailableError


class Discovery:
    """Discovery is a simple service discovery class which retrieves an
    Interactive host to connect to. This is passed into the State by default;
    you usually should not need to override it.
    """
    def __init__(self, host='https://mixer.com',
                 path='/api/v1/interactive/hosts', loop=None, timeout=10):
        self._host = host
        self._path = path
        self._timeout = timeout
        self._loop = None

    async def find(self):
        """Returns the websocket address of an interactive server to connect
        to, or raises a NoServersAvailableError.
        """

        # Technically it might be nice to asyncio this, but I'm not eager to
        # add another dependency and Python doesn't seem to have an asyncio
        # http client in its standard library yet.

        async with aiohttp.ClientSession(loop=self._loop) as session:
            async with session.get(self._host + self._path) as res:
                if res.status >= 300:
                    raise DiscoveryError('Expected a 2xx status code, but'
                                         'got {}'.format(res.status))

                servers = await res.json()
                if len(servers) == 0:
                    raise NoServersAvailableError()
                print(servers[0]['address'])
                return servers[0]['address']
