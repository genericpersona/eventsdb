# -*- coding: utf-8 -*-

import fnmatch
import os
import re
import time

from flask import Flask, g, render_template, request

from flask.ext.pymongo import DESCENDING, PyMongo

# Set up the Flask app
app = Flask(__name__)

# Configurations
app.config.from_object('config')

# Database setup and functions
mongo = PyMongo(app)

# Page regex
PAGE_REGEX = re.compile(r'page=\d+')

def all_events():
    '''Return a tuple of all supported event types.
    '''
    return (u'join', u'kick', u'mode', u'part', u'quit', u'rename')

def all_geoip_params():
    '''Return a tuple of all supported geoip parameters.
    '''
    return (u'ASN', u'CC', u'City', u'Country', u'IP', u'ISP', u'Region')

def deal_with_wildcard(s):
    '''Return a REGEX object if a wildcard is involved
    '''
    if '*' in s: 
        return re.compile(fnmatch.translate(s))
    else:
        return s

def epoch_to_str(ets, time_format='%d %b %Y %H:%M:%S'):
    '''Convert an epoch timestamp in UTC
    to a given time format string.

    Params:
        ets: int
            Epoch Time Stamp in UTC

        time_format: string
            Time format string (http://strftime.org/)
    '''
    return time.strftime(time_format, time.gmtime(ets))

def event_to_str(eventd):
    '''Convert an event dict into a descriptive string.
    '''
    if eventd[u'type'] == u'join':
        return u'Join'

    elif eventd[u'type'] == u'quit':
        return u'Quit{}'.format(u' ({})'.format(eventd[u'reason']))

    elif eventd[u'type'] == u'rename':
        return u'Rename to {}'.format(eventd[u'newname'])

    elif eventd[u'type'] == u'part':
        return u'Part{}'.format(u' ({})'.format(eventd[u'reason']))

    elif eventd[u'type'] == u'kick':
        kickee = u'{}'.format(eventd[u'by'][u'nick'])
        return u'Kicked by {}{}'.format(kickee, 
                            u' ({})'.format(eventd[u'reason']))

    elif eventd[u'type'] == u'mode':
        sign = u'+' if eventd[u'plus'] else u'-'
        setter = eventd[u'by'][u'nick']
        return u'Mode {}{} by {}'.format(sign, eventd[u'flag'], setter)

    else:
        return eventd[u'type']

def get_events(findd, page=1, limit=None, sortts=(u'ts', DESCENDING)):
    '''Retrieve events from the DB based on the parameters
    specified.

    This is a general function to be used by all URLs responsible
    for displaying events to the client.
    '''
    limit = limit or app.config['LIMIT_PER_PAGE']
    skip = limit * (page - 1)
    events = mongo.db.events.find(findd, limit=limit, skip=skip)
    return events.sort([sortts])

def get_events_count(findd):
    '''Retrieve count of events from the DB based on the parameters
    specified.
    '''
    return mongo.db.events.find(findd).count()

def num_results(total, page, limit):
    '''Return the number of results that should be shown on a page
    given the total number of results, the current page, and the
    limit per page.
    '''
    if page > total_pages(total, limit):
        return 0

    return total - ((page - 1) * limit)

def parse_get_params(findd, rargs):
    '''Add parameters to a dictionary for passing
    to MongoDB's find given the GET requests params.

    Return the page and limit after parsing.

    Parameters
    ----------
        findd: dict
            The dict to be passed to find
            Modified after execution of this function

        rargs: dict
            The GET parameters in dict form
    '''
    events = rargs.get(u'event', u'')
    events_regex = []
    if events:
        for event in events.split(u'+'):
            if event.lower() in all_events():
                events_regex.append(event.lower())

        if events_regex:
            findd[u'event.type'] = re.compile(u'|'.join(events_regex)) 

    if u'mode' in events_regex:
        parse_mode_params(findd, rargs)

    try:
        limit = int(request.args['limit'])
    except:
        limit = app.config['LIMIT_PER_PAGE']

    try:
        page = int(request.args['page'])
    except:
        page = 1

    return page, limit

