import random
import time
import urllib
import sys

while True:
    url = sys.argv[1]
    print "hitting %s" % (url)
    print urllib.urlopen(url).read()
    time.sleep(random.random())
