import asyncio
import os

import aiohttp
from dotenv import load_dotenv

from alerts import AlertSender
from job_thornode_height import JobThorNodeHeight
from job_watchdog import JobWatchdog


class Main:
    def __init__(self):
        self.admin_id = int(os.environ['TG_ADMIN_USER'])
        self.bot_token = os.environ['TG_BOT_TOKEN']
        self.test_url = os.environ['TEST_URL']
        self.ref_url = os.environ['REF_URL']
        self.period = float(os.environ['TICK_PERIOD'])
        self.diff_alert_threshold = int(os.environ['BLOCK_DIFF_TO_ALERT']) or 10
        self.keep_alive_ticks = int(os.environ['KEEP_ALIVE_NOTIFICATION_PERIOD_TICKS']) or 9999
        self.session = aiohttp.ClientSession()
        self.alert = AlertSender(self.bot_token, self.admin_id)

        # jobs are
        self.jobs = [
            JobThorNodeHeight(
                self.alert,
                self.session,
                self.test_url, self.ref_url,
                self.period, self.diff_alert_threshold
            ),
            JobWatchdog(self.alert, self.period, self.keep_alive_ticks)
        ]

    async def run(self):
        await asyncio.gather(
            *[job.run() for job in self.jobs]
        )


async def main():
    load_dotenv()

    main_obj = Main()
    await main_obj.run()


if __name__ == "__main__":
    asyncio.run(main())
