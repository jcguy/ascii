# -*- coding: utf-8 -*-
from typing import List

import irc3
from irc3 import rfc
from irc3.plugins.command import command
from irc3.utils import IrcString


@irc3.plugin
class Plugin(object):
    whitelist: dict = {}
    identified: bool = False

    admin: str = "Rhet"
    mods: List[str] = ["Wildbow"]
    channel: str = "#theroast"

    whitelist_file: str = "whitelist"
    password_file: str = "password"

    # Start the bot, and initialize the whitelist with the current contents
    # of the whitelist file
    def __init__(self, bot: irc3.IrcBot):
        self.bot = bot
        self.update_whitelist()

    # Reads in the file named "whitelist", building a dictionary where
    # each line starting with a # is a nick comment, and the following lines
    # are some identifying component of the user's mask
    def update_whitelist(self) -> None:
        self.whitelist = {}
        with open(self.whitelist_file, "r") as f:
            key: str = ""
            for line in f:
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
        self.bot.privmsg(self.admin, "Kicking {}.".format(nick))
        self.bot.kick(channel,
                      nick,
                      reason="This channel is the property of the "
                             "People's Front of Judea!")

    # Forward permissions errors to admin
    @irc3.event(rfc.ERR_CHANOPRIVSNEEDED)
    def forward(self, srv: IrcString, me: IrcString, channel: IrcString,
                data: IrcString) -> None:
        self.bot.privmsg(self.admin,
                         "{} {} {} {}".format(srv, me, channel, data))

    # As users join, say whether or not they're on the whitelist, and
    # then kick them if they are not
    @irc3.event(rfc.JOIN)
    def debug_joins(self, mask: IrcString, channel: IrcString) -> None:
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

    # Handle messages received
    @irc3.event(rfc.PRIVMSG)
    def reply(self, tags: IrcString, mask: IrcString, event: IrcString,
              target: IrcString, data: IrcString) -> None:
        # Identify with NickServ
        if not self.identified and "NickServ" in mask.nick:
            self.identified = True
            with open(self.password_file) as f:
                password: str = f.readline().strip("\n")
                self.bot.privmsg(mask.nick, "identify {}".format(password))

        # Forward any PMs to admin
        if not target.startswith("#"):
            self.bot.privmsg(self.admin,
                             "{} {} {} {} {}"
                             .format(tags, mask, event, target, data))

        # Echo non-command PMs from the admin to the channel
        if self.admin in mask.nick \
                and not target.startswith("#") \
                and not data.startswith("?"):
            self.bot.privmsg(self.channel, data)

    # Reload the whitelist from the file
    @command(permissions="view")
    def update(self):
        """Update

            %%update
        """
        self.update_whitelist()
        yield "Updated whitelist"

    # Private message the user the whitelist
    @command(permissions="view")
    def list(self, mask):
        """List

            %%list
        """
        self.bot.privmsg(mask.nick, str(self.whitelist))

    # Add a user to the whitelist
    @command(permissions="admin")
    def add(self, args):
        """Add User

            %%add <user> <key>
        """
        with open(self.whitelist_file, "a") as f:
            f.writelines("#" + args["<user>"] + "\n")
            f.writelines(args["<key>"] + "\n")

        self.update_whitelist()
        yield "Added user {} ({})".format(args["<user>"],
                                          args["<key>"])