def parse_mode_params(findd, rargs):
    '''Parse the GET parameters for querying the DB for different
    mode settings.

    Modifies the findd passed in.
    '''
    flags = rargs.get(u'flag', u'')
    if flags:
        flags_regex = []
        for flag in flags.split(u'+'):
            if flag in (u'b', u'o', u'q', u'v'):
                flags_regex.append(flag)

        if flags_regex:
            findd[u'event.flag'] = re.compile(u'|'.join(flags_regex))

    plus = rargs.get(u'plus', u'')
    if plus:
        if plus.lower() == u'true':
            findd[u'event.plus'] = True
        elif plus.lower() == u'false':
            findd[u'event.plus'] = False

def replace_page(url, page):
    '''Replace a page parameter in the URL passed in with
    the page number passed in.
    '''
    new_url = PAGE_REGEX.sub('page={}'.format(page), url)
    if not 'page=' in url and new_url == url:
        new_url = '{}{}page={}'.format(new_url, 
                '&' if '?' in url else '?', 
                page)

    return new_url

def total_pages(total, limit):
    '''Return the number of pages given the total results
    and the limit of results per page.
    '''
    q, r = divmod(total, limit)
    if r == 0:
        return q
    else:
        return q + 1

@app.before_request
def to_g():
    '''Add needed functions to g
    '''
    funcs = ( 'epoch_to_str'
            , 'event_to_str'
            , 'num_results'
            , 'replace_page'
            , 'total_pages'
            )
    for func in funcs:
        if not hasattr(g, func):
            setattr(g, func, eval(func))

# Error Handling
@app.errorhandler(404)
def not_found(error):
    return render_template('404.html'), 404

# Routing
@app.route('/about')
def about():
    return render_template('about.html')

@app.route('/full/<nick>/<user>/<path:host>')
def full(nick, user, host):
    # Start off with a dict for passing to find
    findd = { u'nick': deal_with_wildcard(nick)
            , u'user': deal_with_wildcard(user)
            , u'host': deal_with_wildcard(host)
            }

    # Add to findd and get the page and limit params
    page, limit = parse_get_params(findd, request.args)

    return render_template('events.html', 
            count=get_events_count(findd),
            events=get_events(findd, page, limit), 
            limit=limit,
            page=page, 
            title=u'{}!~{}@{}'.format(nick, user, host))

@app.route('/geoip')
def geoip():
    # Start off with a dict for passing to find and add params
    findd = {}

    for param in all_geoip_params():
        if param.lower() in request.args:
            findd[u'geoip.{}'.format(param.lower())] = \
                        deal_with_wildcard(request.args[param.lower()])

    # Add to findd and get the page and limit params
    page, limit = parse_get_params(findd, request.args)

    return render_template('events.html', 
            count=get_events_count(findd),
            events=get_events(findd, page, limit), 
            limit=limit,
            page=page, 
            title=u'GeoIP')

@app.route('/')
def home():
    return render_template('home.html')

@app.route('/host/<path:hostname>')
def host(hostname):
    # Start off with a dict for passing to find
    findd = {u'host': deal_with_wildcard(hostname)}

    # Add to findd and get the page and limit params
    page, limit = parse_get_params(findd, request.args)

    return render_template('events.html', 
            count=get_events_count(findd),
            events=get_events(findd, page, limit), 
            limit=limit,
            page=page, 
            title=hostname)

@app.route('/nick/<nickname>')
def nick(nickname):
    # Start off with a dict for passing to find
    findd = {u'nick': deal_with_wildcard(nickname)}

    # Add to findd and get the page and limit params
    page, limit = parse_get_params(findd, request.args)

    return render_template('events.html', 
            count=get_events_count(findd),
            events=get_events(findd, page, limit), 
            limit=limit,
            page=page, 
            title=nickname)

@app.route('/user/<username>')
def user(username):
    # Start off with a dict for passing to find
    findd = {u'user': deal_with_wildcard(username)}    

    # Add to findd and get the page and limit params
    page, limit = parse_get_params(findd, request.args)

    return render_template('events.html', 
            count=get_events_count(findd),
            events=get_events(findd, page, limit), 
            limit=limit,
            page=page, 
            title=username)

# Robots need not apply
@app.route('/robots.txt')
def robots():
    return app.send_static_file(os.path.join('static', 'robots.txt'))
