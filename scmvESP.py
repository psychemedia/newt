import sys, os, newt, argparse, datetime, csv, random
import networkx as nx
import newtx as nwx

import urllib
#to do
#when doing eg hashtag search, need to be able to use original tagger list with differet filter arg
# ie print a 'try this' command to cope with different filter val. Requires new code block?
# triangulate: given list of N users, find folk who follow M of them

def checkDir(dirpath):
  if not os.path.exists(dirpath):
    os.makedirs(dirpath)

def report(m):
  newt.report(m,True)

api=newt.getTwitterAPI()

#----------------------------------------------------------------
#user settings
#Examples:
## python scmvESP.py -filterfile reports/scmvESP/scmvESP_2011-12-17-20-38-50 -indegree 5 -outdegree 30 -outdegreemax 500
#python scmvESP.py -searchterm allotment veg OR fruit OR garden -tagsample 500 -outdegree 50  -indegree 20 -projection forward -typ friends -tagfilter 1

## python scmvESP.py -user tetley_teafolk -sample 5000 -mindegree 500
## python scmvESP.py -user tetley_teafolk -sample 200 -indegree 20 -outdegree 30
## python scmvESP.py -hashtag philately -tagsample 500 -tagfilter 5 -mindegree 20
## python scmvESP.py -searchterm philately -tagsample 500 -tagfilter 5 -mindegree 20
## python scmvESP.py -hashtag sherlock -tagsample 1500  -mindegree 75 -projection forward
## python scmvESP.py -searchterm http://www.johnwatsonblog.co.uk/  -tagsample 500 -tagfilter 1 -mindegree 20 -projection forward 
# python scmvESP.py -fromfile ../users.txt  -indegree 15 -outdegree 1 -projection forward 
# python scmvESP.py -fromfile ../users.txt  -indegree 15 -outdegree 1 -projection forward -filter 10
# python scmvESP.py -list emercoleman/cstwitter -indegree 15 -outdegree 1 -projection forward
#python scmvESP.py -users actiononhearing deafaction deafnessuk hearinglink -filter 2  -sample 500  -typ followers -outdegree 10 -indegree 10 
#python scmvESP.py -searchterm anti bullying  -tagsample 500 -tagfilter 1 -outdegree 20 -indegree 20 -projection forward -fname anti_bullying -location milton keynes -dist 500 -fname geoMK500_anti_bulliying

parser = argparse.ArgumentParser(description='Generate social positioning map')

parser.add_argument('-fname',default='scmvESP',help='Custom folder name')


group = parser.add_mutually_exclusive_group()
group.add_argument('-user',help='Name of a user (without the @) for whom you want to generate their ESP.')
group.add_argument('-users',nargs='*', help="A space separated list of usernames (without the @) for whom you want to generate their common ESP.")
group.add_argument('-fromfile',help='Name of a simple text file from which to enter a list of usernames (without the @) for whom you want to generate their common ESP.')
group.add_argument('-filterfile',help='Run a network filter on a project file.')
group.add_argument('-list',help='Grab users from a list. Provide source as: username/listname #IN TESTING')
#NOTE - the newt hashtag code allows us to exclude RTs; at the moment, the default to not exclude hashtaggers is used;
## TODO add in an argument to allow this to be controlled
group.add_argument('-hashtag',help='Hashtag for which you want to identify recent users and then generate their common ESP.')
group.add_argument('-searchterm',nargs='*',help='Searchterm for which you want to identify recent users and then generate their common ESP.')

parser.add_argument('-location',nargs='*',help="Search location")
parser.add_argument('-dist',type=float,help='Location search distance')

parser.add_argument('-typ',default='followers',help='Are we going to generate ESP from friends or followers?')
parser.add_argument('-typ2',default='friends',help='This relates to the second, projection step of the ESP process, and describes whether we project friends or followers of the folk identified by typ')

parser.add_argument('-sample',default=197,type=int,metavar='N',help='Sample the friends/followers (user, users); use 0 if you want all (users/users).')
parser.add_argument('-sample2',default=-1,type=int,metavar='N',help='Sample the friends/followers (user, users) for forward projection')

parser.add_argument('-tagsample',default=500,type=int,metavar='N',help='For hashtag/searchterm sample, number of recently hashtagged/search term including tweets to search for (hashtag,searchterm)')
parser.add_argument('-tagfilter',default=2,type=int,metavar='N',help='For hashtag or searchterm sample, number times a person needs to use tag/searchterm to count')

parser.add_argument('-filter',default=0,type=int,metavar='N',help='For use with users argument. Specify how many users the fr/fo must follow to be included as positioning sources.')

