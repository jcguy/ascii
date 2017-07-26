# -*- coding: utf-8 -*-
from irc3.plugins.command import command
from irc3 import rfc
import irc3

@irc3.plugin
class Plugin(object):
    whitelist = {"test" : ["test"]}
    registered = False

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
    # TODO: doesn't work
    def kick(self, channel, nick):
        self.bot.privmsg(channel, "Kicking {}".format(nick))
        self.bot.kick(channel, nick, reason="Later")

    @irc3.event(rfc.ERR_CHANOPRIVSNEEDED)
    def myevent(self, srv=None, me=None, channel=None, data=None):
        self.bot.privmsg("Rhet", "{} {} {} {}".format(srv, me, channel, data))

    # As users join, say whether or not they're on the whitelist, and
    # then kick them if they are not
    @irc3.event(rfc.JOIN)
    def debug_joins(self, mask, channel, **kw):
        """Prints out joins

        """
        if mask.nick == self.bot.nick: return

        on_whitelist = False
        for ident in self.whitelist.values():
            if ident in str(mask).lower():
                on_whitelist = True
                break

        if on_whitelist:
            self.bot.privmsg(channel,
                             "{} is on the whitelist".format(mask.nick))
        else:
            self.bot.privmsg(channel,
                             "{} is not on the whitelist".format(mask.nick))
            self.kick(channel, mask.nick)

    # Forward any PMs to Rhet
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
            self.bot.privmsg("Rhet",
                             "{} {} {} {} {}"
                                .format(tags, mask, event, target, data))

    # Reload the whitelist from the file
    @command(permissions="view")
    def update(self, mask, target, args):
        """Update

            %%update
        """
        update_whitelist()
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
