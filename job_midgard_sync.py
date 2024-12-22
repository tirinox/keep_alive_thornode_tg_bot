import re
from typing import Optional

from aiohttp import ClientSession

from alerts import AlertSender
from job import AbstractJob
from utils import normalize_url

# Regular expression pattern to extract progress
RE_PROGRESS_PATTERN = r"progress=(\d+\.\d+)%"


class JobMidgardSync(AbstractJob):
    def __init__(self, alert: AlertSender, session: Optional[ClientSession] = None,
                 period: float = 10.0,
                 target_url: str = '', progress_step: float = 1.0):
        super().__init__(alert, period, session)
        self.target_url = self.fix_url(target_url)
        self.prev_progress = 0.0
        self.progress_step = progress_step

    async def tick(self):
        logs = await self.get_logs()
        if logs is None:
            return

        # find the last log line with progress
        progress = None
        for log_line in reversed(logs):
            progress = self._get_progress(log_line)
            if progress is not None:
                break

        if progress is not None:
            self.logger.info(f"Progress: {progress}%")
            if progress >= 100.0:
                self.logger.info("Finished!")
                text = f"🆗 [Midgard] Sync completed!"
                await self.alert.send(text)
            else:
                if progress - self.prev_progress >= self.progress_step:
                    self.prev_progress = progress
                    text = f"🚥 [Midgard] Sync progress: {progress}%"
                    await self.alert.send(text)

    async def get_logs(self):
        # load logs from the target URL
        async with self.session.get(self.target_url) as resp:
            if resp.status != 200:
                self.logger.error(f"Failed to get logs: {resp.status}")
                return

            # json logs
            logs = await resp.json()
            messages = [log.get('message', '') for log in logs['logs']]
            return messages

    @staticmethod
    def fix_url(url: str):
        return normalize_url(url, '/logs')

    @staticmethod
    def _get_progress(log_line):
        match = re.search(RE_PROGRESS_PATTERN, log_line)
        if match:
            progress = float(match.group(1))
            return progress