parser.add_argument('-projection',default='default',help='If you just want to find the innerfriends of friends/followers, and not the projection, set this false.')


#At the moment, mindegree dominates indegree and outdegree. Need to set exclusion rules accordingly
parser.add_argument('-mindegree',type=int,metavar='N',help='If you want to generate a labelled projection graph, set the minimum degree that nodes in the projection graph must have.')
#parser.add_argument('-maxdegree',type=int,metavar='N',help='If you want to generate a labelled projection graph, set the maximum degree that nodes in the projection graph must have.')
parser.add_argument('-indegree',type=int,metavar='N',help='If you want to generate a labelled projection graph, set the minimum in_degree that nodes in the ESP set and not in the projection set must have.')
parser.add_argument('-indegreemax',type=int,metavar='N',help='If you want to generate a labelled projection graph, set the maximum in_degree that nodes in the ESP set and not in the projection set must have.')
parser.add_argument('-outdegree',type=int,metavar='N',help='If you want to generate a labelled projection graph, set the minimum out_degree that nodes in the projection set must have.')
parser.add_argument('-outdegreemax',type=int,metavar='N',help='If you want to generate a labelled projection graph, set the maxiumum out_degree that nodes in the projection set must have.')


args=parser.parse_args()

#----------------------------------------------------------------

def logger(fname,args):
	flog=open("reports/scmvESP/logger.csv","a")
	logger=csv.writer(flog)
	logger.writerow([fname,repr(args)])
	flog.close()

def ascii(s): return "".join(i for i in s if ord(i)<128)

def getTimeStampedProjDirName(path,stub):
	now = datetime.datetime.now()
	ts = now.strftime("_%Y-%m-%d-%H-%M-%S")
	return path+'/'+stub+ts

def nowTime():
	now = datetime.datetime.now()
	ts = now.strftime("_%Y-%m-%d-%H-%M-%S")
	return ts
	
checkDir('reports')
checkDir('reports/scmvESP')

fpf=''

def getSearchtermUsers(searchterm,num,limit,projname,location='',dist=''):
	if location!='': term='locterm'
	else: term='term'
	return getGenericSearchUsers(searchterm,num,limit,projname,term,location,dist)
	
def getHashtagUsers(tag,num,limit,projname):
	return getGenericSearchUsers(tag,num,limit,projname,"tag")

def getGenericSearchUsers(tag,num,limit,projname,styp="tag",location='',dist=''):
	tweeters={}
	tags={}
	if styp=='tag':
		print 'Looking for twitterers and tags in context of hashtag',tag
		tweeters,tags,tweets=newt.twSearchHashtag(tweeters,tags,num, tag,exclRT=False)
	elif styp=='locterm':
		tweeters,tags,tweets=newt.twSearchNear(tweeters,tags,num, location, tag, dist=float(dist),exclRT=False)
	else: #styp=='term'
		print 'Looking for twitterers and tags in context of searchterm',tag
		tweeters,tags,tweets=newt.twSearchTerm(tweeters,tags,num, tag,exclRT=False)
		#newt.report_hashtagsearch('searchterm-'+qtag,tweeters,tags)

	fo=open(projname+'/tweets.txt','wb+')
	writer=csv.writer(fo)
	for tweet in tweets:
		writer.writerow([tweet['from_user_id'],tweet['from_user'],tweet['text'].encode('ascii','ignore'),tweet['to_user_id'],tweet['created_at']])
	fo.close()

	fo=open(projname+'/tweeps.txt','wb+')
	writer=csv.writer(fo)
	for tweeter in tweeters:
		writer.writerow([tweeter])
	fo.close()

	fo=open(projname+'/cotags.txt','wb+')
	writer=csv.writer(fo)
	for cotag in tags:
		writer.writerow([cotag])
	fo.close()

	for t in sorted(tags, key=tags.get, reverse=True):
		print t,tags[t]

	alltweeps=[]
	tw=[]
	tws={}
	for i in tweeters:
		alltweeps.append(i)
		tws[i]=tweeters[i]['count']
		if tws[i]>=limit:
			tw.append(i)
	print alltweeps
	#this is a fudge; return alltweeps as well tw? Also generalis w/ getSourceList?
	return tw
	

