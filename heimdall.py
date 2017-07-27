# -*- coding: utf-8 -*-
# This plugin monitors joins, and kicks unlisted users out
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
    whitelist_msg: str = "Welcome back, {}."
    modlist_msg: str = "Howdy, {}. Welcome to the channel."
    kick_msg: str = "{} was not on the whitelist."
    kick_reason: str = "This channel is the property of " \
                       "the People's Front of Judea!"

    def __init__(self, bot: irc3.IrcBot):
        self.bot = bot
        self.update_whitelist()

    # Set self.whitelist to the contents of the whitelist file
    def update_whitelist(self) -> None:
        self.whitelist = {}

        with open(self.whitelist_file, "r") as file:
            key: str = ""
            for line in file:
                # ignore blank lines
                if line == "\n":
                    continue

                # Lines starting with # are just a comment, usually with
                # the nick of the user being identified
                if line.startswith("#"):
                    key = line.strip("#").strip("\n")

                    if key not in self.whitelist.keys():
                        self.whitelist[key] = []
                else:
                    self.whitelist[key].append(line.strip("\n").lower())

    def kick(self, channel: IrcString, nick: IrcString) -> None:
        self.bot.privmsg(config.admin, "Kicking {}.".format(nick))
        self.bot.kick(channel, nick, reason=self.kick_reason)

    # Respond to users joining the channel
    @irc3.event(rfc.JOIN)
    def on_user_join(self, mask: IrcString, channel: IrcString) -> None:
        # Ignore our own join
        if mask.nick == self.bot.nick:
            return

        # Check through the whitelist
        on_whitelist: bool = False
        for ident_list in self.whitelist.values():
            for ident in ident_list:
                if ident in mask.lower():
                    on_whitelist = True
                    break

        if on_whitelist:
            return  # message = self.whitelist_msg.format(mask.nick)
        elif mask.nick in self.mods:
            message = self.modlist_msg.format(mask.nick)
        else:
            message = self.kick_msg.format(mask.nick)
            self.kick(channel, mask.nick)

        self.bot.privmsg(channel, message)

    # noinspection PyUnusedLocal
    @command(permissions="view")
    def update(self, mask, target, args):
        """Reload the whitelist from the file

            %%update
        """
        self.update_whitelist()
        yield "Updated whitelist"

    # noinspection PyUnusedLocal
    @command(permissions="view")
    def list(self, mask, target, args):
        """List the users currently on the whitelist. Warning: lots of PMs

            %%list
        """
        for key, value in self.whitelist.items():
            message: str = "{}: ".format(key)
            for ident in value:
                message += "{} ".format(ident)

            self.bot.privmsg(mask.nick, message)

    # noinspection PyUnusedLocal
    @command(permissions="admin")
    def add(self, mask, target, args):
        """Add a user to the whitelist, using a unique portion of their mask

            %%add <user> <key>
        """
        with open(self.whitelist_file, "a") as f:
            f.writelines("#" + args["<user>"] + "\n")
            f.writelines(args["<key>"] + "\n")

        self.update_whitelist()

        yield "Added user {} ({}) and updated whitelist." \
            .format(args["<user>"], args["<key>"])
