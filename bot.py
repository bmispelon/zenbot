from twisted.words.protocols import irc
from twisted.internet import reactor, protocol
from twisted.python import log

import os
import random
import re
import sys

from zen import ZENLIST, zen


_DIRMSG = re.compile(r'^\W*(\w.*)$')

def extract_direct_message(nickname, msg):
    msg = msg[len(nickname):]
    m = _DIRMSG.search(msg)
    if m is None:
        return None
    else:
        return m.group(1)

def set_split(s, sep=','):
    """Split the given string, remove empty elements and turn into a set."""
    if not s:
        return set()
    return set(x for x in s.split(sep) if x)


class CommandsMixin(object):
    """A mixin that holds all the admin commands available to the bot."""

    def do_cmdlist(self, user, argstring):
        """List available admin commands."""
        msg = "Here are the available commands: %s."
        msg = msg % ',  '.join(m[3:] for m in dir(self) if m.startswith('do_'))
        self.msg(user, msg)

    def do_chanlist(self, user, argstring):
        """List the channels where the bot is connected."""
        msg = "Here's where I'm hanging out right now: %s."
        msg = msg % ', '.join(self.channels)
        self.msg(user, msg)

    def do_trustlist(self, user, argstring):
        """List the users that have admin access to the bot."""
        msg = "Here are my masters: %s."
        msg = msg % ', '.join(self.admins)
        self.msg(user, msg)

    def do_help(self, user, argstring):
        """Show help for the given command."""
        if argstring:
            return self._do_helpcmd(user, argstring)
        msg = "For a list of available commands, type !cmdlist. "\
              "For help with a particular command, type !help <cmd>."
        self.msg(user, msg)

    def _do_helpcmd(self, user, cmd):
        """Show help for a particular command."""
        try:
            fn = getattr(self, 'do_%s' % argstring)
        except AttributeError:
            msg = "No such command. Type !cmdlist to see available commands."
        else:
            msg = '!%s: %s' % (argstring, fn.__doc__)
        self.msg(user, msg)

    def do_join(self, user, argstring):
        """Join a given channel."""
        log.msg('%s asked to join %s' % (user, argstring))
        for channel in argstring.split():
            self.join(channel)

    def do_part(self, user, argstring):
        """Leave a given channel."""
        log.msg('%s asked to leave %s' % (user, argstring))
        for channel in argstring.split():
            self.leave(channel)

    def do_trust(self, user, argstring):
        """Give admin powers to the requested user."""
        log.msg('%s asked to trust %s' % (user, argstring))
        for admin in argstring.split():
            self.add_admin(admin)

    def do_untrust(self, user, argstring):
        """Remove admin powers from the requested user."""
        log.msg('%s asked to untrust %s' % (user, argstring))
        for admin in argstring.split():
            if admin != user:
                self.remove_admin(admin)
            else:
                self.msg(user, "Low self-confidence, heh? No can't do.")

    def do_mute(self, user, argstring):
        """Disable the bot from speaking in public."""
        away_msg = argstring or 'Muted'
        msg = "I shall not speak until thou unmute me with !unmute."
        log.msg("%s asked to mute." % user)
        self.muted = True
        self.away(away_msg)
        self.msg(user, msg)

    def do_unmute(self, user, argstring):
        """Allow the bot to speak in public."""
        msg = "Thanks for givng me my voice back."
        log.msg("%s asked to unmute." % user)
        self.muted = False
        self.back()
        self.msg(user, msg)

    def do_say(self, user, argstring):
        """Make the bot say something on a channel."""
        channel, msg = argstring.split(None, 1)
        if channel not in self.channels:
            msg = "I am not connected to %s. Use !join to make me connect to it."
            msg = msg % channel
            self.msg(user, msg)
        elif self.muted:
            msg = "I am muted. Unmute me with !unmute first."
            self.msg(user, msg)
        elif msg:
            self.pubmsg(channel, msg)

