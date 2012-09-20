# Poll-chart

This app takes posts on a webpage, increments counters and produces a graph of the results.

## Authors

Michael Brunton-Spall
Philip Wills
Grant Klopper


## Get it running

You need appengine installed and on the path.

```
dev_appserver.py runserver .
```

in the current directory should get a local version working

See admin at: http://localhost:8080/admin/poll/list

You can follow instructions from there

## Releaseing

Edit the app.yaml to increment the app version to the new release number

run ```appcfg.py update .```, watch the pretty lights and see it update.

If you changed the release number, you'll need to go to [https://appengine.google.com/deployment?&app_id=e~sentiment-tracker][AppEngine] to set the default version.  Please delete old versions when you are happy.