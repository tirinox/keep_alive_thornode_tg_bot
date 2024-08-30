import asyncio
import logging
import os
from contextlib import suppress

import aiohttp
from dotenv import load_dotenv

from alerts import AlertSender
from job_midgard_height import JobMidgardHealth
from job_thornode_height import JobThorNodeHeight
from job_watchdog import JobWatchdog
from logs import WithLogger, setup_logs


class Main(WithLogger):
    def __init__(self):
        super().__init__()
        self.admin_id = int(os.environ['TG_ADMIN_USER'])
        self.bot_token = os.environ['TG_BOT_TOKEN']
        self.period = float(os.environ['TICK_PERIOD'])
        self.diff_alert_threshold = int(os.environ['BLOCK_DIFF_TO_ALERT']) or 10
        self.keep_alive_ticks = int(os.environ['KEEP_ALIVE_NOTIFICATION_PERIOD_TICKS']) or 9999
        self.session = aiohttp.ClientSession()
        self.alert = AlertSender(self.session, self.bot_token, self.admin_id)

        # jobs are
        self.jobs = [
            JobThorNodeHeight(
                self.alert, self.session,
                ref_url=os.environ['THORNODE_REF_URL'], test_url=os.environ['THORNODE_TEST_URL'],
                period=self.period, diff_alert_threshold=self.diff_alert_threshold
            ),
            JobWatchdog(self.alert, self.period, self.keep_alive_ticks),
            JobMidgardHealth(
                self.alert, self.session,
                ref_url=os.environ['MIDGARD_HEALTH_REF_URL'], test_url=os.environ['MIDGARD_HEALTH_TEST_URL'],
                period=self.period, diff_alert_threshold=self.diff_alert_threshold
            )
        ]

    async def run(self):
        self.logger.info("Starting main loop")
        with suppress(Exception):
            await self.alert.send("🚀 Starting main loop")

        await asyncio.gather(
            *[job.run() for job in self.jobs]
        )


async def main():
    setup_logs(logging.INFO)
    load_dotenv()

    main_obj = Main()
    await main_obj.run()


if __name__ == "__main__":
    asyncio.run(main())
