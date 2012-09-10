import newt,sys



location=sys.argv[1]
distance=sys.argv[2]
try:
  num=int(sys.argv[3])
except:
  num=300

try:
  limit=int(sys.argv[4])
except:
  limit=1
  
network=True
  
api=newt.getTwitterAPI()

tweeters={}
tags={}


print 'Looking for twitterers and tags within',distance,'km of',location

tweeters,tags=newt.twSearchNear(tweeters,tags,num, location, term='', dist=float(distance))

for t in sorted(tags, key=tags.get, reverse=True):
  print t,tags[t]

tw=[]
tws={}
for i in tweeters:
  tws[i]=tweeters[i]['count']
  if tws[i]>=limit:
    tw.append(i)


tw=newt.getTwitterUsersDetailsByScreenNames(api,tw)

locfname=location.replace(',','_')

if network:
	newt.gephiOutputFile(api,'local-'+locfname, tw)
else:
	newt.outputHomepageURLs(api,'local-'+locfname,tw,locfname)
	newt.opmlFromCSV('local-'+locfname)