def getSourceList(users,typ,sampleSize,filterN):
	tw={}
	twc={}
	twDetails={}
	print users
	#we can look up a max of 100 users...
	#TO DO / HACK just sample 100 for now, if required...?
	if len(users)>100:
  		users=random.sample(users, 100)
  		print 'HACK FUDGE, only using 100 users:',users
	twd=api.lookup_users(screen_names=users)
	for u in twd:
		if  type(u) is newt.tweepy.models.User:
			twc[u.screen_name]=filterN
			twDetails[u.screen_name]=u
	if sampleSize==0: sampleSize='all'
	for user in users:
		print "Getting ",typ," of ",user
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
	#deDupeList=list(set(origList))
	#deDupeList=filter(lambda e: e not in origList,origList)

	for t in twc:
		if twc[t]>=filterN: tw[t]=twDetails[t]

	return tw


def getFriendsProjection(tw={},maxf=5000):
	newt.gephiOutputFileByName(api,projname+'/'+args.typ+'_innerfriends.gdf', tw,maxf=maxf)
	newt.gephiOutputFileByName(api,projname+'/'+args.typ+'_extrafriends.gdf', tw,'extrafriends',maxf=maxf)
	newt.gephiOutputFileByName(api,projname+'/'+args.typ+'_outerfriends.gdf', tw,'outerfriends',maxf=maxf)

def getFollowersProjection(tw={},maxf=5000):
	newt.gephiOutputFileByName(api,projname+'/'+args.typ+'_innerfollowers.gdf', tw,'followers',maxf=maxf)
	newt.gephiOutputFileByName(api,projname+'/'+args.typ+'_extrafollowers.gdf', tw,'extrafollowers',maxf=maxf)
	newt.gephiOutputFileByName(api,projname+'/'+args.typ+'_outerfollowers.gdf', tw,'outerfollowers',maxf=maxf)

def getFriendsView(tw={},maxf=5000):
	newt.gephiOutputFileByName(api,projname+'/innerfriends.gdf', tw,maxf=maxf)
	newt.gephiOutputFileByName(api,projname+'/extrafriends.gdf', tw,'extrafriends',maxf=maxf)
	newt.gephiOutputFileByName(api,projname+'/outerfriends.gdf', tw,'outerfriends',maxf=maxf)

def getFollowersView(tw={},maxf=5000):
	newt.gephiOutputFileByName(api,projname+'/innerfollowers.gdf', tw,'followers',maxf=maxf)
	newt.gephiOutputFileByName(api,projname+'/extrafollowers.gdf', tw,'extrafollowers',maxf=maxf)
	newt.gephiOutputFileByName(api,projname+'/outerfollowers.gdf', tw,'outerfollowers',maxf=maxf)

	
def labelGraph(LG,idlist):
	idlabels=newt.twDetailsFromIds(api,idlist)
	#There is going to be a clash on this filename:-(
	f=open(projname+'/idnames.txt','wb+')
	cf=csv.writer(f)
	cf.writerow(['id','username','desc'])
	for id in idlabels:
		if str(id) in LG.node:
			LG.node[str(id)]['label']=idlabels[id].screen_name
			LG.node[str(id)]['fo_count']=idlabels[id].followers_count
			LG.node[str(id)]['fr_count']=idlabels[id].friends_count
			LG.node[str(id)]['updates']=idlabels[id].statuses_count
			desc=idlabels[id].description
			if desc !=None:
				desc=desc.encode('ascii','ignore')
			#LG.node[str(id)]['descr']=desc
			#print LG.node[str(id)]['desc']
			cf.writerow([id,idlabels[id].screen_name,desc])
			LG.node[str(id)]['indegree']=LG.in_degree(str(id))
			if idlabels[id].followers_count>0:
				LG.node[str(id)]['fo_prop']=1.0*LG.in_degree(str(id))/idlabels[id].followers_count
			else:
				LG.node[str(id)]['fo_prop']=0.0
			#LG.node[str(id)]['since']=idlabels[id].created_at
			'''
			LG.node[str(id)]['location']=idlabels[id].location
			LG.node[str(id)]['desc']=idlabels[id].description
			'''
			LG.node[str(id)]['desc']=ascii(idlabels[id].description)
			#print LG.node[str(id)]
	f.close()
	return LG

