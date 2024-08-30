from aiohttp import ClientSession

from alerts import AlertSender
from job import AbstractJob


class JobMidgardHealth(AbstractJob):
    def __init__(self, alert: AlertSender, session: ClientSession, test_url, ref_url, period=10.0,
                 diff_alert_threshold=10):
        super().__init__(alert, period)
        self.session = session
        self.test_url = self.fix_url(test_url)
        self.ref_url = self.fix_url(ref_url)
        self.diff_alert_threshold = diff_alert_threshold

    @staticmethod
    def fix_url(test_url):
        test_url = test_url.rstrip('/')
        if not test_url.endswith('/v2/health'):
            test_url += '/v2/health'
        if not test_url.startswith('http'):
            test_url = 'https://' + test_url
        return test_url

    async def get_health(self, url):
        try:
            async with self.session.get(url) as resp:
                data = await resp.json()
                if resp.status != 200:
                    raise Exception(f'Status is not OK ({resp.status}))')
                if isinstance(data, str):
                    raise Exception(f'Unexpected text ({data})')
                return data

        except Exception as e:
            text = f"🚨Error loading URL {self.test_url}: {e!r}"
            print(text)
            await self.alert.send(text)

    async def tick(self):
        test_health = await self.get_health(self.test_url)
        if test_health is None:
            return

        if not test_health.get('database', False):
            await self.alert.send(f"🚨Test URL {self.test_url} has no database connection!")
            return

        if not test_health.get('inSync', False):
            await self.alert.send(f"🚨Test URL {self.test_url} is out of sync!")
            return

        ref_health = await self.get_health(self.ref_url)
        if ref_health is None:
            return

        test_last_aggr_height = test_health.get('lastAggregated', {}).get('height', 0)
        ref_last_aggr_height = ref_health.get('lastAggregated', {}).get('height', 0)

        self.logger.info(
            f"Aggregated height diff: {abs(test_last_aggr_height - ref_last_aggr_height)} "
            f"(ref = {ref_last_aggr_height} vs test = {test_last_aggr_height})"
        )

        if abs(test_last_aggr_height - ref_last_aggr_height) >= self.diff_alert_threshold:
            text = (f"🚨Aggregated height diff is more than {self.diff_alert_threshold} blocks "
                    f"<b>(test={test_last_aggr_height} vs ref={ref_last_aggr_height})</b>!")
            self.logger.warning(text)
            await self.alert.send(text)
            return

