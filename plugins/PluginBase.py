# -*- coding: utf-8 -*-

class PluginBase(object):
    def __init__(self, conf):
        '''
        Base class for all of BaneBot's plugins.

        Saves the config dict's members as 
        attributes of the object
        '''
        for k, v in conf.iteritems():
            setattr(self, k, v)

class CommandPlugin(PluginBase):
    def __init__(self, conf):
        '''
        Base class for BaneBot's command plugins.
        '''
        super(CommandPlugin, self).__init__(conf)

        # Help dictionary for mapping a command
        # to a help message
        self._helpd = {}

    def commands(self):
        '''
        Return a dictionary where

            k -> non-prefixed command name as a string
            v -> function responsible for handling the
                 command

        The function/method reponsible for handling the
        command should return a string if it has a response
        and None otherwise. It should take a list of args
        and a BaneBot object as its parameters.
        '''
        raise NotImplementedError

    def help(self, command):
        '''
        Return a string help message for the given command
        or None if command isn't supported
        '''
        if command in self.commands():
            if command in self.helpd:
                return self.helpd[command]
            else:
                return self.commands()[command].__doc__

class LinePlugin(PluginBase):
    def __init__(self, conf):
        '''
        Base class for BaneBot's plugins which need to
        examine every privmsg for a possible response.
        '''
        super(LinePlugin, self).__init__(conf)

    def hasResponse(self, msg, irc):
        '''
        For plugins which need to examine every privmsg
        being sent for a possible response, e.g., to give
        information about a YouTube link, this method must
        be implemented.

        Return True if the msg passed in, considering any
        relevant state in the irc object, has a response.

        If True is returned the reponse must be saved as
        a unicode object in irc.response

        Parameters
        ----------
            msg : string
                msg is the text seen in a privmsg

            irc : BaneBot
                irc is a BaneBot object
        '''
        raise NotImplementedError

class CommandError(Exception):
    def __init__(self, message, pm=True):
        # Call the base class constructor with the parameters it needs
        super(ValidationError, self).__init__(message)

        # Whether this should be sent as a PM
        self.pm = pm