def filterNet(DG,mindegree,indegree,outdegree,outdegreemax,typ,addUserFriendships,user,indegreemax):
	print 'In filterNet'
	#need to tweak this to allow filtering by in and out degree?
	if addUserFriendships==1:
		DG=addFocus(DG,user,typ)
	#handle min,in,out degree
	filter=[]
	#filter=[n for n in DG if DG.degree(n)>=mindegree]
	for n in DG:
		if outdegreemax==None or DG.out_degree(n)<=outdegreemax:
			if mindegree!=None:
				if DG.degree(n)>=mindegree:
					filter.append(n)
			else:
				if indegree!=None:
					if DG.in_degree(n)>=indegree:
						filter.append(n)
				if outdegree!=None:
					if DG.out_degree(n)>=outdegree:
						filter.append(n)
	#the filter represents the intersect of the *degreesets
	#indegree and outdegree values are ignored if mindegree is set
	filter=set(filter)
	H=DG.subgraph(filter)
	#Superstitiously, perhaps, make sure we only grab nodes that project edges...
	filter= [n for n in H if H.degree(n)>0]
	L=H.subgraph(filter)
	print "Filter set:",filter
	print L.order(),L.size()
	L=labelGraph(L,filter)
	
	if mindegree==None: tm='X'
	else: tm=str(mindegree)
	if indegree==None: ti='X'
	else: ti=str(indegree)
	if outdegree==None: to='X'
	else: to=str(outdegree)
	if outdegreemax==None: tom='X'
	else: tom=str(outdegreemax)
	st='/'.join([projname,typ+'degree_'+tm+'_'+ti+'_'+to+'_'+tom+"_esp"])
	nx.write_graphml(L, st+".graphml")
	nx.write_edgelist(L, st+".txt",data=False)
	fpf=st+'.graphml'
	return fpf
		
	'''
	#delimiter=''

	#indegree=sorted(nx.indegree(DG).values(),reverse=True)
	indegree=H.in_degree()
	outdegree=H.out_degree()

	inout = [indegree, outdegree]
	inoutpair = {}
	for k in indegree.iterkeys():
		inoutpair[k] = tuple(inoutpair[k] for inoutpair in inout)
	fig = plt.figure()
	ax = fig.add_subplot(111)
	#ax.plot(indegree,outdegree, 'o')
	#ax.set_title('Indegree vs outdegree')
	degree_sequence=sorted(indegree.values(),reverse=True)
	plt.loglog(degree_sequence)
	plt.savefig( '/'.join([path,agent,typ,tt+"degree"+str(mindegree)+"outdegree_histogram.png"]))
	#plt.show()
	'''

def addFocus(DG,user,typ='all'):
	userData=api.get_user(user)
	userID=userData.id
	if userID not in DG.nodes():
		if typ=='all' or typ=='fr':
			print 'adding in user friendships...'
			userFriends=api.friends_ids(user)
			print user,'as',userID
			frNet=nwx.createTwitterFnet(api,user,typ='friends')
			DG=nwx.mergeNets(DG,frNet)
		if typ=='all' or typ=='fo':
			print 'adding in user followerships...'
			userFollowers=api.followers_ids(user)
			print user,'as',userID
			foNet=nwx.createTwitterFnet(api,user,typ='followers')
			DG=nwx.mergeNets(DG,foNet)
	return DG

def filterProjFile(projname,args):
	#As we know the filenames, we can now easily run gdfFilter type analyses
	#Use the file route because it provides an audit trail...
	print 'In filterProjFile'
	typ=args.typ+'_outer'+args.typ2
	fn='/'.join([projname,typ+'.gdf'])
	print 'Loading file...',fn
	DG=nwx.directedNetworkFromGDF(fn)
	print DG.order(),DG.size()

	addUserFriendships=0
	user=''
	#use an incluser flag to include fr/fo relations of user(s)?
	if args.mindegree!=None or args.indegree!=None or args.outdegree!=None or args.outdegreemax!=None or  args.indegreemax!=None:
		fpf=filterNet(DG,args.mindegree,args.indegree,args.outdegree,args.outdegreemax,typ,addUserFriendships,user,args.outdegreemax)
	return fpf

def filterProjFile2(projname,ftyp='outerfriends'):
	typ=ftyp.replace('outer','')
	#As we know the filenames, we can now easily run gdfFilter type analyses
	#Use the file route because it provides an audit trail...
	#typ=args.typ+'_outer'+args.typ2
	fn='/'.join([projname,ftyp+'.gdf'])
	print 'Loading file...',fn
	DG=nwx.directedNetworkFromGDF(fn)
	print DG.order(),DG.size()

	addUserFriendships=0
	user=''
	#use an incluser flag to include fr/fo relations of user(s)?
	if args.mindegree!=None or args.indegree!=None or args.outdegree!=None or args.outdegreemax!=None or  args.indegreemax!=None:
		fpf=filterNet(DG,args.mindegree,args.indegree,args.outdegree,args.outdegreemax,typ,addUserFriendships,user,args.outdegreemax)
	return fpf

