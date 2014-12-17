#!/usr/bin/zsh

##
## Add iptables redirection to not have to run the
## app under root at any time
##
iptables -t nat -A PREROUTING -p tcp --dport 80 -j REDIRECT --to-port 8080

##
## uwsgi running the app w/o a web server
##
uwsgi --http :8080 --module eventsdb --callable app \
  --processes 4 --threads 2 --stats 127.0.0.1:9191 \
  --uid 1001 --gid 1001 --daemonize ../logs/uwsgi.log

