import webapp2

import helpers
import urllib2
import urllib
import logging
import os

from models import Poll
import models
#import logging
#logging.logMultiprocessing = 0

import politicalparties


import json        
import datetime
from dateutil.tz import *
from dateutil.parser import *
import jinja2


jinj = jinja2.Environment(
    loader=jinja2.FileSystemLoader(os.path.join(os.path.dirname(__file__), 'admintemplates')))


class CreatePoll(webapp2.RequestHandler):
    @helpers.write_response
    def get(self, *args):
        template = jinj.get_template('poll_create.html')
        return template.render({
            'politicalparties': politicalparties.all(),
            'start_time': datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            'edit': False
            })

    def party_to_choice_value(self, party_name):
        party_to_choice = {
            politicalparties.CONSERVATIVE :"con",
            politicalparties.LABOUR :"lab",
            politicalparties.LIBERAL_DEMOCRATS : "libdem"
        }
        return party_to_choice[party_name]

    def party_to_choice_name(self, party_name):
        party_to_choice_name = {
            politicalparties.CONSERVATIVE :"CON",
            politicalparties.LABOUR :"LAB",
            politicalparties.LIBERAL_DEMOCRATS : "LD"
        }
        return party_to_choice_name[party_name]

    def party_to_rgb_color(self, party_name):
        party_to_rgb_color_name = {
            politicalparties.CONSERVATIVE:[4, 133, 190],
            politicalparties.LABOUR: [204, 0, 0],
            politicalparties.LIBERAL_DEMOCRATS:[255, 179, 22]
        }
        return party_to_rgb_color_name[party_name]

    @helpers.write_response
    def post(self, *args):
        logging.info(self.request.arguments())
        name = self.request.get('name')
        start_time = parse(self.request.get('start_time'))
        duration = int(self.request.get('duration'))
        logging.info(name)
        party = politicalparties.all_parties[self.request.get('political_party')]

        poll = Poll(name=name, start_time=start_time, duration=duration)
        logging.info(poll.start_time)
        poll.start_time = poll.start_time.replace(tzinfo=gettz('Europe/London'))
        poll.save()

        poll.create_choice(party['id'], party['short_name'], party['colour'])
        self.redirect("/admin/poll/list")


class EditPoll(webapp2.RequestHandler):
    @helpers.write_response
    def get(self, pollname):
        logging.info("Editing poll: "+pollname)
        poll = Poll.get_by_name(pollname)
        poll.start_time = models.get_time_as_local(poll.start_time)        
        logging.info("Got poll from datastore: %s " % (poll))
        template = jinj.get_template('poll_create.html')

        return template.render({
            'politicalparties': politicalparties.all(),
            'start_time': poll.start_time,
            'name': poll.name,
            'duration': poll.duration,
            'edit': True
            })

    @helpers.write_response
    def post(self, pollname):
        logging.info("Editing poll: "+pollname)
        poll = models.Poll.get_by_name(pollname)
        name = self.request.get('name')
        start_time = parse(self.request.get('start_time')).replace(tzinfo=gettz('Europe/London'))
        duration = int(self.request.get('duration'))
        poll.name = name
        poll.start_time = start_time
        poll.duration = duration
        poll.save()
        self.redirect("/admin/poll/list")


class DeletePoll(webapp2.RequestHandler):
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


class ListPolls(webapp2.RequestHandler):
    @helpers.write_response
    def get(self, *args):
        template_values = {
            "polls": models.Poll.all().fetch(50)
        }
        template = jinj.get_template('poll_list.html')
        return template.render(template_values)


class WriteCache(webapp2.RequestHandler):
    @helpers.write_response
    def get(self, *args):
        poll = models.Poll.get_by_name((args[0]))
        for choice in poll.choice_set:
            choice.write_counts()
        return "Done"

app = webapp2.WSGIApplication([
    ('/admin/create', CreatePoll),
    ('/admin/([\w-]+)', EditPoll),
    ('/admin/([\w-]+)/delete', DeletePoll),
    ('/admin/([\w-]+)/write_cache', WriteCache),
    ('/admin/.*', ListPolls)
    ], debug=True)
