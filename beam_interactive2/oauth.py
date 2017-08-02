import aiohttp
import asyncio
import datetime

from .errors import UnknownShortCodeError, ShortCodeAccessDeniedError, \
    ShortCodeTimeoutError


class OAuthGrant:
    """Internal DTO for an OAuth grant"""

    def __init__(self, client_id, client_secret, scopes, host):
        self.client_id = client_id
        self.client_secret = client_secret
        self.scopes = scopes
        self.host = host

    def url(self, path):
        return self.host + '/api/v1' + path


class OAuthTokens:
    """OAuthTokens is a bearer from an OAuth access and refresh token retrieved
    via the `OAuthShortCode`'s ``accepted()`` method.
    """

    def __init__(self, body):
        self.access = body['access_token']
        self.refresh = body['refresh_token']
        self.expires_at = datetime.datetime.now() + \
                          datetime.timedelta(seconds=body['expires_in'])


class OAuthShortCode:
    """
    OAuthShortCode is the shortcode handle returned by the `OAuthClient`. See
    documentation on that class for more information and usage examples.
    """

    def __init__(self, grant, client, body, check_interval=1):
        self._handle = body['handle']
        self._client = client
        self._grant = grant
        self._check_interval = check_interval
        self.code = body['code']
        self.expires_at = datetime.datetime.now() + \
                          datetime.timedelta(seconds=body['expires_in'])

    async def accepted(self):
        """
        Waits until the user enters the shortcode on the Mixer website. Throws
        if they deny access or don't enter the code in time.

        :raise ShortCodeAccessDeniedError: if the user denies access
        :raise ShortCodeTimeoutError: if the user doesn't enter
        :return: OAuthTokens
        """
        address = self._grant.url('/oauth/shortcode/check/' + self._handle)
        while True:
            await asyncio.sleep(self._check_interval)

            async with self._client.get(address) as res:
                if res.status == 200:
                    return await self._get_tokens(await res.json())
                elif res.status == 204:
                    continue
                elif res.status == 403:
                    raise ShortCodeAccessDeniedError('User has denied access')
                elif res.status == 404:
                    raise ShortCodeTimeoutError('Timeout waiting for the user '
                                                'to enter the OAuth shortcode.')

    async def _get_tokens(self, body):
        address = self._grant.url('/oauth/token')
        payload = {
            'client_id': self._grant.client_id,
            'grant_type': 'authorization_code',
            'code': body['code'],
        }

        async with self._client.post(address, json=payload) as res:
            if res.status != 200:
                raise UnknownShortCodeError('Expected a 2xx status code, but'
                                            'got {}'.format(res.status))

            return OAuthTokens(await res.json())


class OAuthClient:
    """
    The OAuth client implements our shortcode OAuth flow. From a user's
    perspective, your app or game displays a 6-digit code to them and prompts
    them to go to `mixer.com/go <https://mixer.com/go>`_. This library will
    resolve back into your application once they enter that code.

    Here's a full example of what a full usage might look like, with complete
    error handling:

    .. code::py

        import beam_interactive2 as Interactive
        async def get_access_token(client):
            code = await client.get_code()
            print("Go to mixer.com/go and enter {}".format(code.code))

            try:
                return await code.accepted()
            except Interactive.ShortCodeAccessDeniedError:
                print("The user denied access to our client")
            except Interactive.ShortCodeTimeoutError:
                print("Yo, you're too slow! Let's try again...")
                return await get_access_token(client)

        try:
            with Interactive.OAuthClient(my_client_id) as client:
                token = await get_access_token(client)
                print("Access token: {}".format(token.access))
        except Interactive.UnknownShortCodeError as e:
            print("An unknown error occurred in Mixer: {}".format(e))
    """

    def __init__(self, client_id, client_secret=None, host='https://mixer.com',
                 scopes=['interactive:robot:self'], loop=None):
        """

        :param client_id: Your OAuth client ID
        :param client_secret: Your OAuth client secret, if any
        :param host: Base address of the Mixer servers
        :param scopes:  A list of scopes to request. For Interactive, you only
            need the 'interactive:robot:self' scope
        :param loop: asyncio event loop to attach to
        """
        self._loop = loop
        self._grant = OAuthGrant(client_id, client_secret, scopes, host)

    def __enter__(self):
        self._client = aiohttp.ClientSession(loop=self._loop)
        return self

    def __exit__(self, *args):
        self._client.close()

    async def get_code(self):
        """
        Requests a shortcode from the Mixer servers and returns an
        OAuthShortCode handle.
        :return: OAuthShortCode
        """
        address = self._grant.url('/oauth/shortcode')
        payload = {
            'client_id': self._grant.client_id,
            'client_secret': self._grant.client_secret,
            'scope': ' '.join(self._grant.scopes)
        }

        async with self._client.post(address, json=payload) as res:
            if res.status >= 300:
                raise UnknownShortCodeError('Expected a 2xx status code, but'
                                            'got {}'.format(res.status))

            return OAuthShortCode(self._grant, self._client, await res.json())
