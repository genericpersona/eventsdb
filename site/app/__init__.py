# -*- coding: utf-8 -*-

import re
import time

from flask import Flask, g, render_template, request

from flask.ext.pymongo import ASCENDING, PyMongo

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
        return re.compile(s)
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

def get_events(findd, page=1, limit=None, sortts=(u'ts', ASCENDING)):
    '''Retrieve events from the DB based on the parameters
    specified.

    This is a general function to be used by all URLs responsible
    for displaying events to the client.
    '''
    limit = limit or app.config['LIMIT_PER_PAGE']
    skip = limit * (page - 1)
    events = mongo.db.events.find(findd, limit=limit, skip=skip)
    return events.sort([sortts])

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
    events = rargs.get(u'events', u'')
    mode = []   # List to hold options for the mode parameter
    if events:
        events_regex = []
        for event in events.split(u'+'):
            if event in all_events():
                events_regex.append(event)

        if events_regex:
            findd[u'events'] = {u'type': \
                    re.compile(u'|'.join(events_regex), re.IGNORECASE)}

    try:
        page = int(request.args['page'])
    except:
        page = 1

    try:
        limit = int(request.args['limit'])
    except:
        limit = app.config['LIMIT_PER_PAGE']

    return page, limit

def replace_page(url, page):
    '''Replace a page parameter in the URL passed in with
    the page number passed in.
    '''
    new_url = PAGE_REGEX.sub('page={}'.format(page), url)
    if not 'page=' in url and new_url == url:
        new_url = '{}?page={}'.format(new_url, page)

    return new_url

@app.before_request
def to_g():
    '''Add needed functions to g
    '''
    for func in ('epoch_to_str', 'replace_page'):
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

@app.route('/full/<nick>/<user>/<host>')
def full(nick, user, host):
    # Start off with a dict for passing to find
    findd = { u'nick': deal_with_wildcard(nick)
            , u'user': deal_with_wildcard(user)
            , u'host': deal_with_wildcard(host)
            }

    # Add to findd and get the page and limit params
    page, limit = parse_get_params(findd, request.args)

    return render_template('events.html', 
            events=get_events(findd, page, limit), 
            page=page, 
            title=u'{}!~{}@{}'.format(nick, user, host))

@app.route('/geoip')
def geoip():
    # Start off with a dict for passing to find and add params
    findd = { u'geoip': {}}

    for param in all_geoip_params():
        if param.lower() in request.args:
            if param == u'IP':
                findd[param.lower()] = request.args[param.lower()]
            else:
                findd['geoip'][param.lower()] = request.args[param.lower()]

    return render_template('events.html', 
            events=get_events(findd, page, limit), 
            page=page, 
            title=u'GeoIP')

@app.route('/')
def home():
    return render_template('home.html')

@app.route('/host/<hostname>')
def host(hostname):
    # Start off with a dict for passing to find
    findd = {u'host': deal_with_wildcard(hostname)}

    # Add to findd and get the page and limit params
    page, limit = parse_get_params(findd, request.args)

    return render_template('events.html', 
            events=get_events(findd, page, limit), 
            page=page, 
            title=hostname)

@app.route('/nick/<nickname>')
def nick(nickname):
    # Start off with a dict for passing to find
    findd = {u'nick': deal_with_wildcard(nickname)}

    # Add to findd and get the page and limit params
    page, limit = parse_get_params(findd, request.args)

    return render_template('events.html', 
            events=get_events(findd, page, limit), 
            page=page, 
            title=nickname)

@app.route('/user/<username>')
def user(username):
    # Start off with a dict for passing to find
    findd = {u'user': deal_with_wildcard(username)}    

    # Add to findd and get the page and limit params
    page, limit = parse_get_params(findd, request.args)

    return render_template('events.html', 
            events=get_events(findd, page, limit), 
            page=page, 
            title=username)

