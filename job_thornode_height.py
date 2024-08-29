import aiohttp

from alerts import AlertSender
from job import AbstractJob

BLOCK_TIME = 6


class JobThorNodeHeight(AbstractJob):
    def __init__(self, alert: AlertSender, session, test_url, ref_url, period=10.0, diff_alert_threshold=10):
        super().__init__(alert, period)
        self.session = session or aiohttp.ClientSession()
        self.test_url = self.fix_url(test_url)
        self.ref_url = self.fix_url(ref_url)
        self.diff_alert_threshold = diff_alert_threshold

    @staticmethod
    def fix_url(url: str):
        url = url.rstrip('/')
        if not url.endswith('/thorchain/lastblock'):
            url += '/thorchain/lastblock'
        if not url.startswith('http'):
            url = 'https://' + url
        return url

    async def retrieve_block_number(self, url):
        try:
            async with self.session.get(url) as resp:
                data = await resp.json()
                if resp.status != 200:
                    raise Exception(f'Status is not OK ({resp.status}))')
                if isinstance(data, str):
                    raise Exception(f'Unexpected text ({data})')
                return int(data[0]['thorchain'])

        except Exception as e:
            text = f"🚨Error loading URL {self.test_url}: {e!r}"
            print(text)
            await self.alert.send(text)

    async def compare_block_numbers(self):
        print(f'----- Tick #{self.tick:010} ------')

        block_number_test = await self.retrieve_block_number(self.test_url)
        if block_number_test is None:
            return

        block_number_ref = await self.retrieve_block_number(self.ref_url)
        if block_number_ref is None:
            return

        delta = abs(block_number_test - block_number_ref)
        time_delta = delta * BLOCK_TIME

        print(f"Block number diff: {delta} (ref = {block_number_ref} vs test = {block_number_test}) "
              f"≈{time_delta} sec")

        if abs(block_number_test - block_number_ref) >= self.diff_alert_threshold:
            text = (f"🚨Block number diff is more than {self.diff_alert_threshold} "
                    f"<b>({delta} blocks, {time_delta} seconds)</b>!")
            await self.alert.send(text)

    async def tick(self):
        await self.compare_block_numbers()
