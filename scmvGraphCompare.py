import argparse,csv
import networkx as nx
import operator

parser = argparse.ArgumentParser(description='Compare two graphs')
parser.add_argument('-filestub',help='If there is a common prefix in the file paths add it here')
parser.add_argument('-filesuffix',help='If there is a common suffix in the file paths add it here')

parser.add_argument('-files',nargs='*',help='gdf files you want to compare')
parser.add_argument('-labels',nargs='*',help='Labels in same order as gdf files you want to compare')

parser.add_argument('-outpath',help='Filename path for output files')

parser.add_argument('-compare',help='If there is a common prefix in the file paths add it here')

args=parser.parse_args()
if len(args.files)!=len(args.labels): exit(-1)


path=args.outpath
labels=args.labels

if args.filestub!=None: filestub=args.filestub
else: filestub=''
if args.filesuffix!=None: filesuffix=args.filesuffix
else: filesuffix=''

def getCountsFilename(path,label):
	return path+'/counts_'+label+'.csv'

def getCountsCSVwriter(path,label):
	fn=getCountsFilename(path,label)
	f=open(fn,'ab+')
	return f,csv.writer(f)

for label in labels:
	fn=getCountsFilename(path,label)
	f=open(fn,'wb+')
	writer=csv.writer(f)
	writer.writerow(['userid','username','indegree','outdegree','inNorm','fo_count','normaliser'])
	f.close()

inUsers={}

graphs={}
print filestub,args.files
for i in range(0,len(args.files)):
	label=labels[i]
	fn=filestub+args.files[i]+filesuffix
	print fn
	graphs[label]={'graph':nx.read_graphml(fn),'name':label}
	print args.files[i]
	#DG=nx.read_graphml(args.files[i])
	#label=args.labels[i]
	#for node in DG.nodes():
	#	writer.writerow([label,node,DG.node[node]['label'],DG.in_degree(node),DG.out_degree(node)])

for graph in graphs:
	graphs[graph]['inNodes']=[]
	graphs[graph]['outnodecount']=0
	DG=graphs[graph]['graph']
	for node in DG.nodes():
		if DG.in_degree(node)>0:
			user=DG.node[node]['label']
			graphs[graph]['inNodes'].append(user)
			if user not in inUsers:
				inUsers[user]={'fo_count':DG.node[node]['fo_count']}
		if DG.out_degree(node)>0: graphs[graph]['outnodecount']=graphs[graph]['outnodecount']+1

for user in inUsers:
	for graph in graphs:
		inUsers[user][graph]={'incount':0,'normcount':0}
	
data={}
for graph in graphs:
	print "outnodecount",graphs[graph]['outnodecount'],
	data[graph]=set(graphs[graph]['inNodes'])
	DG=graphs[graph]['graph']
	f,writer=getCountsCSVwriter(path,graph)
	for node in DG.nodes():
		user=DG.node[node]['label']
		if user in inUsers:
			inUsers[user][graph]['incount']=DG.in_degree(node)
			inUsers[user][graph]['normcount']=float(DG.in_degree(node))/float(graphs[graph]['outnodecount'])
		writer.writerow([node,DG.node[node]['label'],DG.in_degree(node),DG.out_degree(node),float(DG.in_degree(node))/float(graphs[graph]['outnodecount']),int(DG.node[node]['fo_count']),int(graphs[graph]['outnodecount'])])
	f.close()

if args.compare=='false':exit(-1)

#based on O'reilly Mining Social Web p. 157
#intersection=set()
keys=data.keys()
#for k in range(len(keys)-1):
#	#THE FOLLOWING DOESN'T FIND THE INTERSECTION ACROSS ALL SETS?
#	intersection=data[keys[k]].intersection(data[keys[k-1]])
sets=[]
for key in data:
	sets.append(data[key])
#This seems to be the standard way of finding the intersection of several sets:
intersection=set.intersection(*sets)
	
msg='Common items shared amongst: %s' % ', '.join(keys).strip()
print msg
print '-' * len(msg)


fn=path+'/intersection.csv'
f=open(fn,'wb+')
writer=csv.writer(f)
txt=['name']
for graph in graphs: txt.append(graph)
writer.writerow(txt)
for i in intersection:
	#print i.strip(),inUsers[i.strip()]
	txt=[i]
	for graph in graphs:
		txt.append(inUsers[i][graph]['normcount'])
	writer.writerow(txt)

f.close()