import newt,csv,unicodedata,os
import networkx as nx
import newtx as nwx
api=newt.getTwitterAPI()

users=['lfeatherstone','jamesgraymp','davidevennett','mike_fabricant']
projpath='test'
sampleSize=997


def checkDir(dirpath):
  if not os.path.exists(dirpath):
    os.makedirs(dirpath)

def outputter(fn,twd):
	f=open(fn,'wb+')
	writer=csv.writer(f,quoting=csv.QUOTE_ALL)
	k=[ 'source','screen_name','name','description','location','time_zone','created_at','contributors_enabled','url','listed_count','friends_count','followers_count','statuses_count','favourites_count','id_str','id','verified','utc_offset','profile_image_url','protected']
	writer.writerow(k)
	
	for uu in twd:
		u=twd[uu]
		ux=[user]
		for x in [u.screen_name,u.name,u.description,u.location,u.time_zone]:
			if x != None:
				ux.append(unicodedata.normalize('NFKD', unicode(x)).encode('ascii','ignore'))
			else: ux.append('')
		for x in [u.created_at,u.contributors_enabled,u.url,u.listed_count,u.friends_count,u.followers_count,u.statuses_count,u.favourites_count,u.id_str,u.id,u.verified,u.utc_offset,u.profile_image_url,u.protected]:
			ux.append(x)
		try:
			writer.writerow(ux)
		except: pass
	f.close()


#get friends of followers of user
def getFriendsProjection(tw={},maxf=5000):
	newt.gephiOutputFileByName(api,projname+'/friends_innerfriends.gdf', tw,maxf=maxf)
	newt.gephiOutputFileByName(api,projname+'/friends__extrafriends.gdf', tw,'extrafriends',maxf=maxf)
	newt.gephiOutputFileByName(api,projname+'/friends__outerfriends.gdf', tw,'outerfriends',maxf=maxf)


def labelGraph(LG,idlist):
	idlabels=newt.twDetailsFromIds(api,idlist)
	outputter(projname+'/followersCommonFriends.csv',idlabels)
	for id in idlabels:
		if str(id) in LG.node:
			LG.node[str(id)]['label']=idlabels[id].screen_name
			LG.node[str(id)]['fo_count']=idlabels[id].followers_count
			LG.node[str(id)]['fr_count']=idlabels[id].friends_count
			LG.node[str(id)]['updates']=idlabels[id].statuses_count
			LG.node[str(id)]['indegree']=LG.in_degree(str(id))
			if idlabels[id].followers_count>0:
				LG.node[str(id)]['fo_prop']=1.0*LG.in_degree(str(id))/idlabels[id].followers_count
			else:
				LG.node[str(id)]['fo_prop']=0.0
	return LG

def filterNet(DG,mindegree=None,indegree=100,outdegree=50,outdegreemax=9999999,indegreemax=999999):
	print 'In filterNet'
	filter=[]
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
	nx.write_graphml(L, projname+"/followersCommonFriends.graphml")
	nx.write_edgelist(L, projname+"/followersCommonFriends.txt",data=False)

def handleUser(user):
	#get details of followers of user
	twd=newt.getTwitterFollowersDetailsByIDs(api,user,sampleSize)
	twc={}
	twDetails={}
	
	for t in twd:
		if t in twc:
			twc[t]=twc[t]+1
		else:
			twc[t]=1
			twDetails[t]=twd[t]
	
	
	outputter(projname+'/followers.csv',twd)
	
	getFriendsProjection(twDetails)
	
	fn=projname+'/friends__outerfriends.gdf'
	DG=nwx.directedNetworkFromGDF(fn)
	print DG.order(),DG.size()
	
	fn=projname+'/big_netstats.csv'
	f=open(fn,'wb+')
	writer=csv.writer(f,quoting=csv.QUOTE_ALL)
	writer.writerow(['user','indegree','outdegree'])
	for n in DG:
		writer.writerow( [n, DG.in_degree(n), DG.out_degree(n) ] )
	f.close()
	
	fn=projname+'/followers_netstats.csv'
	f=open(fn,'wb+')
	writer=csv.writer(f,quoting=csv.QUOTE_ALL)
	writer.writerow(['user','indegree','outdegree','fullindegree','fulloutdegree'])
	filter= [n for n in DG if DG.out_degree(n)>0]
	L=DG.subgraph(filter)
	for n in L:
		writer.writerow( [n, L.in_degree(n), L.out_degree(n),DG.in_degree(n), DG.out_degree(n) ] )
	f.close()
	
	fn=projname+'/followersfriends_netstats.csv'
	f=open(fn,'wb+')
	writer=csv.writer(f,quoting=csv.QUOTE_ALL)
	writer.writerow(['user','indegree','outdegree','fullindegree','fulloutdegree'])
	filter= [n for n in DG if DG.in_degree(n)>0]
	L=DG.subgraph(filter)
	for n in L:
		writer.writerow( [n,L.in_degree(n), L.out_degree(n),DG.in_degree(n), DG.out_degree(n)] )
	f.close()
	
	fn=projname+'/followersfriends10_netstats.csv'
	f=open(fn,'wb+')
	writer=csv.writer(f,quoting=csv.QUOTE_ALL)
	writer.writerow(['user','indegree','outdegree','fullindegree','fulloutdegree'])
	filter= [n for n in DG if DG.in_degree(n)>10]
	L=DG.subgraph(filter)
	for n in L:
		writer.writerow( [n, L.in_degree(n), L.out_degree(n),DG.in_degree(n), DG.out_degree(n)] )
	f.close()
	
	filterNet(DG)

for user in users:
	projname=projpath+'/'+user
	checkDir(projname)

	handleUser(user)
		
#add count of inner friends to followers details
#find common outerfriends
#get details of common outerfriends
#find indegree of common outerfriends
