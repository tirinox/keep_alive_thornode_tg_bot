from datetime import datetime

from cooldown import Cooldown
from job import AbstractJob
from utils import format_timedelta


class JobWatchdog(AbstractJob):
    def __init__(self, alert, period, alert_period_sec):
        super().__init__(alert, period)
        self.alert_period_sec = alert_period_sec
        self.start_ts = datetime.utcnow()
        self.fire_ts = self.start_ts
        self.cd = Cooldown(self.name, self.alert_period_sec)
        self.logger.info(f'Configured watchdog with period {self.alert_period_sec} sec.')

    async def tick(self):
        if self.cd.ready:
            elapsed_formatted = format_timedelta(datetime.utcnow() - self.start_ts)
            period_formatted = format_timedelta(self.alert_period_sec)
            await self.alert.send(
                f"👀 Still watching... #{self.tick_no}.\n"
                f"Elapsed since last restart: {elapsed_formatted}.\n"
                f"I will send you just message every {period_formatted}.")

            self.cd.do()
