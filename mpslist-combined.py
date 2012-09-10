import newt

def report(m):
  newt.report(m,True)

api=newt.getTwitterAPI()

#----------------------------------------------------------------
#user settings
#----------------------------------------------------------------
twsn={}


tw=[]
tw2={}
tw2['newt::headerPlus']='party VARCHAR'

'''
twsn=newt.listDetailsByScreenName({},api.list_members,'tweetminster','libdems')
for i in twsn:
  tw.append(i)
  tw2[i]={}
  tw2[i]['party']='libdems'

twsn=newt.listDetailsByScreenName({},api.list_members,'tweetminster','others')
for i in twsn:
  tw.append(i)
  tw2[i]={}
  tw2[i]['party']='others'
'''  
def doGroup(group,tw,tw2):
  twsn=newt.listDetailsByScreenName({},api.list_members,'tweetminster',group)
  for i in twsn:
    tw.append(i)
    tw2[i]={}
    tw2[i]['party']=group
  return tw,tw2

affiliations=["parliament","financialtimes","otherukmedia","skynews","telegraph","theindependent","channel4news","guardian","bbc","ukgovernmentdepartments","others","conservatives","labour","libdems"]
label='govtweeps'

#affiliations=["others","conservatives","labour","libdems"]
#label='ukmps'

for aff in affiliations:
  tw,tw2=doGroup(aff,tw,tw2)

tw=newt.getTwitterUsersDetailsByScreenNames(api,tw)
 
newt.gephiOutputFilePlus(api,label, tw,tw2,'innerfriends')
newt.gephiOutputFilePlus(api,label, tw,tw2,'outerfriends')
newt.gephiOutputFilePlus(api,label, tw,tw2,'extrafriends')