def getUsersFromList(userList):
	userList_l =userList.split('/')
	user=userList_l[0]
	list=userList_l[1]
	tmp=newt.listDetailsByScreenName({},api.list_members,user,list)
	u=[]
	for i in tmp:
		u.append(tmp[i].screen_name)
	return u
  

#does py have a switch statement?

if args.filterfile==None:
	if args.fname=='scmvESP':
		projname=getTimeStampedProjDirName('reports/scmvESP','scmvESP')
	else: projname= 'reports/scmvESP/'+args.fname+'/'+nowTime()
	checkDir(projname)

	f=open(projname+'/settings.txt','wb+')
	f.write(repr(args)+'\n')
	f.write("To run another filter over this data, use:\n")
	f.write("python scmvESP.py -filterfile "+projname+' -typ '+args.typ+'\n')
	f.write("with -indegree, -mindegree, -outdegree args as required\n")
	f.close()

	
users=[]
if args.user!=None: users=[args.user]
elif args.users!=None: users=args.users
elif args.fromfile!=None:
	fname=args.fromfile
	print 'Opening file...',fname
	f=open(fname,'r+')
	for i in f:
		i=i.replace('http://twitter.com/','')
		i=i.replace('@','')
		print 'Grabbed user',i
		users.append(i)
	f.close()
elif args.hashtag!=None:
	users=getHashtagUsers(args.hashtag,args.tagsample,args.tagfilter,projname)
	print users
	if args.projection=='default':
		args.projection=='false'
elif args.searchterm!=None:
	searchterm=' '.join(args.searchterm)
	#searchterm=urllib.quote(searchterm)
	loc=''
	dist=50.0
	if args.location!=None:
		loc=' '.join(args.location)
		if args.dist!=None: dist=args.dist
	users=getSearchtermUsers(searchterm,args.tagsample,args.tagfilter,projname,loc,dist)
	print users
	if args.projection=='default':
		args.projection=='false'
elif args.list!=None:
	users=getUsersFromList(args.list)
	if args.projection=='default':
		args.projection=='false'


if users!=[]:
	tw=newt.getTwitterUsersDetailsByScreenNames(api,users)
	newt.gephiOutputFileByName(api,projname+'/users_innerfriends.gdf', tw)


if args.filterfile!=None:
	projname=args.filterfile
logger(projname,args)

print "Projection status is:",args.projection
if args.projection=='forward':
	#The getFriendsProjection doesn't use sample but does max out...
	args.sample=''
	if args.filterfile==None:
		getFriendsView(tw)
	if args.mindegree!=None or args.indegree!=None or args.outdegree!=None or args.outdegreemax!=None:
		fpf=filterProjFile2(projname)
	print "Stopping after forward projection; root call is:"
	print "python scmvESP.py -filterfile "+projname +' -projection '+ args.projection
	print "Also guessing at [TO DO]:"
	print "python scmvGraphCompare.py -compare false -outpath "+projname+" -files "+fpf+" -labels testX"
	exit(-1)
elif args.projection=='backward':
	#The getFriendsProjection doesn't use sample but does max out...
	args.sample=''
	getFollowersView(tw)
	if args.mindegree!=None or args.indegree!=None or args.outdegree!=None or args.outdegreemax!=None:
		filterProjFile2(projname,'outerfollowers')
	print "Stopping after backward projection; root call is:"
	print "python scmvESP.py -filterfile "+projname +' -projection '+ args.projection
	exit(-1)
elif args.projection=='false':
	print "As requested, stopping before projection routines"
	exit(-1)

if args.filterfile==None:

	tw=getSourceList(users,args.typ,args.sample,args.filter)
	
	f=open(projname+'/projectionset.txt','wb+')
	for tweep in tw:
		f.write(str(tweep)+'\n')
	f.close()

	if args.typ2!='followers':
		args.typ2='friends'
		if args.sample2>=0:
			getFriendsProjection(tw,args.sample2)
		else: getFriendsProjection(tw)
	else:
		getFollowersProjection(tw)
	if args.mindegree!=None or args.indegree!=None or args.outdegree!=None or args.outdegreemax!=None:
		fpf=filterProjFile(projname,args)
else:
	if args.mindegree!=None or args.indegree!=None or args.outdegree!=None or args.outdegreemax!=None:
		projname=args.filterfile
		fpf=filterProjFile(projname,args)
	
print "To run another filter over this data, use:"
print "python scmvESP.py -filterfile "+projname+' -typ '+args.typ
print "with -indegree, -mindegree, -outdegree args as required"

print "Also guessing at [TO DO]:"
print "python scmvGraphCompare.py -compare false -outpath "+projname+" -files "+fpf+" -labels testX"


