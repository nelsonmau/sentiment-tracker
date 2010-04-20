Poll-chart
==================

By Michael Brunton-Spall

Quick Overview
--------------

This app takes posts on a webpage, increments counters and produces a graph of the results.

Urls
----

Install / Run Locally Instructions
----------------------------------

Download python google-appengine libraries
dev_appserver.py runserver <directory>
where <directory> is the directory the code is in (. for current directory)
hit http://localhost:8000/graph.html for graph
hit http://localhost:8000/vote/1 to vote for item 1
hit http://localhost:8000/admin/ to setup the votable items
