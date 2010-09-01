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



Create Poll: 		http://localhost:8080/admin/poll/create

The date/time format is: 2010-08-27 14:35:00

Viewing your poll: 	http://localhost:8080/poll/{poll-name}/debug

The debug allows the app to be executed in a standalone mode outside of r2.

List your polls:	http://localhost:8080/admin/poll/list
