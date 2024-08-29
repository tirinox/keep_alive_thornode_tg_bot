from datetime import datetime

from job import AbstractJob


class JobWatchdog(AbstractJob):
    def __init__(self, alert, period, keep_alive_ticks):
        super().__init__(alert, period)
        self.keep_alive_ticks = keep_alive_ticks
        self.time_start = datetime.now()

    async def tick(self):
        if self.tick_no % self.keep_alive_ticks == 0:
            current_time = datetime.now()
            elapsed = current_time - self.time_start
            elapsed_formatted = str(elapsed).split('.')[0]
            await self.alert.send(f"👀 Still watching... #{self.tick}. Elapsed: {elapsed_formatted}")
