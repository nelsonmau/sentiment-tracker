from google.appengine.ext import webapp
from google.appengine.ext.webapp.util import run_wsgi_app
from google.appengine.ext.webapp import template

import helpers
import urllib2
import urllib
import logging
import os

import models

MIN=60
HOUR=60*MIN


try:
    from django.utils import simplejson
except ImportError:
    try:
        from django.utils import simplejson
    except ImportError:
        import json as simplejson
        
import datetime
        
class MainRequest(webapp.RequestHandler):
    @helpers.write_response
    def get(self, *args):
        pollname = args[0]
        poll = models.Poll.get_by_name(pollname)
        path = os.path.join(os.path.dirname(__file__), "templates", "main.html")
        return template.render(path, {'poll': poll})

class DebugRequest(webapp.RequestHandler):
    @helpers.write_response
    def get(self, *args):
        pollname = args[0]
        poll = models.Poll.get_by_name(pollname)
        path = os.path.join(os.path.dirname(__file__), "templates", "debug.html")
        return template.render(path, {'poll': poll})

class RegisterIncrRequest(webapp.RequestHandler):
    @helpers.write_response
    def get(self, *args):
        pollname = args[0]
        choice = args[1]
        callback = self.request.get('callback')                
        path = os.path.join(os.path.dirname(__file__), "templates", "register.html")
        poll = models.Poll.get_by_name(pollname)
        if poll.open():
            choice = poll.get_choice_by_name(choice)
            logging.info("Got choice %s" % (choice))
            if choice:
                choice.increment()
        return template.render(path, {'callback':callback})
    

class RegisterDecrRequest(webapp.RequestHandler):
    @helpers.write_response
    def get(self, *args):
        pollname = args[0]
        choice = args[1]
        callback = self.request.get('callback')
        path = os.path.join(os.path.dirname(__file__), "templates", "register.html")
        poll = models.Poll.get_by_name(pollname)
        if poll.open():
            choice = poll.get_choice_by_name(choice)
            if choice:
                choice.decrement()
        return template.render(path, {'callback':callback})

class ResultsRequest(webapp.RequestHandler):
    @helpers.write_response
    def get(self, *args):
        logging.info("Results request with args: "+str(args))
        pollname = args[0]
        format = args[1]
        path = os.path.join(os.path.dirname(__file__), "templates", format+".html")
        poll = models.Poll.get_by_name(pollname)
        if poll and poll.open():
            self.response.headers['Cache-Control'] = 'public, max-age=15'
        else:
            self.response.headers['Cache-Control'] = 'public, max-age=%d' % (24*HOUR)
        return template.render(path, {'poll': poll})

class ListOpenRequest(webapp.RequestHandler):
    @helpers.write_response
    def get(self, *args):
         open_polls = models.Poll.get_all_open()
         path = os.path.join(os.path.dirname(__file__), "templates", "list.html")
         return template.render(path, {'open_polls': open_polls})

class PersistVotesRequest(webapp.RequestHandler):
    @helpers.write_response
    def get(self):
        open_polls = models.Poll.get_all_open()
        for poll in open_polls:
            poll.persist_votes()
        return [poll.name for poll in open_polls]


def main():
    application = webapp.WSGIApplication([
        ('/poll/([\w-]+)/display', MainRequest),
        ('/poll/([\w-]+)/debug', DebugRequest),
        # Results, in a format, like /results/json or /results/jsonp...
        ('/poll/([\w-]+)/results/(\w+)', ResultsRequest),
        # Post a value to counter
        ('/poll/([\w-]+)/([\w-]+)/incr', RegisterIncrRequest),
        ('/poll/([\w-]+)/([\w-]+)/decr', RegisterDecrRequest),

        ('/polls/persist', PersistVotesRequest),

        ('/all-open', ListOpenRequest),
        
    ], debug=True)
    run_wsgi_app(application)

if __name__ == '__main__':
  main()


