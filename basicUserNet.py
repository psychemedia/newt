import sys,newt

def report(m):
  newt.report(m,True)

api=newt.getTwitterAPI()

#----------------------------------------------------------------
#user settings
user=sys.argv[1]

try:
  typ=sys.argv[2]
except:
  typ="friends"
#----------------------------------------------------------------
tw={}

if typ=="followers":
  tw=newt.getTwitterFollowersDetailsByIDs(api,user)
else:
  tw=newt.getTwitterFriendsDetailsByIDs(api,user)


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
if typ=="friends":
	newt.gephiOutputFile(api,user+'/'+typ, tw,'extrafriends')
	newt.gephiOutputFile(api,user+'/'+typ, tw,'outerfollowers')
'''
newt.gephiOutputFile(api,user, tw,'outerfriends')
newt.gephiOutputFile(api,user, tw,'outerfollowers')
newt.googleCSEDefinitionFile("XXX",user, tw)
newt.googleCSEDefinitionFileWeighted("XXX",user, tw)
'''