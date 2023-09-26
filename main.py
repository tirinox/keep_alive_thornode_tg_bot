import asyncio
import os
import urllib.parse
from contextlib import suppress

import aiohttp
from dotenv import load_dotenv


def to_json_bool(b):
    return 'true' if b else 'false'


BLOCK_TIME = 6


class Main:
    def __init__(self, admin_id, bot_token, test_url, ref_url, period=10.0, diff_alert_threshold=10,
                 keep_alive_ticks=9999):
        self.session = aiohttp.ClientSession()
        self.admin_id = admin_id
        self.bot_token = bot_token
        self.period = period
        self.test_url = test_url
        self.ref_url = ref_url
        self.diff_alert_threshold = diff_alert_threshold
        self.tick = 0
        self.keep_alive_ticks = keep_alive_ticks

    async def retrieve_block_number(self, url):
        try:
            async with self.session.get(url) as resp:
                data = await resp.json()
                if resp.status != 200:
                    raise Exception(f'Status is not OK ({resp.status}))')
                if isinstance(data, str):
                    raise Exception(f'Unexpected text ({data})')
                return int(data[0]['thorchain'])

        except Exception as e:
            text = f"🚨Error loading URL {self.test_url}: {e!r}"
            print(text)
            await self.telegram_send_message_basic(
                self.admin_id,
                message_text=text
            )

    async def compare_block_numbers(self):
        print(f'----- Tick #{self.tick:010} ------')

        block_number_test = await self.retrieve_block_number(self.test_url)
        if block_number_test is None:
            return

        block_number_ref = await self.retrieve_block_number(self.ref_url)
        if block_number_ref is None:
            return

        delta = abs(block_number_test - block_number_ref)
        time_delta = delta * BLOCK_TIME

        print(f"Block number diff: {delta} (ref = {block_number_ref} vs test = {block_number_test}) "
              f"≈{time_delta} sec")

        if abs(block_number_test - block_number_ref) >= self.diff_alert_threshold:
            text = (f"🚨Block number diff is more than {self.diff_alert_threshold} "
                    f"<b>({delta} blocks, {time_delta} seconds)</b>!")
            await self.telegram_send_message_basic(
                self.admin_id,
                message_text=text
            )

    async def run(self):
        while True:
            if self.tick % self.keep_alive_ticks == 0:
                await self.telegram_send_message_basic(
                    self.admin_id,
                    message_text=f"👋 I'm alive! Tick #{self.tick}"
                )
            await self.compare_block_numbers()
            await asyncio.sleep(self.period)
            self.tick += 1

    async def telegram_send_message_basic(self, user_id, message_text: str,
                                          disable_web_page_preview=True,
                                          disable_notification=False):
        with suppress(Exception):
            message_text = message_text.strip()

            if not message_text:
                return

            message_text = urllib.parse.quote_plus(message_text)
            url = (
                f"https://api.telegram.org/"
                f"bot{self.bot_token}/sendMessage?"
                f"chat_id={user_id}&"
                f"text={message_text}&"
                f"parse_mode=HTML&"
                f"disable_web_page_preview={to_json_bool(disable_web_page_preview)}&"
                f"disable_notification={to_json_bool(disable_notification)}"
            )

            async with aiohttp.ClientSession() as session:
                async with session.get(url) as resp:
                    if resp.status != 200:
                        err = await resp.read()
                        raise Exception(f'Telegram error: "{err}"')
                    return resp.status == 200


async def main():
    load_dotenv()

    main_obj = Main(int(os.environ['TG_TEST_USER']),
                    os.environ['TG_BOT_TOKEN'],
                    os.environ['TEST_URL'],
                    os.environ['REF_URL'],
                    period=float(os.environ['TICK_PERIOD']),
                    diff_alert_threshold=int(os.environ['BLOCK_DIFF_TO_ALERT']),
                    keep_alive_ticks=int(os.environ['KEEP_ALIVE_NOTIFICATION_PERIOD_TICKS']))
    await main_obj.run()


if __name__ == "__main__":
    asyncio.run(main())
