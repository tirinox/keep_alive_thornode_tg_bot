import asyncio
from abc import ABCMeta, abstractmethod

from alerts import AlertSender
from logs import WithLogger


class AbstractJob(WithLogger, metaclass=ABCMeta):
    def __init__(self, alert: AlertSender, period: float):
        super().__init__()
        self.tick_no = 0
        self.alert = alert
        self.period = period

    @abstractmethod
    async def tick(self):
        ...

    async def run(self):
        self.logger.info(f"Starting job with period {self.period} sec")
        while True:
            try:
                self.logger.debug(f"Tick #{self.tick_no}")
                await self.tick()
                self.logger.info(f"Tick #{self.tick_no} done")
            except Exception as e:
                self.logger.exception(f"Error in main loop: {e!r}")
                await self.alert.send(f"🚨Error in main loop: {type(e).__name__}")
            await asyncio.sleep(self.period)
            self.tick_no += 1
