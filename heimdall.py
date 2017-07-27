# -*- coding: utf-8 -*-
# This plugin monitors joins and kicks unlisted users out
from typing import Dict, List

import irc3
from irc3 import rfc
from irc3.plugins.command import command
from irc3.utils import IrcString

import config


@irc3.plugin
class Plugin(object):
    whitelist: Dict[str, List[str]] = {}

    mods: List[str] = ["Wildbow"]
    whitelist_file: str = "whitelist"
    kick_msg: str = "This channel is the property of " \
                    "the People's Front of Judea!"

    # Start the bot, and initialize the whitelist with the current contents
    # of the whitelist file
    def __init__(self, bot: irc3.IrcBot):
        self.bot = bot
        self.update_whitelist()

    # Reads in the whitelist file, building a dictionary where each line
    # starting with a # is a nick comment, and the following lines
    # are some identifying component of the user's mask
    def update_whitelist(self) -> None:
        self.whitelist = {}
        with open(self.whitelist_file, "r") as file:
            key: str = ""
            for line in file:
                # ignore blank lines
                if line == "\n":
                    continue
                if line.startswith("#"):
                    key = line.strip("#").strip("\n")
                    if key not in self.whitelist.keys():
                        self.whitelist[key] = []
                else:
                    self.whitelist[key].append(line.strip("\n").lower())

    # Kicks the given user from the given channel
    def kick(self, channel: IrcString, nick: IrcString) -> None:
        self.bot.privmsg(config.admin, "Kicking {}.".format(nick))
        self.bot.kick(channel, nick, reason=self.kick_msg)

    # As users join, say whether or not they're on the whitelist, and
    # then kick them if they are not
    @irc3.event(rfc.JOIN)
    def on_join(self, mask: IrcString, channel: IrcString) -> None:
        if mask.nick == self.bot.nick:
            return

        on_whitelist: bool = False

        for ident in self.whitelist.values():
            for nick in ident:
                if nick in str(mask).lower():
                    on_whitelist = True
                    break

        if on_whitelist:
            self.bot.privmsg(channel,
                             "Welcome back, {}.".format(mask.nick))
        elif mask.nick in self.mods:
            self.bot.privmsg(channel,
                             "Hello, {}. Welcome to the channel."
                             .format(mask.nick))
        else:
            self.bot.privmsg(channel,
                             "{} is not on the whitelist. Goodbye."
                             .format(mask.nick))
            self.kick(channel, mask.nick)

    # Reload the whitelist from the file
    # noinspection PyUnusedLocal
    @command(permissions="view")
    def update(self, mask, target, args):
        """Update

            %%update
        """
        self.update_whitelist()
        yield "Updated whitelist"

    # Private message the user the whitelist
    # noinspection PyUnusedLocal
    @command(permissions="view")
    def list(self, mask, target, args):
        """List

            %%list
        """
        self.bot.privmsg(mask.nick, str(self.whitelist))

    # Add a user to the whitelist
    # noinspection PyUnusedLocal
    @command(permissions="admin")
    def add(self, mask, target, args):
        """Add User

            %%add <user> <key>
        """
        with open(self.whitelist_file, "a") as f:
            f.writelines("#" + args["<user>"] + "\n")
            f.writelines(args["<key>"] + "\n")

        self.update_whitelist()
        yield "Added user {} ({})".format(args["<user>"],
                                          args["<key>"])
