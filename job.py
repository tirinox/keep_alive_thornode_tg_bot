import asyncio
from abc import ABCMeta, abstractmethod
from typing import Optional

from aiohttp import ClientSession

from alerts import AlertSender
from logs import WithLogger
from utils import DAY


class AbstractJob(WithLogger, metaclass=ABCMeta):
    def __init__(self, alert: AlertSender, period: float, session: Optional[ClientSession] = None):
        super().__init__()
        self.tick_no = 0
        self.alert = alert
        self.session = session
        self.period = period
        if self.period < 1:
            self.logger.warning(f"Period is too low: {self.period} sec. Setting to 1 sec.")
            self.period = 1
        elif self.period > DAY:
            self.logger.warning(f"Period is too high: {self.period} sec. Setting to 1 day.")
            self.period = DAY

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
                self.logger.exception(f"Error in the loop: {e!r}")
                await self.alert.send(f"🚨Error in the loop: {type(e).__name__}")
            await asyncio.sleep(self.period)
            self.tick_no += 1

    @property
    def name(self):
        return self.__class__.__name__

    async def get_url_contents(self, url):
        if not self.session:
            raise Exception("No session provided!")

        async with self.session.get(url) as resp:
            data = await resp.json()
            if resp.status != 200:
                raise Exception(f'Status is not OK ({resp.status}))')
            if isinstance(data, str):
                raise Exception(f'Unexpected text: <code>{data[:120]}</code>')
            return data
