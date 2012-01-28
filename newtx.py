import networkx as nx
import newt
import csv,random

def directedNetworkFromGDF(filename):
	f=open(filename,'rb')
	reader = csv.reader(f)

	print "Loading graph..."

	phase='nodes'
	header=reader.next()
	
	DG=nx.DiGraph()
	
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
	f.close()
	return DG

def labelGraph(api,LG,idlist=None):
	if idlist==None:
		idlist=LG.nodes()
	idlabels=newt.twNamesFromIds(api,idlist)
	for id in idlabels:
		if str(id) in LG.node:
			LG.node[str(id)]['label']=idlabels[id]
	return LG

	
def createTwitterFnet(api,user,typ='friends',samplesize='all'):
	DG=nx.DiGraph()
	userDet=api.get_user(user)
	userID=userDet.id
	if typ is 'friends':
		try:
			members=api.friends_ids(user)
		except: members=[]
		if samplesize !='all' and samplesize<len(members):
			members=random.sample(members, samplesize)
		fedges=[(str(userID),str(u)) for u in members]
		DG.add_edges_from(fedges)
	else:
		try:
			members=api.followers_ids(user)
		except: members=[]
		if samplesize !='all'  and samplesize<len(members):
			members=random.sample(members, samplesize)
		fedges=[(str(u),str(userID)) for u in members]
		DG.add_edges_from(fedges)

	
	return DG

def progressPrint(u,fetchlen,i):
	i=i+1
	print 'getting data for',u,str(i),'of',fetchlen
	return i

#-----CRIB  http://www.drewconway.com/zia/?p=345

def snowball_search(network,api,cur_round=1):
    users=nodes_at_degree(network,cur_round)    # Get all the users at the current round degree
    fetchlen=len(users)
    i=0
    for u in users:
    	i=progressPrint(u,fetchlen,i)
        search_results=createTwitterFnet(api,u)
        network=nx.compose(network,search_results)
    return network


def nodes_at_degree(network,degree):
# Get nodes to perform round k search on
    d=network.degree()
    d=d.items()
    return [(a) for (a,b) in d if b==degree]
#---END CRIB
	
def mergeNets(net1,net2):
    return nx.compose(net1,net2)