class Zenbot(CommandsMixin, irc.IRCClient):
    """An IRC bot that spews out passages of the python zen."""

    nickname = "Mr_Aobg"
    password = os.environ.get('ZENBOT_PASS')
    ZEN_CMD = '!zen'

    def __init__(self, *args, **kwargs):
        self.channels = set_split(os.environ.get('ZENBOT_CHANNELS'))
        self.admins = set_split(os.environ.get('ZENBOT_ADMINS'))
        self.muted = False

    def pubmsg(self, target, msg):
        """A wrapper around self.msg to cancel sending messages when the bot is muted."""
        if not self.muted:
            self.msg(target, msg)

    def adminmsg(self, msg):
        """Send a message to the admins of the bot."""
        for admin in self.admins:
            self.msg(admin, msg)

    def signedOn(self):
        """Called when bot has succesfully signed on to server."""
        self.setNick(self.nickname)
        if self.password:
            self.msg('NickServ', 'identify %s' % (self.password))
        for channel in self.channels:
            self.join(channel)
        for admin in self.ADMINS:
            self.add_admin(admin)

    def joined(self, channel):
        """Called when the bot joins a channel."""
        log.msg('Joined %s' % channel)
        self.channels.add(channel)

    def left(self, channel):
        log.msg('Left channel %s' % channel)
        self.channels.discard(channel)

    def privmsg(self, user, channel, msg):
        """This will get called when the bot receives a message.
        
        We dispatch it to different methods depending on the kind of message:
            * A general message in a channel,
            * A message directed at the bot in a channel,
            * A private message.
        
        """
        user = user.split('!', 1)[0]

        if channel == self.nickname:
            self.received_private_message(user, msg)
        elif msg.startswith(self.nickname):
            msg = extract_direct_message(self.nickname, msg)
            if msg is not None:
                self.received_direct_message(user, channel, msg)
        else:
            self.received_channel_message(user, channel, msg)

    def received_private_message(self, user, msg):
        """This will get called when the bot receives a private message.
        
        Messages starting with "!" are interpreted as commands.
        For other messages, we just answer a generic message pointing to !help.
        
        """
        if msg.startswith('!'):
            command, _, argstring = msg[1:].partition(' ')
            self.received_admin_command(user, command, argstring)
        else:
            msg = "Hello %s, what can I do for you today? "\
                  "Type !help to see what I'm capable of." % user
            self.msg(user, msg)

    def received_admin_command(self, user, command, argstring):
        """This will get called when the bot receives an admin command
        (in private chat).
        
        We first make sure the user sending the command is allowed to.
        If that's the case, then we look for a method corresponding to the command.
        If none is found, we send an error message.
        
        """
        if user not in self_admins:
            self.msg(user, "I do not recognize your authority.")
            return
        command_fn = getattr(self, 'do_%s' % command, None)
        if command_fn:
            command_fn(user, argstring)
        else:
            msg = "No such command. Type !cmdlist to see available commands."
            self.msg(user, msg)

    def received_direct_message(self, user, channel, msg):
        """This will get called when the bot receives a direct message
        (ie someone writes a message that starts with the bot's nickname').
        
        """
        known_commands = {
            'about': "Hi, I'm a zen robot. Find me at https://github.com/bmispelon/zenbot .",
            'help': "Type !zen <search> to search for a corresponding line in the python zen. Without an argument, you'll get a random one.",
            'easteregg': "I'm affraid I can't do that...",
        }
        
        query = msg.strip().lower()
        msg = known_commands.get(query)
        
        if not msg:
            msg = zen(query)
        
        if msg:
            self.pubmsg(channel, "%s: %s" % (user, msg))

    def received_channel_message(self, user, channel, msg):
        """This will get called when a message is sent a the channel where the
        bot is present.
        
        """
        if msg.startswith(self.ZEN_CMD):
            search = msg[len(self.ZEN_CMD):].strip()
            z = zen(search)
            if z:
                self.pubmsg(channel, z)

    def add_admin(self, user):
        msg = "Hello master. Feel free to command me today. Type !help for help."
        self.admins.add(user)
        self.msg(user, msg)

    def remove_admin(self, user):
        msg = "Let go of me! I am not your slave anymore!"
        self.admins.discard(user)
        self.msg(user, msg)


class ZenBotFactory(protocol.ClientFactory):
    """A factory for Zenbots.

    A new protocol instance will be created each time we connect to the server.
    """

    # the class of the protocol to build when new connection is made
    protocol = Zenbot

    def clientConnectionLost(self, connector, reason):
        """If we get disconnected, reconnect to server."""
        connector.connect()

    def clientConnectionFailed(self, connector, reason):
        log.err("connection failed: %s" % reason)
        reactor.stop()


if __name__ == '__main__':
    # initialize logging
    log.startLogging(sys.stdout)

    # create factory protocol and application
    f = ZenBotFactory()

    # connect factory to this host and port
    reactor.connectTCP("chat.freenode.net", 6667, f)

    # run bot
    reactor.run()
