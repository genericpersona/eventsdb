# -*- coding: utf-8 -*-

from Queue import Queue
import re
import shlex
import subprocess as sp
import traceback

import requests

from utils.ip_regex import ipv4_address, ipv6_address

# Constants and globals
GEOIP_URL = 'http://www.telize.com/geoip/{}'
GEOIP_CACHE = {}
GEOIP_CACHE_MAX = 200
GEOIP_QUEUE = Queue(GEOIP_CACHE_MAX)

def extract_hostname(host):
  '''
  Extract a hostname if one is available.

  Otherwise, return an empty string.
  '''
  h = host
  if u'/' in host:
      for name in host.split(u'/'):
          if u'.' in name:
              h = name
              break

  if u'.' not in h:
    h = u''
  elif valid_hostname(h):
    h = host

  return h

def find_ip_info(host):
  '''
  Given an IRC hostname, look for an IPv4 or
  IPv6 address.  If one is found either directly
  in the hostname or as a result of a reverse 
  DNS lookup, a dict is returned such that:
    
    { 'ip'    : string of IP address
    , 'geoip' : dict of GeoIP data
    }

  If no IP address is found, the following dict
  is returned:

    { 'ip'    : u''
    , 'geoip' : {}
    }
  '''
  if type(host) == str:
      host = unicode(host)
  host = host.strip()
  ipaddr = None

  # Run a regex to look for an IP address
  ips = ipv4_address.findall(host) or ipv6_address.findall(host)
  if ips:
    ipaddr = ips[0].strip()

  # If that doesn't find anything, try a DNS lookup
  host = extract_hostname(host)
  if ipaddr is None and host:
    try:
      cmd = 'dig +short {}'.format(host)
      o = sp.check_output(shlex.split(cmd)).strip()
      if o:
        ipaddr = o
        if type(ipaddr) == str:
            ipaddr = unicode(ipaddr)
    except sp.CalledProcessError:
      pass

  # Return what we have
  return { u'ip'    : ipaddr if ipaddr is not None else u''
         , u'geoip' : geoip(ipaddr) if ipaddr is not None else {}
         }

def geoip(ip):
  '''
  Use telize.com to perform a GeoIP lookup.

  If an error occurs, an empty dict is returned,
  otherwise the full JSON response is returned
  as a dict.
  '''
  # Check the cache
  global GEOIP_CACHE, GEOIP_QUEUE
  if ip in GEOIP_CACHE:
      return GEOIP_CACHE[ip]

  try:
    r = requests.get(GEOIP_URL.format(ip))
    if r.status_code != 200:
      return {}

    if GEOIP_QUEUE.full():
        del GEOIP_CACHE[GEOIP_QUEUE.get()]

    GEOIP_CACHE[ip] = r.json()
    GEOIP_QUEUE.put(ip)

    return GEOIP_CACHE[ip]
  except:
    return {}

def mode_dict(plus, by, flag):
  '''
  Assemble mode change information and return a
  dict representation suitable for inserting
  into the events mongodb collection.

  Only handles one mode change at a time since
  each individual change counts as a separate
  event.

  Only care about the following modes:

    +/-b
    +/-o
    +/-q
    +/-v

  If any other mode is changed, return an empty
  dict.

  Params
  ------
    plus: bool
      Whether this is a + or -

    by: string
      full nick!~user@host who changed the mode

    flag: string
      all flags set or unset
  '''
  if flag not in ('b', 'o', 'q', 'v'):
    return {}

  eventd = { u'type': u'mode'
           , u'plus': plus
           , u'by': by
           , u'flag': flag
           }
  return eventd

def parse_client_name(full_cn, safe=False):
  '''
  Parse a nick!~user@host into a 3-tuple of the
  constituent fields:

    (nick, user, host)

  Return a dictionary with the following keys:

    u'nick'
    u'user'
    u'host'

  If an error occurs and safe is False, raise 
  an AttributeError.  Otherwise, return a
  dictionary with the u'user' and u'host' values
  set to the empty string.

  Params
  ------
    full_cn: string
      The full client name
  '''
  try:
    nick, rest = full_cn.split('!')
    user, host = rest.lstrip('~').split('@')

    # Deal with the case where a $ is used 
    # in a ban or quiet and throw away the
    # part after the $
    host = host.split('$')[0]

    # Return the dict
    return { u'nick': nick
           , u'user': user
           , u'host': host
           }
  except:
    if not safe:
      #print traceback.format_exc()
      raise AttributeError
    else:
      return { u'nick': full_cn
             , u'user': u''
             , u'host': u''
             }

def valid_hostname(hn):
  '''
  Return True if hn is a valid hostname.
 
  Taken from:
    https://stackoverflow.com/questions/2532053/validate-a-hostname-string
  '''
  if len(hn) > 255:
    return False
  if hn.endswith("."): # A single trailing dot is legal
    hn = hn[:-1] # strip exactly one dot from the right, if present
  disallowed = re.compile("[^A-Z\d-]", re.IGNORECASE | re.UNICODE)
  return all( # Split by labels and verify individually
    (label and len(label) <= 63 # length is within proper range
     and not label.startswith("-") and not label.endswith("-") # no bordering hyphens
     and not disallowed.search(label)) # contains only legal characters
    for label in hn.split("."))
