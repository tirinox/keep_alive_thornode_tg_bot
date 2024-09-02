from urllib import parse

from logs import WithLogger
from utils import to_json_bool


class AlertSender(WithLogger):
    def __init__(self, session, bot_token, receiver_id):
        super().__init__()
        self.session = session
        self.bot_token = bot_token
        self.receiver_id = receiver_id

    async def telegram_send_message_basic(self, user_id, message_text: str,
                                          disable_web_page_preview=True,
                                          disable_notification=False):

        message_text = message_text.strip()
        message_text = message_text[:1024]

        if not message_text:
            return

        message_text = parse.quote_plus(message_text)
        url = (
            f"https://api.telegram.org/"
            f"bot{self.bot_token}/sendMessage?"
            f"chat_id={user_id}&"
            f"text={message_text}&"
            f"parse_mode=HTML&"
            f"disable_web_page_preview={to_json_bool(disable_web_page_preview)}&"
            f"disable_notification={to_json_bool(disable_notification)}"
        )

        async with self.session.get(url) as resp:
            if resp.status != 200:
                err = await resp.read()
                raise Exception(f'Telegram error: "{err}"')
            return resp.status == 200

    async def send(self, text):
        try:
            self.logger.info(f"Sending alert: {text!r}")
            await self.telegram_send_message_basic(self.receiver_id, text)
        except Exception as e:
            self.logger.exception(f"Error sending alert: {e!r}")
