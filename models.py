from google.appengine.api import memcache
from google.appengine.ext import db
from google.appengine.ext.webapp import template
from google.appengine.ext.db import djangoforms

import random
import datetime
import time
import logging

from dateutil.tz import *
import helpers
import politicalparties

TZ_EUROPE_LONDON = gettz('Europe/London')
TZ_UTC = gettz('UTC')

TIME_SLICE = 60
def get_time_as_local(t):
    utc_time = t.replace(tzinfo=TZ_UTC)
    london_time = utc_time.astimezone(TZ_EUROPE_LONDON)
#    logging.info("Convert UTC: %s to London %s" % (utc_time, london_time))
    return london_time

def get_time_now():    
    return get_time_as_local(datetime.datetime.now())

def time_in_secs(t):
    return time.mktime(t.timetuple())

class Poll(db.Model):
    name = db.StringProperty(required=True)
    start_time = db.DateTimeProperty(required=True)
    duration = db.IntegerProperty(required=True)
    political_party = db.StringProperty(required=True, choices=set([politicalparties.CONSERVATIVE, politicalparties.LIBERAL_DEMOCRATS, politicalparties.LABOUR]), default=politicalparties.LIBERAL_DEMOCRATS)

    @classmethod
    def get_by_name(cls, name):
        return cls.all().filter('name =',name).get()

    @classmethod
    def get_all_open(cls):
        return [poll for poll in cls.all() if poll.open()]

    def start_time_as_epoch_secs(self):
        epoch_secs = time.mktime(get_time_as_local(self.start_time).timetuple())
        return epoch_secs
        
    def get_choice_by_name(self, name):
        rname = '%s,%s' % (self.name,name)
        logging.info("Looking for choice with name '%s'" % (rname))
        return self.choice_set.filter('name =', rname).get()

    def create_choice(self, name, fullname, colour):
        rname = '%s,%s' % (self.name,name)
        choice = Choice(poll=self, name=rname, fullname=fullname, colour=colour)
        choice.put()
        return choice

    def offset(self):
        offset = (time.mktime(get_time_now().timetuple()) - self.start_time_as_epoch_secs())
        return int(offset // TIME_SLICE)

    def open(self):
        if self.offset() < self.duration:
            return True
        return False

    def data_path(self):
        return 'poll/%s/results/jsonp' % self.name

    def persist_votes(self):
        for choice in self.choice_set:
            choice.write_counts()

        
class PollForm(djangoforms.ModelForm):
      class Meta:
        model = Poll
    
class Choice(db.Model):
    poll = db.ReferenceProperty(Poll, required=True)
    name = db.StringProperty(required=True)
    fullname = db.StringProperty(required=True)
    colour = db.ListProperty(int, required=True)

    def calc_offset(self):
        return self.poll.offset()
        
    def displayname(self):
        return self.name.split(',')[1]

    def get_counts_from_memcache(self):
        max_time = min(self.poll.duration,self.calc_offset())
        caches = []
        for offset in range(max_time+1):
            caches.append("counts,%s,%d" % (self.name, offset))

        return memcache.get_multi(caches)

    def write_counts(self):
       for [actual_time, count] in self.get_counts():
            offset = int(((actual_time/1000) - self.poll.start_time_as_epoch_secs()) / TIME_SLICE)
            cachename = "counts,%s,%d" % (self.name, offset)
            logging.info("Creating countersnapshot for %d, value %d" % (self.calc_offset(), count))
            record = self.countsnapshot_set.filter('time_offset =',offset).get()
            if not record:
                record = CountSnapshot(name="%s,%s" % (self.poll.name,self.name), choice=self, time_offset=offset, parent=self)
                record.put()
            counter = record.get_or_create_random_sharded_counter()
            counter.count = count
            counter.put()

    def get_counts(self):
        max_time = min(self.poll.duration, (self.calc_offset()))
        logging.info("Get counts up to %d" % (max_time))
        cachetime = 0
        l = []

        cache_results = self.get_counts_from_memcache()
        for offset in range(max_time+1):
            cachename = "counts,%s,%d" % (self.name, offset)
            actual_time = int(self.poll.start_time_as_epoch_secs()+(offset*TIME_SLICE))*1000
            if cachename not in cache_results:
                count = 0
                count_snapshot = self.countsnapshot_set.filter('time_offset =',offset).get()
                if count_snapshot:
                    logging.info("Snapshot exists - getting count")
                    count = int(count_snapshot.get_count())
                logging.info("Snapshot is %d - Caching %s for %d" % (count, cachename, cachetime))
                cached = memcache.set(cachename, 1000000+count, cachetime)
            else:
                count = int(cache_results[cachename])-1000000
                logging.info("Cache hit for %s = %d" % (cachename, count))
            l.append([actual_time, count])
        return l

    def increment(self):
        offset = self.calc_offset()
        cachename = "counts,%s,%d" % (self.name, offset)
        val = memcache.incr(cachename, initial_value=1000000)
        logging.info("Current value for %s = %d" % (cachename, val))

    def decrement(self):    
        offset = self.calc_offset()
        cachename = "counts,%s,%d" % (self.name, offset)
        val = memcache.decr(cachename, initial_value=1000000)
        logging.info("Current value for %s = %d" % (cachename, val))
        

class CountSnapshot(db.Model):
    """Tracks the number of shards for each named counter."""
    name = db.StringProperty(required=True)
    num_shards = db.IntegerProperty(required=True, default=1)
    choice = db.ReferenceProperty(Choice, required=True)
    time_offset = db.IntegerProperty(required=True)
    
    def cachename(self):
        return "%s%d" % (self.name,self.time_offset)
        
    def keyname(self, index):
        return "%s,%d" % (self.cachename(),index)
    
    def get_count(self):
        total = 0
        for counter in ShardedCounter.all().filter('shared_name =',self.cachename()).fetch(self.num_shards):
            total += counter.count
        return total
        
    def delete_counters(self):
        for counter in ShardedCounter.all().filter('shared_name =',self.cachename()).fetch(self.num_shards):
            db.delete(counter)

    def get_or_create_random_sharded_counter(self):
        index = random.randint(0, self.num_shards - 1)
        counter = ShardedCounter.get_by_key_name(self.keyname(index))
        if counter is None:
            logging.info("Creating Sharded Counter %s" % (self.keyname(index)))
            counter = ShardedCounter(key_name=self.keyname(index), shared_name=self.cachename(), vote_config=self)
        return counter
        
    def increment(self):    
        logging.info("Incrementing %s" % (self.name))
        def txn():
            counter = self.get_or_create_random_sharded_counter()
            counter.count += 1
            counter.put()
        db.run_in_transaction(txn)

    def decrement(self):    
        logging.info("Decrementing %s" % (self.name))
        def txn():
            counter = self.get_or_create_random_sharded_counter()
            counter.count -= 1
            counter.put()
        db.run_in_transaction(txn)

class ShardedCounter(db.Model):
    """Shards for each named counter"""
    shared_name = db.StringProperty(required=True)
    count = db.IntegerProperty(required=True, default=0)
