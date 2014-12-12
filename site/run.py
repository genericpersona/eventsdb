#!/usr/bin/env python
# -*- coding: utf-8 -*-

from gevent.wsgi import WSGIServer

from app import app

http_server = WSGIServer(('', 8080), app)
http_server.serve_forever()
