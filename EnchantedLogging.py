import Config


class EnchantedLogging:
    def __init__(self, bot, level, message_format: str):
        self.bot = bot
        self.message_format = message_format
        self.log_channel = Config.LOG_CHANNEL
        self.level = level
        self.info_logs = []

    # Logging levels, as per the logging module
    NOTSET = 0
    DEBUG = 10
    INFO = 20
    WARNING = 30
    ERROR = 40
    CRITICAL = 50

    def info(self, msg):
        if self.level > EnchantedLogging.INFO:
            return
        self.info_logs.append(self.message_format.format(level="INFO", message=msg))

    async def send_logs(self):
        info_logs = self.info_logs
        self.info_logs = []
        # Sort into messages with a maximum of 2000 characters
        message = ""
        messages = []
        for log in info_logs:
            message += log + "\n"
            if len(message) > 2000:
                messages.append(message[:-len("\n"+log+"\n")])
                message = log + "\n"
        messages.append(message)

        # Send each message
        channel = self.bot.get_channel(self.log_channel)
        for msg in messages:
            if len(msg) != 0:
                await channel.send(msg)

    async def warning(self, msg):
        if self.level > EnchantedLogging.WARNING:
            return
        channel = self.bot.get_channel(self.log_channel)
        await channel.send(self.message_format.format(level="WARNING", message=msg))

    async def error(self, msg):
        if self.level > EnchantedLogging.ERROR:
            return
        channel = self.bot.get_channel(self.log_channel)
        await channel.send(">>> " + self.message_format.format(level="ERROR", message=msg))

    async def exception(self, msg):
        if self.level > EnchantedLogging.CRITICAL:
            return
        channel = self.bot.get_channel(self.log_channel)
        await channel.send(">>> " + self.message_format.format(level="**EXCEPTION**", message=msg))
