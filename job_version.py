import aiohttp
import semver

from alerts import AlertSender
from job import AbstractJob
from utils import normalize_url

BLOCK_TIME = 6


class JobThorNodeVersion(AbstractJob):
    def __init__(self, alert: AlertSender, session, test_url, ref_url, period=10.0):
        super().__init__(alert, period)
        self.session = session or aiohttp.ClientSession()
        self.test_url = self.fix_url(test_url)
        self.ref_url = self.fix_url(ref_url)
        self.last_signalled_version = None

    @staticmethod
    def fix_url(url: str):
        return normalize_url(url, '/thorchain/version')

    async def retrieve_version(self, url):
        try:
            async with self.session.get(url) as resp:
                data = await resp.json()
                if resp.status != 200:
                    raise Exception(f'Status is not OK ({resp.status}))')
                if isinstance(data, str):
                    raise Exception(f'Unexpected text ({data})')
                return data

        except Exception as e:
            text = f"🚨 [THOR] Error loading URL {self.test_url}: {type(e).__name__}"
            self.logger.exception(text)
            await self.alert.send(text)

    async def compare_versions(self):
        test_v = await self.retrieve_version(self.test_url)
        if test_v is None:
            return

        ref_v = await self.retrieve_version(self.ref_url)
        if ref_v is None:
            return

        self.logger.info(f"Test version: {test_v} vs Ref version: {ref_v}")

        my_version = semver.VersionInfo.parse(test_v['querier'])
        ref_version = semver.VersionInfo.parse(ref_v['querier'])

        if my_version != ref_version:
            if self.last_signalled_version != ref_version:
                self.last_signalled_version = ref_version
                text = (f"⬆️ [THOR] Our version (<b>{my_version})</b> "
                        f"is different from the reference one (<b>{ref_version})</b>!")
                await self.alert.send(text)

    async def tick(self):
        await self.compare_versions()
