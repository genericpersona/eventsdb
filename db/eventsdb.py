# -*- coding: utf-8 -*-

import traceback

from pymongo import MongoClient
from twisted.python import log

class EventsDB(object):

    def __init__(self, host = 'localhost', port = 27017, 
            db_name = 'eventsdb', collection_name = 'events'):
        self.client = MongoClient(host, port)
        self.db = self.client[db_name]
        self.events = self.db[collection_name]

    def addEvent(self, eventd):
        """
        Insert an event dict into the collection referenced
        by the self.events attribute.

        Can bulk insert by passing in a list of event dicts.
        
        An event dict contains the following fields:
        
                 ts: int    (Epoch timestamp)
               nick: string
               user: string
               host: string
            channel: string (Empty string for rename and quit)
                 ip: string
              geoip: dict
              event: dict
        
        The geoip dict is defined by the Telize JSON API
        defined at:
        
            http://www.telize.com/
        
        The event dict has different keys based on the type of
        event.  Every event dict has the key:
        
             type: string   (one of join, kick, mode, part, quit, rename)
        
        Each of the events has the following unique fields:
        
            Type        Fields
            ----        ------
        
            join        None
        
            kick        reason (string)
                        by     (dict)   # nick, user, host
        
            mode        plus   (bool)   # Whether mode was + or -
                        by     (dict)   # nick, user, host
                        flag   (string)
                        args   (string)
        
            part        reason (string)
        
            quit        reason (string)
        
            rename      newname (string)
                        
        Note: mode is only logged if it's changed on a user
        """
        return self.events.insert(eventd)

def getEvent(q, edb):
    '''
    Used to implement an event's database worker 
    to watch a queue object for dicts representing
    an event.  After get()'ing an event dict it is
    inserted into the EventsDB.
    '''
    while True:
        eventd = q.get()
        log.msg('Adding event to the database')
        try:
            edb.addEvent(eventd)
        except:
            log.err('Traceback: {}'.format(traceback.print_exc()))
