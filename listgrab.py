import sys, os, newt, argparse, datetime, csv, random
import networkx as nx
import newtx as nwx

import urllib, unicodedata

parser = argparse.ArgumentParser(description='Data about list members')
group = parser.add_mutually_exclusive_group()
group.add_argument('-list',help='Grab users from a list. Provide source as: username/listname')

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


users=getUsersFromList(args.list)
twd=[]
for l in newt.chunks(users,100):
	#print 'partial',l
  	tmp=api.lookup_users(screen_names=l)
  	for u in tmp:twd.append(u)

fn='reports/listTest_'+args.list.replace('/','_')+'.csv'
writer=csv.writer(open(fn,'wb+'),quoting=csv.QUOTE_ALL)
writer.writerow([ 'screen_name','name','description','created_at','contributors_enabled','url','listed_count','friends_count','followers_count','statuses_count','id_str','id','verified'])

twDetails={}
for u in twd:
	twDetails[u.screen_name]=u
	ux=[]
	for x in [u.screen_name,u.name,u.description]:
		ux.append(unicodedata.normalize('NFKD', x).encode('ascii','ignore'))
	for x in [u.created_at,u.contributors_enabled,u.name,u.url,u.listed_count,u.friends_count,u.followers_count,u.statuses_count,u.id_str,u.id,u.verified]:
		ux.append(x)
	writer.writerow(ux)