import asyncio
import logging
import os
from contextlib import suppress

import aiohttp
from dotenv import load_dotenv

from alerts import AlertSender
from job_midgard_height import JobMidgardHealth
from job_thornode_height import JobThorNodeHeight
from job_version import JobThorNodeVersion
from job_watchdog import JobWatchdog
from logs import WithLogger, setup_logs


class Main(WithLogger):
    def __init__(self):
        super().__init__()
        self.admin_id = int(os.environ['TG_ADMIN_USER'])
        self.bot_token = os.environ['TG_BOT_TOKEN']

        s = self.session = aiohttp.ClientSession()
        a = self.alert = AlertSender(self.session, self.bot_token, self.admin_id)

        self.period = float(os.environ.get('TICK_PERIOD', 60))

        ref_thornode = os.environ['THORNODE_REF_URL']
        test_thornode = os.environ['THORNODE_TEST_URL']

        # jobs are
        self.jobs = [
            JobThorNodeHeight(
                a, s,
                ref_url=ref_thornode,
                test_url=test_thornode,
                period=self.period,
                diff_alert_threshold=int(os.environ.get('THOR_BLOCK_DIFF_TO_ALERT', 10))
            ),
            JobMidgardHealth(
                a, s,
                ref_url=os.environ['MIDGARD_HEALTH_REF_URL'],
                test_url=os.environ['MIDGARD_HEALTH_TEST_URL'],
                period=self.period,
                diff_alert_threshold=int(os.environ.get('MIDGARD_BLOCK_DIFF_TO_ALERT', 10)),
            ),
            JobWatchdog(
                a, self.period,
                keep_alive_ticks=int(os.environ.get('KEEP_ALIVE_NOTIFICATION_PERIOD_TICKS', 1440))
            ),
            JobThorNodeVersion(
                a, s,
                ref_url=ref_thornode,
                test_url=test_thornode,
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
