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
        # Identify with NickServ
        if not self.identified and "NickServ" in mask.nick:
            self.identified = True
            with open(self.password_file) as f:
                password: str = f.readline().strip("\n")
                self.bot.privmsg(mask.nick, "identify {}".format(password))

        # Forward any PMs to admin
        if not target.startswith("#") \
                and "NickServ" not in mask.nick \
                and config.admin not in mask.nick:
            self.bot.privmsg(config.admin, "{} {}".format(mask, data))

        # Echo non-command PMs from the admin to the channel
        if config.admin in mask.nick \
                and not target.startswith("#") \
                and not data.startswith("?"):
            self.bot.privmsg(config.channel, data)
