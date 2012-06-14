from twisted.words.protocols import irc
from twisted.internet import reactor, protocol
from twisted.python import log

import os
import random
import re
import sys

from zen import ZENLIST, find_zen


_DIRMSG = re.compile(r'^\W*(\w.*)$')

def extract_direct_message(nickname, msg):
    msg = msg[len(nickname):]
    m = _DIRMSG.search(msg)
    if m is None:
        return None
    else:
        return m.group(1)

class Zenbot(irc.IRCClient):
    """An IRC bot that spews out passages of the python zen."""

    nickname = "Mr_Aobg"
    password = os.environ.get('ZENBOT_PASS')
    channels = os.environ['ZENBOT_CHANNELS'].split(',')
    ERROR = "I'm afraid I can't do that..."
    ABOUT = "Hi, this is zenbot. Find me at http://github.com/bmispelon/zenbot."
    ADMINS = set(os.environ.get('ZENBOT_ADMINS', '').split(','))
    STFU_CMD = 'STFU!'
    STFU_CMD_OFF = "it's ok"
    stfu = False
    ZEN_CMD = '!zen'

    def msg(self, target, msg):
        """Send a message only if the bot is allowed to talk."""
        if not self.stfu:
            irc.IRCClient.msg(self, target, msg)

    def signedOn(self):
        """Called when bot has succesfully signed on to server."""
        self.setNick(self.nickname)
        if self.password:
            self.msg('NickServ', 'identify %s' % (self.password))
        for channel in self.channels:
            self.join(channel)

    def joined(self, channel):
        """Called when the bot joins a channel."""
        log.msg('Joined %s' % channel)

    def privmsg(self, user, channel, msg):
        """This will get called when the bot receives a message."""
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
        """This will get called when the bot receives a private message."""
        self.msg(user, self.ABOUT)

    def received_direct_message(self, user, channel, msg):
        """This will get called when the bot receives a direct message
        (ie someone writes a message that starts with the bot's nickname').
        
        """
        if msg == self.STFU_CMD:
            self.away('turned off by %s' % user)
            self.stfu = True

        elif self.stfu and user in self.ADMINS and msg == self.STFU_CMD_OFF:
            self.stfu = False
            self.back()

        else:
            self.send_zen(msg, channel, user)

    def received_channel_message(self, user, channel, msg):
        """This will get called when a message is sent to the channel."""
        if msg.startswith(self.ZEN_CMD):
            zen = msg[len(self.ZEN_CMD):].strip()
            self.send_zen(zen, channel)

    def send_zen(self, zen, target, user=None):
        """Find a line that correspond to the given zen keywords and send it
        to the target.
        If not line is found (or if several lines match), send an error message.
        
        """
        msg = self.get_zen(zen)
        if not msg:
            msg = self.ERROR

        if user:
            msg = '%s: %s' % (user, msg)
        self.msg(target, msg)

    def get_zen(self, cmd):
        """Find a line corresponding to the given keywords.
        If no keywords are given, return a random line.
        If no line match, or if several lines do, return None.
        
        """
        return find_zen(cmd) if cmd else random.choice(ZENLIST)


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
