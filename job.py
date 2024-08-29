import asyncio
from abc import ABCMeta, abstractmethod

from alerts import AlertSender


class AbstractJob(metaclass=ABCMeta):
    def __init__(self, alert: AlertSender, period: float):
        self.tick_no = 0
        self.alert = alert
        self.period = period

    @abstractmethod
    async def tick(self):
        ...

    async def run(self):
        while True:
            try:
                await self.tick()
            except Exception as e:
                try:
                    await self.alert.send(f"🚨Error in main loop: {e!r}")
                except Exception as e2:
                    print(f"Error sending alert: {e2!r} from {e!r}")
            await asyncio.sleep(self.period)
            self.tick_no += 1
