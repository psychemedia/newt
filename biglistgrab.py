import tweepy,sys, os, newt, argparse, datetime, csv, random
import networkx as nx
import newtx as nwx

import urllib, unicodedata

def checkDir(dirpath):
  if not os.path.exists(dirpath):
    os.makedirs(dirpath)
    
parser = argparse.ArgumentParser(description='Data about list members')
group = parser.add_mutually_exclusive_group()
group.add_argument('-list',help='Grab users from a list. Provide source as: username/listname')

parser.add_argument('-sample',default=197,type=int,metavar='N',help='Sample the friends/followers (user, users); use 0 if you want all (users/users).')
parser.add_argument('-fname',default='',help='Custom folder name')


args=parser.parse_args()

api=newt.getTwitterAPI()


def checkDir(dirpath):
  if not os.path.exists(dirpath):
    os.makedirs(dirpath)

def getUsersFromList(userList):
	userList_l =userList.split('/')
	user=userList_l[0]
	list=userList_l[1]
	tmp=newt.listDetailsByScreenName({},api.list_members,user,list)
	u=[]
	for i in tmp:
		u.append(tmp[i].screen_name)
	return u

sampleSize=args.sample

if args.fname!=None: fpath=str(args.fname)+'/'
else:fpath=''
now = datetime.datetime.now()


def outputter():
	checkDir(fd)
		
	print 'Writing file...'
	
	writer=csv.writer(open(fn,'wb+'),quoting=csv.QUOTE_ALL)
	writer.writerow([ 'source','screen_name','name','description','location','time_zone','created_at','contributors_enabled','url','listed_count','friends_count','followers_count','statuses_count','favourites_count','id_str','id','verified','utc_offset','profile_image_url','protected'])
	
	twDetails={}
	for u in twd:
		twDetails[u.screen_name]=u
		ux=[source]
		for x in [u.screen_name,u.name,u.description,u.location,u.time_zone]:
			if x != None:
				ux.append(unicodedata.normalize('NFKD', unicode(x)).encode('ascii','ignore'))
			else: ux.append('')
		for x in [u.created_at,u.contributors_enabled,u.url,u.listed_count,u.friends_count,u.followers_count,u.statuses_count,u.favourites_count,u.id_str,u.id,u.verified,u.utc_offset,u.profile_image_url,u.protected]:
			ux.append(x)
		try:
			writer.writerow(ux)
		except: pass
	
	
twd=[]
twn=[]
if args.list!=None:
	source=args.list.replace('/','_')
	users=getUsersFromList(args.list)
	fd='reports/'+fpath+args.list.replace('/','_')+'/'
	fn=fd+'listTest_'+now.strftime("_%Y-%m-%d-%H-%M-%S")+'.csv'
	print fn
	for l in newt.chunks(users,100):
		#print 'partial',l
  		tmp=api.lookup_users(screen_names=l)
  		for u in tmp:
  			twd.append(u)
  			twn.append(u.screen_name)
  	outputter()
else: exit(-1)

for user in twn:
	currSampleSize=sampleSize
	source=user
	twd=[]
	fd='reports/'+fpath #+user+'/'
	
	fn=fd+user+'_fo_'+str(sampleSize)+'_'+now.strftime("_%Y-%m-%d-%H-%M-%S")+'.csv'
	print 'grabbing follower IDs'
	try:
		mi=tweepy.Cursor(api.followers_ids,id=user).items()
	except: 
		continue
	users=[]
	for m in mi: users.append(m)
	biglen=str(len(users))
	print 'Number of followers:',biglen
	#HACK
	if str(len(users))>10000: currSampleSize=10000
	if currSampleSize>0:
		if len(users)>currSampleSize:
			users=random.sample(users, currSampleSize)
			print 'Using a random sample of '+str(currSampleSize)+' from '+str(biglen)
		else:
			print 'Fewer members ('+str(len(users))+') than sample size: '+str(currSampleSize) 
	n=1
	print 'Hundred batching' 
	for l in newt.chunks(users,100):
		#print 'partial',l
		print str(n)
		n=n+1
  		tmp=api.lookup_users(user_ids=l)
  		for u in tmp:twd.append(u)
	print '...done'
	outputter()
