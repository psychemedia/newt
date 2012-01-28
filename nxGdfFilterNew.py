import networkx as nx
import newtx as nwx
import csv,sys,newt
import datetime
import numpy as np
import matplotlib
import matplotlib.pyplot as plt
import argparse

run=['filter']
#['filter','reciprocal']

api=newt.getTwitterAPI()

def getNodeAttr(cell):
	cell=cell.strip()
	cell=cell.split()
	return cell[0].strip(),cell[1].strip()

def labelGraph(LG,idlist):
	idlabels=newt.twNamesFromIds(api,idlist)
	for id in idlabels:
		if str(id) in LG.node:
			LG.node[str(id)]['label']=idlabels[id]
	return LG
	 
#G=nx.Graph()

addUserFriendships=1


#Add in parseArg to handle command line inputs
try:
  mindegree=sys.argv[1]
except:
  mindegree=10

try:
	user=sys.arg[2]
except:
	addUserFriendships=0
	user=''

try:
	typ=sys.argv[3]
except:
	typ=0

path='reports'
#agent='fq50_combinedfollowers_0ormore_sample50'
#agent="edgehill"
#agent='hashtag-fote11/followers_2ormore_sample50'

agent='fq50_combinedfriends_4ormore_sample2000'
agent='hashtag-lseneted/followers_3ormore_sample500'
agent='foreignoffice_lists/foreign-office-on-twitter'
agent='theul'
agent='hashtag-gdslaunch/followers_3ormore_sample195'
agent='ukmps'
typ='friends'
typ='.'
tt='extrafriends'
report=tt+'PlusNet_2011-12-27-14-02-53.gdf'
fn='/'.join([path,agent,typ,report])
print 'Loading file...',fn

DG=nwx.directedNetworkFromGDF(fn)

'''
f=open('/'.join([path,agent,report]),'rb')
reader = csv.reader(f)

print "Loading graph..."

phase='nodes'
header=reader.next()

print "Loading nodes..."
for row in reader:	
	if row[0].startswith('edgedef>'):
		phase='edges'
		print "Moving on to edges"
		continue
	elif phase=='edges':
		fromNode=row[0].strip()
		toNode=row[1].strip()
		#print ':'.join(['Adding edge',fromNode,toNode])
		DG.add_edge(fromNode,toNode)
	else:
		id=row[0].strip()
		val=row[1].strip()
		#print ':'.join(['Adding node',id,val])
		if id!='' and val!='':
			DG.add_node(id,label=val)
'''

#print DG.degree()
print DG.order(),DG.size()
#Generate subgraph with nodes that have a greater than N degree:

def filterNet(DG,mindegree):
	if addUserFriendships==1:
		DG=addFocus(DG,user,typ)
	mindegree=int(mindegree)
	filter=[]
	filter= [n for n in DG if DG.degree(n)>=mindegree]
	H=DG.subgraph(filter)
	print "Filter set:",filter
	print H.order(),H.size()
	LH=labelGraph(H,filter)

	now = datetime.datetime.now()
	ts = now.strftime("_%Y-%m-%d-%H-%M-%S")
  
	nx.write_graphml(H, '/'.join([path,agent,typ,tt+"degree"+str(mindegree)+ts+".graphml"]))

	nx.write_edgelist(H, '/'.join([path,agent,typ,tt+"degree"+str(mindegree)+ts+".txt"]),data=False)
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
			print 'adding in user follwerships...'
			userFollowers=api.followers_ids(user)
			print user,'as',userID
			foNet=nwx.createTwitterFnet(api,user,typ='followers')
			DG=nwx.mergeNets(DG,foNet)
	return DG
	
def reciprocalNet(DG):
	if user !='' and addUserFriendships==1 :
		DG=addFocus(DG,user)
	print 'Looking for reciprocal edges...'
	reciprocalG=DG.to_undirected(reciprocal=True)
	print reciprocalG.order(),reciprocalG.size()
	filter= [n for n in reciprocalG if reciprocalG.degree(n)>=1]
	print 'Filtering out unconnected nodes...'
	H=reciprocalG.subgraph(filter)
	print "Filter set:",filter
	print H.order(),H.size()
	LH=nwx.labelGraph(api,H,filter)
	nx.write_graphml(H, "junk/testReciprocal.graphml")


if 'filter' in run: filterNet(DG,mindegree)
if 'reciprocal' in run:
	reciprocalNet(DG)