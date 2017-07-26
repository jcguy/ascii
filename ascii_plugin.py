# -*- coding: utf-8 -*-
from irc3.plugins.command import command
from irc3 import rfc
from time import sleep
import irc3


@irc3.plugin
class Plugin(object):
    whitelist = {}
    registered = False

    admin = "Rhet"
    mods = ["Wildbow"]

    # Start the bot, and initialize the whitelist with the current contents
    # of the whitelist file
    def __init__(self, bot):
        self.bot = bot
        self.update_whitelist()

    # Reads in the file named "whitelist", building a dictionary where
    # each line starting with a # is a nick comment, and the following lines
    # are some identifying component of the user's mask
    def update_whitelist(self):
        self.whitelist = {}
        with open("whitelist", "r") as f:
            key = ""
            for line in f:
                # ignore blank lines
                if line == "\n":
                    continue
                if line.startswith("#"):
                    key = line.strip("#").strip("\n")
                    if not key in self.whitelist.keys():
                        self.whitelist[key] = []
                else:
                    self.whitelist[key].append(line.strip("\n").lower())

    # Kicks the given user from the given channel
    def kick(self, channel, nick):
        return
        self.bot.kick(channel,
                      nick,
                      reason="This channel is the property of the "
                             "People's Front of Judea!")

    # Forward permissions errors to admin
    @irc3.event(rfc.ERR_CHANOPRIVSNEEDED)
    def myevent(self, srv=None, me=None, channel=None, data=None):
        self.bot.privmsg(self.admin, "{} {} {} {}".format(srv, me, channel, data))

    # As users join, say whether or not they're on the whitelist, and
    # then kick them if they are not
    @irc3.event(rfc.JOIN)
    def debug_joins(self, mask, channel, **kw):
        """Prints out joins

        """
        if mask.nick == self.bot.nick: return

        on_whitelist = False
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
            sleep(1)
            self.kick(channel, mask.nick)

    # Forward any PMs to admin
    @irc3.event(rfc.PRIVMSG)
    def reply(self, tags=None, mask=None, event=None, target=None, data=None):
        if not self.registered \
           and "NickServ" in mask.nick \
           and not target.startswith("#"):
            self.registered = True
            with open("password") as f:
                password = f.readline().strip("\n")
                self.bot.privmsg(mask.nick, "identify {}".format(password))

        if not target.startswith("#"):
            self.bot.privmsg(self.admin,
                             "{} {} {} {} {}"
                                .format(tags, mask, event, target, data))

        if self.admin in mask.nick \
           and not target.startswith("#") \
           and not data.startswith("?"):
            self.bot.privmsg("#theroast", data)


    # Reload the whitelist from the file
    @command(permissions="view")
    def update(self, mask, target, args):
        """Update

            %%update
        """
        self.update_whitelist()
        yield "Updated whitelist"

    # Private message the user the whitelist
    @command(permissions="view")
    def list(self, mask, target, args):
        """List

            %%list
        """
        self.bot.privmsg(mask.nick, str(self.whitelist))

    # Add a user to the whitelist
    @command(permissions="admin")
    def add(self, mask, target, args):
        """Add User

            %%add <user> <key>
        """
        with open("whitelist", "a") as f:
            f.writelines("#" + args["<user>"] + "\n")
            f.writelines(args["<key>"] + "\n")

        self.update_whitelist()
        yield "Added user {} ({})".format(args["<user>"],
                                          args["<key>"])
