# -*- coding: utf-8 -*-
# This plugin handles registration, PM forwarding, and echoing of admin PMs
import irc3
from irc3 import rfc
from irc3.utils import IrcString

import config


@irc3.plugin
class Plugin(object):
    identified: bool = False
    password_file: str = "password"

    def __init__(self, bot: irc3.IrcBot):
        self.bot = bot

    # Handle messages received
    # noinspection PyUnusedLocal
    @irc3.event(rfc.PRIVMSG)
    def reply(self,
              tags: IrcString = None,
              mask: IrcString = None,
              event: IrcString = None,
              target: IrcString = None,
              data: IrcString = None) -> None:
        # Ignore messages sent to channels
        if target.startswith("#"):
            return

        if mask.nick == "NickServ":
            if not self.identified:
                self.identify()
                self.identified = True
            return

        # Forward any PMs to admin
        if mask.nick != config.admin:
            self.bot.privmsg(config.admin, "{} {}".format(mask.nick, data))
            return

        # Echo non-command admin PMs to the channel
        if not data.startswith("?"):
            self.bot.privmsg(config.channel, data)
            return

    # Identify with NickServ
    def identify(self):
        with open(self.password_file) as file:
            password: str = file.readline().strip("\n")
            self.bot.privmsg("NickServ", "identify {}".format(password))
