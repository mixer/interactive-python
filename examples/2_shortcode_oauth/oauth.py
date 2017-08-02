"""
This is an example of "shortcode" oauth that you can use to get an access token
to connect to Interactive. You want to create an OAuth client first on
https://mixer.com/lab, then use its client ID to run this script. You can leave
the "redirect urls" blank.

Run this with::

    python -m examples.2_shortcode_oauth.oauth <YourClientId>
"""

import interactive_python as interactive
import asyncio
from sys import argv

async def get_access_token(client):
    code = await client.get_code()
    print("Go to mixer.com/go and enter {}".format(code.code))

    try:
        return await code.accepted()
    except interactive.ShortCodeAccessDeniedError:
        print("The user denied access to our client")
    except interactive.ShortCodeTimeoutError:
        print("Yo, you're too slow! Let's try again...")
        return await get_access_token(client)

async def run():
    try:
        with interactive.OAuthClient(argv[1]) as client:
            token = await get_access_token(client)
            print("Access token: {}".format(token.access))
    except interactive.UnknownShortCodeError as e:
        print("An unknown error occurred in Mixer: {}".format(e))

if __name__ == '__main__':
    asyncio.get_event_loop().run_until_complete(run())
