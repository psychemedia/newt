import newt,sys,csv

tag=sys.argv[1]
try:
  num=int(sys.argv[2])
except:
  num=300

network=True
followerView=False

opml=False

api=newt.getTwitterAPI()

tweeters={}
tags={}


print 'Looking for twitterers and tags in context of hashtag (excluding oldstyle RT messages)',tag

tweeters,tags,tweets=newt.twSearchHashtag(tweeters,tags,num, tag,exclRT=True)

fo=newt.openTimestampedFile("hashtag-"+tag,'tweets.txt')
writer=csv.writer(fo)
for tweet in tweets:
	writer.writerow([tweet['from_user_id'],tweet['from_user'],tweet['text'].encode('ascii','ignore'),tweet['to_user_id'],tweet['created_at']])
fo.close()

newt.report_hashtagsearch('hashtag-'+tag,tweeters,tags)

for t in sorted(tags, key=tags.get, reverse=True):
  print t,tags[t]

limit=1
tw=[]
tws={}
for i in tweeters:
  tws[i]=tweeters[i]['count']
  if tws[i]>=limit:
    tw.append(i)


tw=newt.getTwitterUsersDetailsByScreenNames(api,tw)

#newt.outputHomepageURLs(api,'hashtag-'+tag,tw,tag)
#newt.opmlFromCSV('hashtag-'+tag)

if network:
	newt.gephiOutputFile(api,'hashtag-'+tag, tw)
	newt.gephiOutputFile(api,'hashtag-'+tag, tw,'outerfriends')
	newt.gephiOutputFile(api,'hashtag-'+tag, tw,'extrafriends')
	newt.gephiOutputFile(api,'hashtag-'+tag, tw,'outerfollowers')

if followerView:
	typ='followers'
	sampleSize=195
	filterN=3
	twc={}
	twDetails={}

	for tweep in tw:
		user=tw[tweep].screen_name
		print "Getting followers of ",user
		if typ=="followers":
			tmp=newt.getTwitterFollowersDetailsByIDs(api,user,sampleSize)
		else:
			tmp=newt.getTwitterFriendsDetailsByIDs(api,user,sampleSize)
		print "Grabbed ",str(len(tmp)),typ,' for ',user
		#tw.extend(tmp)
		for t in tmp:
			if t in twc:
				twc[t]=twc[t]+1
			else:
				twc[t]=1
				twDetails[t]=tmp[t]
	tw={}

	for t in twc:
		if twc[t]>=filterN: tw[t]=twDetails[t]

	print len(tw),tw


	user=typ+'_'+str(filterN)+'ormore_sample'+str(sampleSize)
	f=newt.openTimestampedFile('hashtag-'+tag+'/'+user+'/','tweeps.txt')
	for tweep in tw:
		f.write(str(tweep)+'\n')
	f.close()

	typ2='friends'
	#newt.gephiOutputFile(api,user+'/'+typ, tw,'outerfriends')
	newt.gephiOutputFile(api,'hashtag-'+tag+'/'+user+'/'+typ2, tw)
	extra=1
	if extra!=-1:
		newt.gephiOutputFile(api,'hashtag-'+tag+'/'+user+'/'+typ2, tw,'extrafriends')
		newt.gephiOutputFile(api,'hashtag-'+tag+'/'+user+'/'+typ2, tw,'outerfriends')
		#newt.gephiOutputFile(api,user+'/'+typ, tw,'outerfollowers')




#-------
def opmlOut(tw, tag):
  fo=newt.openTimestampedFile("opml",'hashtag-'+tag+'.xml',False)
  newt.writeOPMLHeadopenBody(fo)
  newt.openOPMLoutline(fo,tag)
  for i in tw:
    newt.handleOPMLitem(fo,tw[i].url)
  newt.closeOPMLoutline(fo)
  newt.closeOPMLbody(fo)
  fo.close()


if opml:
  opmlOut(tw,tag)
  