#!/usr/bin/env python2
# -*- coding: utf-8 -*-

import re
import shlex
import subprocess as sp
import sys

from db.eventsdb import EventsDB
import utils.irc as ui

# Constants
CHANNEL = '#bitcoin-otc'
JOIN_RE = re.compile(' has joined {} '.format(CHANNEL))
KICK_RE = re.compile(' has kicked ')
KICK_ALL_RE = re.compile(r'(?P<by>.*) has kicked (?P<nick>.*) \((?P<reason>.*)\)')
LOGE_RE = re.compile('--|<--|-->')
MODE_RE = re.compile(r'Mode {} '.format(CHANNEL) + \
    r'\[(?P<plus>\+|-)(?P<flags>\w+) (?P<args>.+)\] ' + \
    r'by (?P<by>.+)')
MODE_RE2 = re.compile(r'Mode {} \[(?P<all>.*)\] by (?P<by>.+)'.format(CHANNEL))
NICK_RE = re.compile(r'[A-Za-z\[\]\\`_\^\{\|\}][A-Za-z0-9\[\]\\`\{\|\}\-]*')
PART_RE = re.compile(' has left ')
QUIT_RE = re.compile(' has quit ')
RENAME_RE = re.compile('(?P<oldname>\S+) is now known as (?P<newname>\S+)')
USER_HOST_RE = re.compile(r'\(~?(?P<user>.*)@(?P<host>.*?)\)')

def parse_join(line):
    '''
    '''
    joind = {}

    # Get the nick
    m = NICK_RE.search(line)
    joind[u'nick'] = line[m.start():m.end()]
    
    # Get the user and host
    m = USER_HOST_RE.search(line)
    joind.update(m.groupdict())

    # Add the event dict
    joind[u'event'] = { u'type': u'join' }

    return joind

def parse_kick(line):
    '''
    '''
    #print('Kick line: {}'.format(line))
    m = KICK_ALL_RE.search(line)
    gd = m.groupdict()

    kickd = {}
    kickd[u'nick'] = gd['nick']
    kickd[u'user'] = u''
    kickd[u'host'] = u''

    try:
        by = ui.parse_client_name(gd['by'])
    except AttributeError:
        by = { u'nick': gd['by']
             , u'user': u''
             , u'host': u''
             }

    kickd[u'event'] = { u'type': u'kick'
                      , u'by': by
                      , u'reason': gd['reason']
                      }
    return kickd

def parse_mode(line):
    '''
    '''
    #print('Mode line: {}'.format(line))
    m = MODE_RE.search(line)
    if m is None:
        m = MODE_RE2.search(line)
    gd = m.groupdict()
    if 'plus' in gd:
        args = gd['args'].split()
        pluses = [gd['plus'] == '+' for _ in range(len(args))]
        flags = gd['flags']
    else:
        allm = gd['all'].split()
        prev_plus = None
        pluses = []
        for plus in allm[0]:
            if plus in '+-':
                prev_plus = plus
            else:
                pluses.append(prev_plus)
        flags = filter(str.isalpha, allm[0])
        args = allm[1:]

    modeds = []
    for i, flag in enumerate(flags):
        if flag not in ('b', 'o', 'q', 'v'):
            continue

        moded = {}
        try:
            moded.update(ui.parse_client_name(args[i]))
        except AttributeError:
            moded[u'nick'] = args[i]
            moded[u'user'] = u''
            moded[u'host'] = u''

        try:
            by = ui.parse_client_name(gd['by'])
        except AttributeError:
            by = { u'nick': gd['by']
                 , u'user': u''
                 , u'host': u''
                 }

        moded[u'event'] = { u'type': u'mode'
                          , u'plus': pluses[i]
                          , u'by': by
                          , u'flag': flag
                          }
        modeds.append(moded)

    return modeds

def parse_part(line):
    '''
    '''
    partd = {}

    # Get the nick
    m = NICK_RE.search(line)
    partd[u'nick'] = line[m.start():m.end()]
    
    # Get the user and host
    m = USER_HOST_RE.search(line)
    partd.update(m.groupdict())

    # Extract the reason if there is one
    reason = ''
    for i in range(line.find('(', line.find(CHANNEL)) + 1, len(line)):
        if line[i] == ')':
            break
        reason += line[i]

    # Add the event dict
    partd[u'event'] = { u'type': u'part' 
                      , u'reason': reason.decode('utf-8')
                      }

    return partd

def parse_quit(line):
    '''
    '''
    #print('Quit line: {}'.format(line))
    quitd = {}

    # Get the nick
    m = NICK_RE.search(line)
    quitd[u'nick'] = line[m.start():m.end()]
    
    # Get the user and host
    m = USER_HOST_RE.search(line)
    quitd.update(m.groupdict())

    # Extract the reason if there is one
    reason = ''
    for i in range(line.find('(', line.find('has quit ')) + 1, len(line)):
        if line[i] == ')':
            break
        reason += line[i]

    # Add the event dict
    quitd[u'event'] = { u'type': u'quit' 
                      , u'reason': reason.decode('utf-8')
                      }

    return quitd

def parse_rename(line):
    '''
    '''
    m = RENAME_RE.search(line)
    gd = m.groupdict()

    renamed = { u'nick': gd['oldname']
              , u'host': u''
              , u'user': u''
              , u'event': { u'type': 'rename'
                          , u'newname': gd['newname']
                          }
              }
    return renamed

def parse_ts(ts_str):
    '''
    '''
    try:
        cmd = 'date --date=\'TZ="America/Los_Angeles" {}\' +%s'.format(ts_str)
        o = sp.check_output(shlex.split(cmd))
        return int(o)
    except: 
        return None

if __name__ == '__main__':
    logf = sys.argv[1]
    edb = EventsDB()
    entryds = []

    for i, entry in enumerate(open(logf)):
        # Print line number
        print('Line number {}'.format(i+1))

        # Get rid of newlines, etc.
        entry = entry.strip()

        entryd = {}

        # Extract the ts
        ts_str_len = len('YYYY-MM-DD HH:MM:SS')
        ts = parse_ts(entry[:ts_str_len])
        if ts is None:
            continue
        entryd[u'ts'] = ts

        # Remove the ts from the entry
        entry = entry[ts_str_len:].strip()
        m = LOGE_RE.match(entry)
        if m is None:
            print('Skipped: {}'.format(entry))
            continue
        else:
            entry = entry[m.end():]

        # Figure out which type of event we have
        # Parse it to get a dict with its info
        # And insert it into the events collection
        if JOIN_RE.search(entry) is not None:
            entryd.update(parse_join(entry))

        elif PART_RE.search(entry) is not None:
            entryd.update(parse_part(entry))

        elif QUIT_RE.search(entry) is not None:
            entryd.update(parse_quit(entry))

        elif RENAME_RE.search(entry) is not None:
            entryd.update(parse_rename(entry))

        elif KICK_RE.search(entry) is not None and CHANNEL not in entry:
            entryd.update(parse_kick(entry))

        elif 'Mode {}'.format(CHANNEL) in entry and ' by ' in entry:
            modeds = parse_mode(entry)
            for moded in modeds:
                moded.update(entryd)
                moded[u'channel'] = CHANNEL
                moded.update(ui.find_ip_info(moded[u'host']))
                #print(moded)
                entryds.append(moded)

            continue

        else:
            continue

        entryd[u'channel'] = CHANNEL
        entryd.update(ui.find_ip_info(entryd[u'host']))
        entryds.append(entryd)
        #print(entryd)

    # Inserting into database
    edb.addEvent(entryds) 
