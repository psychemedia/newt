import sys,newt

def report(m):
  newt.report(m,True)

api=newt.getTwitterAPI()
print api.test()
#----------------------------------------------------------------
#user settings
user=sys.argv[1]

try:
  typ=sys.argv[2]
except:
  typ="friends"
  
try:
  extra=sys.argv[3]
except:
  extra=-1

try:
  sampleSize=int(sys.argv[4])
except:
  sampleSize='all'
#----------------------------------------------------------------
tw={}

if typ=="followers":
  tw=newt.getTwitterFollowersDetailsByIDs(api,user,sampleSize)
else:
  tw=newt.getTwitterFriendsDetailsByIDs(api,user,sampleSize)

f=newt.openTimestampedFile(user+'/'+typ,'sample'+str(sampleSize)+'tweeps.txt')
for tweep in tw:
    f.write(str(tweep)+'\n')
f.close()

report("List members:")
for i in tw:
  report(tw[i].screen_name)
  
'''
report("List members:")
for i in tw:
  report(tw[i].screen_name)
'''  
#newt.gephiOutputFile(api,user+'/'+typ, tw,'outerfriends')
newt.gephiOutputFile(api,user+'/'+typ, tw)
if extra!=-1:
	newt.gephiOutputFile(api,user+'/'+typ, tw,'extrafriends')
	#newt.gephiOutputFile(api,user+'/'+typ, tw,'outerfollowers')
'''
newt.gephiOutputFile(api,user, tw,'outerfriends')
newt.gephiOutputFile(api,user, tw,'outerfollowers')
newt.googleCSEDefinitionFile("XXX",user, tw)
newt.googleCSEDefinitionFileWeighted("XXX",user, tw)
'''