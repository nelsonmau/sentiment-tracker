from google.appengine.ext import webapp
from google.appengine.ext.webapp.util import run_wsgi_app
from google.appengine.ext.webapp import template

import helpers
import urllib2
import urllib
import logging
import os

import models


try:
    from django.utils import simplejson
except ImportError:
    try:
        from django.utils import simplejson
    except ImportError:
        import json as simplejson
        
import datetime
from dateutil.tz import *
from dateutil.parser import *

class CreatePoll(webapp.RequestHandler):
    @helpers.write_response
    def get(self, *args):
        template_values = {
            "form": models.PollForm()
        }
        path = os.path.join(os.path.dirname(__file__), "admintemplates", "poll_create.html")
        return template.render(path, template_values)

    @helpers.write_response        
    def post(self, *args):
        form = models.PollForm(data=self.request.POST)
        if form.is_valid():
            poll = form.save(commit=False)
            logging.info(poll.start_time)
            poll.start_time = poll.start_time.replace(tzinfo=gettz('Europe/London'))
            poll.save()
            poll.create_choice('lab', 'LAB', [204, 0, 0])
            poll.create_choice('con', 'CON', [4, 133, 190])
            poll.create_choice('libdem', 'LD', [255, 179, 22])
            logging.info(poll.start_time)
            self.redirect("/admin/poll/list")
        else:
            template_values = {
                "form": form,
            }
            path = os.path.join(os.path.dirname(__file__), "admintemplates", "poll_create.html")
            return template.render(path, template_values)

class EditPoll(webapp.RequestHandler):
    @helpers.write_response
    def get(self, *args):
        logging.info("Getting pollname from %s" % (args))
        pollname = args[0]
        logging.info("Editing poll: "+pollname)
        poll = models.Poll.get_by_name(pollname)
        poll.start_time = models.get_time_as_local(poll.start_time)        
        logging.info("Got poll from datastore: "+str(poll))
        template_values = {
            "form": models.PollForm(instance=poll)
        }
        path = os.path.join(os.path.dirname(__file__), "admintemplates", "poll_create.html")
        return template.render(path, template_values)

    @helpers.write_response
    def post(self, *args):
        pollname = args[0]
        logging.info("Editing poll: "+pollname)
        poll = models.Poll.get_by_name(pollname)
        logging.info("Got poll from datastore: "+str(poll))
        form = models.PollForm(data=self.request.POST, instance=poll)
        if form.is_valid():
            lst = form.save()
            lst.start_time = lst.start_time.replace(tzinfo=gettz('Europe/London'))
            lst.save()
            self.redirect("/admin/poll/list")
        else:
            template_values = {
                "form": form,
            }
            path = os.path.join(os.path.dirname(__file__), "admintemplates", "poll_create.html")
            return template.render(path, template_values)

class DeletePoll(webapp.RequestHandler):

    @helpers.write_response
    def post(self, *args):
        pollname = args[0]
        logging.info("Deleting poll: "+pollname)
        poll = models.Poll.get_by_name(pollname)
        for choice in poll.choice_set:
            for snapshot in choice.countsnapshot_set:
                snapshot.delete_counters()
                snapshot.delete()
            choice.delete()
        poll.delete()
        self.redirect("/admin/poll/list")

class ListPolls(webapp.RequestHandler):
    @helpers.write_response
    def get(self, *args):
        template_values = {
            "polls": models.Poll.all().fetch(50)
        }
        path = os.path.join(os.path.dirname(__file__), "admintemplates", "poll_list.html")
        return template.render(path, template_values)

class WriteCache(webapp.RequestHandler):
    @helpers.write_response
    def get(self, *args):
        poll = models.Poll.get_by_name((args[0]))
        for choice in poll.choice_set:
            choice.write_counts()
        return "Done"

def main():
    application = webapp.WSGIApplication([
    ('/admin/poll/create', CreatePoll),
    ('/admin/poll/list', ListPolls),
    ('/admin/poll/([\w-]+)/edit', EditPoll),
    ('/admin/poll/([\w-]+)/delete', DeletePoll),
    ('/admin/poll/([\w-]+)/write_cache', WriteCache)
    ], debug=True)
    run_wsgi_app(application)


if __name__ == '__main__':
  main()

