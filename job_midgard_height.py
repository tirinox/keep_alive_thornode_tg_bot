from aiohttp import ClientSession

from alerts import AlertSender
from cooldown import Cooldown
from job import AbstractJob
from job_thornode_height import BLOCK_TIME
from utils import normalize_url


class JobMidgardHealth(AbstractJob):
    def __init__(self, alert: AlertSender, session: ClientSession, test_url, ref_url, period=10.0,
                 diff_alert_threshold=10, cooldown=10):
        super().__init__(alert, period, session)
        self.session = session
        self.test_url = self.fix_url(test_url)
        self.ref_url = self.fix_url(ref_url)
        self.diff_alert_threshold = diff_alert_threshold
        self.cd = Cooldown(self.name, cooldown)

    @staticmethod
    def fix_url(url: str):
        return normalize_url(url, '/v2/health')

    async def get_health(self, url):
        try:
            return await self.get_url_contents(url)
        except Exception as e:
            text = f"🚨 [MDG] Error loading URL: {self.test_url}: {type(e).__name__}"
            self.logger.exception(text)
            await self.alert.send(text)

    async def tick(self):
        if not self.cd.ready:
            return

        test_health = await self.get_health(self.test_url)

        self.logger.info(f"Test health: {test_health}")
        if test_health is None:
            self.cd.grow_duration()
            return

        if not test_health.get('database', False):
            await self.alert.send(f"🚨 [MDG] Test URL {self.test_url} has no database connection!")
            self.cd.grow_duration()
            return

        if not test_health.get('inSync', False):
            await self.alert.send(f"🚨 [MDG] Test URL {self.test_url} is out of sync!")
            self.cd.grow_duration()
            return

        ref_health = await self.get_health(self.ref_url)
        if ref_health is None:
            return

        test_last_aggr_height = test_health.get('lastAggregated', {}).get('height', 0)
        ref_last_aggr_height = ref_health.get('lastAggregated', {}).get('height', 0)
        diff = abs(test_last_aggr_height - ref_last_aggr_height)
        time_delta = diff * BLOCK_TIME

        self.logger.info(
            f"Aggregated height diff: {diff} "
            f"(ref = {ref_last_aggr_height} vs test = {test_last_aggr_height})"
        )

        if diff >= self.diff_alert_threshold:
            text = (f"🚨 [MDG] Aggregated height diff is more than {self.diff_alert_threshold} blocks: "
                    f" <b>({diff} blocks | {time_delta} sec)</b>"
                    f" (test={test_last_aggr_height} vs ref={ref_last_aggr_height})!")
            self.logger.warning(text)
            await self.alert.send(text)
            return

