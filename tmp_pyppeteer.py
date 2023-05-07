import asyncio
import logging
import httpx
import pyppeteer

import conf

logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(levelname)s] %(name)s: %(message)s')
log = logging.getLogger('octo')
OCTO_TOKEN = conf.OCTO_API_TOKEN
OCTO_API = 'https://app.octobrowser.net/api/v2/automation/profiles'
LOCAL_API = 'http://localhost:58888/api/profiles/start'
HEADERS = {'X-Octo-Api-Token': OCTO_TOKEN}

UUID = 'ccde58b53f9c46c3b9cd943c872e9b88'


async def get_cdp(cli):
    resp = (await cli.post(LOCAL_API, json={'uuid': UUID, 'debug_port': True})).json()
    log.info(f'Start profile resp: {resp}')
    return resp['ws_endpoint']


async def main():
    async with httpx.AsyncClient() as cli:
        ws_url = await get_cdp(cli)
    browser = await pyppeteer.launcher.connect(browserWSEndpoint=ws_url)
    # try:
    page = await browser.newPage()
    url = 'https://uefa.com/'
    await page.goto(url)
    # finally:
    #     await browser.close()


if __name__ == '__main__':
    asyncio.run(main())