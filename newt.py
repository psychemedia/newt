import tweepy, simplejson, urllib, os,datetime,re
import md5, tempfile, time,random
import csv,yql
import itertools
#import klout
import xml.sax.saxutils as saxutils
from urlparse import urlparse
import networkx as nx

import privatebits
import unicodedata
import sqlite3
#----------------------------------------------------------------

#--- sqlite database handling
def getdb():
	return sqlite3.connect('newt.db')

def getdbc():
	db=getdb()
	return db.cursor()
	
#tables: frfo,user,tweet
#dbc.execute('CREATE TABLE frfo (`from` int, `to` int, `type` text)')
#dbc.execute('CREATE TABLE user ( `id` int, `screen_name` text,`desc` text,`location` text)')
#dbc.execute('CREATE TABLE tweet ( `id` int, `from' int, `text` text,`date` date)')

#----------------------------------------------------------------

#import backtype
#def getBackTypeKey():
#  key=privatebits.getBackTypeKey()
#  return key

def getBitlyKey():
  bu,bkey=privatebits.getBitlyKey()
  return bu,bkey
  
def getTwapperkeeperKey():
  key=privatebits.getTwapperkeeperKey()
  return key

def getKloutKey():
  kkey=privatebits.getKloutKey()
  return kkey

def getPeerIndexKey():
  pkey=privatebits.getPeerIndexKey()
  return pkey

  
def getYahooOAuthKey():
  key,shared_secret=privatebits.getYahooOAuthKey()
  return key,shared_secret
  
def getYahooAppID():
  appid=privatebits.getYahooAppID()
  return appid
  
def getTwitterKeys():
  consumer_key,consumer_secret,skey,ssecret=privatebits.getTwitterKeys()
  return consumer_key,consumer_secret,skey,ssecret

def expandBitlyURL(burl):
  bu,bkey=getBitlyKey()
  url='http://api.bit.ly/v3/expand?shortUrl='+urllib.quote(burl)+'&login='+bu+'&apiKey='+bkey+'&format=json'
  print 'url: '+url
  r=simplejson.load(urllib.urlopen(url))
  return r['data']['expand']
  # for j in r['data']['expand']:
  #   print 'long '+j['long_url']

def getBackTypedPageData(burl,sources,page,data):
  print 'Getting more backtype data... Page:',page
  key=getBackTypeKey()
  url='http://api.backtype.com/connect.json?page='+str(page)+'&url='+urllib.quote(burl)+'&sources='+sources+'&itemsperpage=1000+&key='+key
  xdata=simplejson.load(urllib.urlopen(url))
  for c in xdata['comments']:
    data['comments'].append(c)
  if 'next_page' in xdata:
    data=getBackTypedPageData(burl,sources,xdata['next_page'],data)
  return data

def clurn(burl):
  burl=burl.split('?')[0]
  return burl

def ascii(s): return "".join(i for i in s if ord(i)<128)


def getBackTypedURLData(burl,sources='twitter'):
  key=getBackTypeKey()
  
  burl=clurn(burl)
  url='http://api.backtype.com/connect.json?url='+urllib.quote(burl)+'&sources='+sources+'&itemsperpage=1000+&key='+key
  data=simplejson.load(urllib.urlopen(url))
  
  print 'Getting Backtype data for',url
  if 'next_page' in data:
    print 'Trying another page of Backtype data'
    data=getBackTypedPageData(burl,sources,data['next_page'],data)
  else:
    print 'Only 1 page of Backtype data'

  return data

def getTweetFromID(api, id):
  try:
    twt=api.get_status(id)
  except:
    twt=''
  return twt

def getTweetsFromIDs(api, ids):
  tweets=[]
  for id in ids:
    twt=getTweetFromID(api, id)
    if twt!='':
      tweets.append(twt)
  return tweets

def getTweetsAboutURL(api,url):
  data=getBackTypedURLData(url)
  ids=[]
  for id in data['comments']:
    ids.append(id['tweet_id'])
  return getTweetsFromIDs(api, ids)
  
def getTwUserNamesTweetingURL(api,url):
  statuses=getTweetsAboutURL(api,url)
  users=[]
  for status in statuses:
    user=status.author.screen_name
    if user not in users:
      users.append(user)
  return users

def getTwUserDetailsTweetingURL(api,users,url):
  statuses=getTweetsAboutURL(api,url)
  for status in statuses:
    user=status.author.screen_name
    if user not in users:
      print user
      users[user]=status.author
  return users


def generateGoogleCSEDefinitionFile(cse,tag, tw,typ='flat'):
  report("Generating Google CSE definition file")
  fname='listhomepages_'+typ+'.xml'
  f=openTimestampedFile(tag,fname)
  f.write("<GoogleCustomizations>\n\t<Annotations>\n")
  for u in tw:
    un=tw[u]
    if  type(un) is tweepy.models.User:
      l=un.url
      if l:
       urls = re.findall('http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\(\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+', l)
       for l in urls:
        #l=l.split(' ')[0]
        #if "http://bit.ly" in url:
        #  urls=expandBitlyURL(burl)
        #l=urls[0]
        #l=l.strip()
        lo=l
        l=l.replace("http://","")
        if not l.endswith('/') and '?' not in l:
          l=l+"/*"
        else:
          if l[-1]=="/":
            l=l+"*"
        report("- using "+lo+" as "+l)
        weight=1.0
        if typ is 'weighted':
          if hasattr(un, 'status'):
            weight=un.status
          else:
            weight=0
        f.write("\t\t<Annotation about=\""+l+"\" score=\""+str(weight)+"\">\n")
        f.write("\t\t\t<Label name=\""+cse+"\"/>\n")
        f.write("\t\t</Annotation>\n")
  f.write("\t</Annotations>\n</GoogleCustomizations>")
  report("...Google CSE definition file DONE")
  f.close()


def googleCSEDefinitionFileWeighted(cse,tag, tw):
  generateGoogleCSEDefinitionFile(cse,tag, tw,'weighted')
  
def googleCSEDefinitionFile(cse,tag, tw):
  generateGoogleCSEDefinitionFile(cse,tag, tw,'flat')

def getBitlyUserLinks(user):
  links=[]
  url='http://bit.ly/u/'+user+'.json'
  data = simplejson.load(urllib.urlopen(url))
  for i in data['data']:
    links.append(i['url'])
  return links


#----------------------------------------------------------------
def getTwapperkeeperURL(tag,type,start,end,page=1):
  key=getTwapperkeeperKey()
  url='http://api.twapperkeeper.com/2/notebook/tweets/?apikey='+key+'&name='+tag+'&type='+type+'&since='+start+'&until='+end+'&rpp=1000&page='+str(page)
  return url
#----------------------------------------------------------------

#----------------------------------------------------------------  
def getTwapperkeeperPage(tag,type,start,end,page=1):
  report("Getting page "+str(page))
  url= getTwapperkeeperURL(tag,type,start,end,page)
  
  #fetcher = DiskCacheFetcher('cache')
  #page=fetcher.fetch(url, 3600)
  #r=simplejson.loads(page)
  
  fetcher=DiskCacheFetcherfname('cache')
  fn=fetcher.fetch(url, 3600)
  f=open(fn)
  data=f.read()
  f.close()
  r=simplejson.loads(data)
  
  #r=simplejson.load(urllib.urlopen(url))
  
  return r['response']
#----------------------------------------------------------------

#----------------------------------------------------------------
def parseTwapperkeeperResponse(tweeters,response,c):
  report("..parsing page")
  if 'tweets_returned' in response:
   for i in response['tweets_returned']:
    c+=1
    u=i['from_user'].strip()
    if u in tweeters:
      tweeters[u]['count']+=1
    else:
      report("New user: "+u)
      tweeters[u]={}
      tweeters[u]['count']=1
  return tweeters,c
#----------------------------------------------------------------


#----------------------------------------------------------------  
def getTwapperkeeperArchiveTweeters(tweeters,tag,start,end,type='hashtag'):
  report("Getting Twapperkeeper archive tweeters")
  count=0
  num=0
  r=getTwapperkeeperPage(tag,type,start,end)
  tweeters,count=parseTwapperkeeperResponse(tweeters,r,count)
  #if there is only one page, does Twapperkeeper report the tweets_found_count?
  if 'tweets_found_count' in r:
   if r['tweets_found_count'] is not None:
     num=int(r['tweets_found_count'])

  page=2
  while count<num:
    r=getTwapperkeeperPage(tag,type,start,end,page)
    tweeters,count=parseTwapperkeeperResponse(tweeters,r,count)
    page+=1
  
  return tweeters
#----------------------------------------------------------------

#----------------------------------------------------------------
def getTwitterAPI(cachetime=360000):
  #----------------------------------------------------------------
  #API settings for Twitter
  consumer_key,consumer_secret,skey,ssecret=getTwitterKeys()
  #----------------------------------------------------------------

  #----------------------------------------------------------------
  #API initialisation for Twitter
  auth = tweepy.OAuthHandler(consumer_key, consumer_secret)
  auth.set_access_token(skey, ssecret)
  #api = tweepy.API(auth)
  api = tweepy.API(auth, cache=tweepy.FileCache('cache',cachetime), retry_errors=[500], retry_delay=5, retry_count=2)
  #----------------------------------------------------------------
  return api
#----------------------------------------------------------------

#----------------------------------------------------------------
def getTwitterAuth():
  #----------------------------------------------------------------
  #API settings for Twitter
  consumer_key,consumer_secret,skey,ssecret=getTwitterKeys()
  #----------------------------------------------------------------

  #----------------------------------------------------------------
  #API initialisation for Twitter
  auth = tweepy.OAuthHandler(consumer_key, consumer_secret)
  auth.set_access_token(skey, ssecret)
  return auth
#----------------------------------------------------------------


#----------------------------------------------------------------
def report(m, verbose=True):
  if verbose is True:
    print m
#----------------------------------------------------------------

#----------------------------------------------------------------
def getGenericCachedData(url, cachetime=36000):
  fetcher=DiskCacheFetcherfname('cache')
  fn=fetcher.fetch(url, cachetime)
  f=open(fn)
  data=f.read()
  f.close()
  #print 'data----',data
  jdata=simplejson.loads(data)
  return jdata

def getKloutDetails(twpl,kd={}):
  kkey=getKloutKey()
  #klout=new Klout()
  print twpl
  twl=chunks(twpl,5)
  for f5 in twl:
    u=','.join(f5)
    url='http://api.klout.com/1/users/show.json?key='+kkey+'&users='+u
    data=getGenericCachedData(url)
    for d in data['users']:
      print d
      kd[d['twitter_screen_name']]=d
  return kd
  

#----------------------------------------------------------------

def getPeerIndexDetails(twpl,cachetime=36000):
  pkey=getPeerIndexKey()
  for u in twpl:
    url='http://api.peerindex.net/1/profile/show.json?id='+u+'&api_key='+pkey
    data=getGenericCachedData(url,cachetime)
    for d in data:
      print data[d]
    time.sleep(2)

#----------------------------------------------------------------
def createListIfRequired(api, tag):
  lists=api.lists()
  listexists= False

  for l in lists:
    for l2 in l:
      if type(l2) is tweepy.models.List:
        if l2.slug==tag:
          listexists= True
          report("List appears to exist")
    
  if listexists is False:
    report("List doesn't appear to exist... creating it now")
    api.create_list(tag)

#----------------------------------------------------------------  
def getLanyrdPeopleXingEvent(twpl,year, event,typ='attendees'):
  #attendees or trackers
  y = yql.Public()
  query="select href from html where url='http://lanyrd.com/"+str(year)+"/"+event+"/' and xpath='//div[@class=\""+typ+"-placeholder placeholder\"]/ul[@class=\"user-list\"]/li/a'"
  result = y.execute(query)
  for row in result.rows:
    lpersonpath=row.get('href')
    twurl=getTwitterNameFromLanyrdPerson(lpersonpath)
    ret=(twurl.replace('http://twitter.com/',''),typ)
    twpl.append(ret)
  return twpl
  
def getLanyrdPeopleFromEvent(year,event):
  twpl=[]
  print "Getting attendees of",event
  twpl=getLanyrdPeopleXingEvent(twpl,year, event,typ='attendees')
  print "Getting trackers of",event
  twpl=getLanyrdPeopleXingEvent(twpl,year, event,typ='trackers')
  return twpl

def getTwitterNameFromLanyrdPerson(lpersonpath):
  y = yql.Public()
  query = "select href from html where url='http://lanyrd.com"+lpersonpath+"' and xpath='//a[@class=\"icon twitter url nickname\"]'"
  result = y.execute(query)
  for row in result.rows:
    return row.get('href')
  return 'oops'
#----------------------------------------------------------------  

def placemakerGeocodeLatLon(address):
  encaddress=urllib.quote_plus(address)
  appid=getYahooAppID()
  url='http://where.yahooapis.com/geocode?location='+encaddress+'&flags=J&appid='+appid
  data = simplejson.load(urllib.urlopen(url))
  if data['ResultSet']['Found']>0:
    for details in data['ResultSet']['Results']:
      return details['latitude'],details['longitude']
  else:
    return False,False

def twSearchNear(tweeters,tags,num,place='mk7 6aa,uk',term='', dist=1,exclRT=False):
  t=int(num/100)+1
  if t>15:t=15
  bigdata=[]
  page=1
  lat,lon=placemakerGeocodeLatLon(place)
  while page<=t:
    #url='http://search.twitter.com/search.json?rpp=100&page='+str(page)+'&q='+urllib.quote_plus(q)
    url='http://search.twitter.com/search.json?geocode='+str(lat)+'%2C'+str(lon)+'%2C'+str(1.0*dist)+'km&rpp=100&page='+str(page)+'&q=''within%3A'+str(dist)+'km'
    print url
    if term!='':
      url+='+'+urllib.quote_plus(term)
    '''
    if since!='':
     url+='+since:'+since
    '''
    page+=1
    
    data = simplejson.load(urllib.urlopen(url))
    for i in data['results']:     
     if (exclRT==False) or (exclRT==True and not i['text'].startswith('RT @')):
      u=i['from_user'].strip()
      if u in tweeters:
        tweeters[u]['count']+=1
      else:
        report("New user: "+u)
        tweeters[u]={}
        tweeters[u]['count']=1
      ttags=re.findall("#([a-z0-9]+)", i['text'], re.I)
      for tagx in ttags:
        if tagx not in tags:
    	  tags[tagx]=1
    	else:
    	  tags[tagx]+=1
    bigdata.extend(data['results'])    
  return tweeters,tags,bigdata
  '''
  t=int(num/100)+1
  if t>15:t=15
  page=1
  lat,lon=placemakerGeocodeLatLon(place)
  while page<=t:
    url='http://search.twitter.com/search.json?geocode='+str(lat)+'%2C'+str(lon)+'%2C'+str(1.0*dist)+'km&rpp=100&page='+str(page)+'&q=+within%3A'+str(dist)+'km'
    print url
    if term!='':
      url+='+'+urllib.quote_plus(term)

    #if since!='':
    # url+='+since:'+since
    page+=1
    data = simplejson.load(urllib.urlopen(url))
    for i in data['results']:
     if not i['text'].startswith('RT @'):
      u=i['from_user'].strip()
      if u in tweeters:
        tweeters[u]['count']+=1
      else:
        report("New user: "+u)
        tweeters[u]={}
        tweeters[u]['count']=1
      ttags=re.findall("#([a-z0-9]+)", i['text'], re.I)
      for tag in ttags:
        if tag not in tags:
    	  tags[tag]=1
    	else:
    	  tags[tag]+=1
    	    
  return tweeters,tags
'''

def twSearchHashtag(tweeters,tags,num,tag='ukoer', since='',term='',exclRT=False):
  t=int(num/100)+1
  if t>15:t=15
  page=1
  bigdata=[]
  while page<=t:
    url='http://search.twitter.com/search.json?tag='+tag+'&rpp=100&page='+str(page)+'&result_type=recent&include_entities=false&q='
    print url
    if term!='':
      url+='+'+urllib.quote_plus(term)
    '''
    if since!='':
     url+='+since:'+since
    '''
    page+=1
    
    data = simplejson.load(urllib.urlopen(url))
    for i in data['results']:
     if (exclRT==False) or (exclRT==True and not i['text'].startswith('RT @')):
      u=i['from_user'].strip()
      if u in tweeters:
        tweeters[u]['count']+=1
      else:
        report("New user: "+u)
        tweeters[u]={}
        tweeters[u]['count']=1
      ttags=re.findall("#([a-z0-9]+)", i['text'], re.I)
      for tagx in ttags:
        if tagx not in tags:
    	  tags[tagx]=1
    	else:
    	  tags[tagx]+=1
    bigdata.extend(data['results'])    
  return tweeters,tags,bigdata

def twSearchTerm(tweeters,tags,num,q='ukoer', since='',term='',exclRT=False):
  t=int(num/100)+1
  if t>15:t=15
  bigdata=[]
  page=1
  while page<=t:
    url='http://search.twitter.com/search.json?rpp=100&page='+str(page)+'&q='+urllib.quote_plus(q)
    print url
    if term!='':
      url+='+'+urllib.quote_plus(term)
    '''
    if since!='':
     url+='+since:'+since
    '''
    page+=1
    
    data = simplejson.load(urllib.urlopen(url))
    for i in data['results']:     
     if (exclRT==False) or (exclRT==True and not i['text'].startswith('RT @')):
      u=i['from_user'].strip()
      if u in tweeters:
        tweeters[u]['count']+=1
      else:
        report("New user: "+u)
        tweeters[u]={}
        tweeters[u]['count']=1
      ttags=re.findall("#([a-z0-9]+)", i['text'], re.I)
      for tagx in ttags:
        if tagx not in tags:
    	  tags[tagx]=1
    	else:
    	  tags[tagx]+=1
    bigdata.extend(data['results'])    
  return tweeters,tags,bigdata
  
#----------------------------------------------------------------
def destroyListIfRequired(api,tag):
  lists=api.lists()
  listexists= False

  for l in lists:
    for l2 in l:
      if type(l2) is tweepy.models.List:
        if l2.slug==tag:
          listexists=True
          report("List appears to exist...destroying it now")
          api.destroy_list(l2.slug)

  if listexists is False:
    report("List did not appear to exist...")
#----------------------------------------------------------------


def txtFileToList(api,o,tag,fname):
  f=open(fname)
  members=[]
  for i in f:
    members.append(i)
  addManyToListByScreenName(api,o,tag,members)
  f.close()
#----------------------------------------------------------------
def addManyToListByScreenName(api,o,tag,members):
  l=[]
  createListIfRequired(api, tag)
  for u in tweepy.Cursor(api.list_members,owner=o,slug=tag).items():
    if  type(u) is tweepy.models.User:
      l.append(u.screen_name)
  for u in members:
      if u in l:
        report(u+' in list')
      else:
        report('Adding '+u+' to '+tag+' list')
        try:
          api.add_list_member(tag, u)
        except:
          report("Hmm... didn't work for some reason")
#----------------------------------------------------------------

def mergeDicts(dicts,x=False):
  merger={}
  for d in dicts:
    for i in d:
      if x is True:
        if i in merger:
          for c in merger[i]['classVals']:
            d[i]['classVals'][c]+='::'+merger[i]['classVals'][c]
      merger[i]=d[i]
  return merger

  
def twNamesFromIds(api,idlist):
  twr={}
  twl=chunks(idlist,99)
  for f100 in twl:
    report("Hundred batch....")
    try:
      twd=api.lookup_users(user_ids=f100)
      for u in twd:
        if  type(u) is tweepy.models.User:
          if u.screen_name != 'none':
            print u.id,u.screen_name 
            twr[u.id]=u.screen_name
    except:
      report("Failed lookup...")  
  return twr

def twDetailsFromIds(api,idlist):
  twr={}
  twl=chunks(idlist,99)
  for f100 in twl:
    report("Hundred batch....")
    try:
      twd=api.lookup_users(user_ids=f100)
      for u in twd:
        if  type(u) is tweepy.models.User:
          if u.screen_name != 'none':
            print u.id,u.screen_name 
            twr[u.id]=u
    except:
      report("Failed lookup...")  
  return twr
  
def twWhois(api,idlist):
  twr={}
  twl=chunks(idlist,99)
  for f100 in twl:
    report("Hundred batch....")
    try:
      twd=api.lookup_users(user_ids=f100)
      for u in twd:
        if  type(u) is tweepy.models.User:
          if u.screen_name != 'none':
            print u.id,u.screen_name 
            twr[u.screen_name]=u
    except:
      report("Failed lookup...")  
  return twr
        
def getTwitterUsersDetailsByScreenNames(api,users):
  twr={}
  twl=chunks(users,99)
  for f100 in twl:
    report("Hundred batch....")
    try:
      twd=api.lookup_users(screen_names=f100)
      for u in twd:
        if  type(u) is tweepy.models.User:
          twr[u.screen_name]=u
          #also works on  screen_names
    except:
      report("Failed lookup...")  
  return twr

def getTwitterUsersDetailsByIDs(api,users):
  twr={}
  twl=chunks(users,99)
  for f100 in twl:
    report("Hundred batch....")
    try:
      twd=api.lookup_users(user_ids=f100)
      for u in twd:
        if  type(u) is tweepy.models.User:
          twr[u.screen_name]=u
          #also works on  screen_names
    except:
      report("Failed lookup...")  
  return twr
  
def getTwitterFriendsDetailsByIDs(api,user,sample='all'):
  return getTwitterUserDetailsByIDs(api,user,"friends",sample)

def getTwitterFollowersDetailsByIDs(api,user,sample='all'):
  return getTwitterUserDetailsByIDs(api,user,"followers",sample)

def getTwitterUserDetailsByIDs(api,user,typ="friends",sample='all'):
  twr={}
  if typ is 'friends':
    #members=api.friends_ids(user)
    #NEED to rewrute downstream to work with iterator?
    mi=tweepy.Cursor(api.friends_ids,id=user).items()
    members=[]
    for m in mi: members.append(m)
    #hack bugfix - no idea what's going on
    if isinstance(members,tuple): members,junk=members
  else:
    try:
    	#members=api.followers_ids(user)
    	mi=tweepy.Cursor(api.followers_ids,id=user).items()
    	members=[]
    	for m in mi: members.append(m)
    	if isinstance(members,tuple): members,junk=members
    except:
    	members=[]
    #hack bugfix - no idea what's going on
    if isinstance(members,tuple): members,junk=members
    
  if sample=='all': twl=chunks(members,99)
  else:
  	sample=int(sample)
  	if len(members)>sample:
  		membersSample=random.sample(members, sample)
  		print 'Using a random sample of '+str(sample)+' from '+str(len(members))
  	else:
  		membersSample=members
  		print 'Fewer members ('+str(len(members))+') than sample size: '+str(sample) 
  	twl=chunks(membersSample,99)
  for f100 in twl:
    report("Hundred batch on "+typ+"....")
    try:
      twd=api.lookup_users(user_ids=f100)
      for u in twd:
        if  type(u) is tweepy.models.User:
          twr[u.screen_name]=u
          #also works on  screen_names
    except:
      report("Failed lookup...")  
  return twr

def gephiOutputNodeDef(f,members,extras=None):
  header=gephiCoreGDFNodeHeader()
  f.write(header+'\n')
  for u in members:
    u2=members[u]
    if u2.screen_name!='none':    
      f.write(gephiCoreGDFNodeDetails(u2)+'\n')
      
def gephiOutputNodeDefPlus(f,members,membersPlus,extras=None):
  header=gephiCoreGDFNodeHeader()
  f.write(header+','+membersPlus['newt::headerPlus']+'\n')
  extras=membersPlus['newt::headerPlus'].split(',')
  for u in members:
    u2=members[u]
    if u2.screen_name!='none':
      extension=''
      for e in extras:
        e=e.strip()
        key=e.split(' ')[0]
        if u in membersPlus:
          print 'extras',extras,'e',e,'key',key,'val',str(membersPlus[u][key])
          extension=extension+','+str(membersPlus[u][key]).strip()
        else:
          print 'extras',extras,'e',e,'key',key,'val',str(0),'error',u
          extension=extension+','+str(0)
      f.write(gephiCoreGDFNodeDetails(u2)+extension+'\n')

   
def gephiCoreGDFNodeHeader(typ='twitter'):
  if (typ=='delicious'):
    header='nodedef> name VARCHAR,label VARCHAR, type VARCHAR'
  elif (typ=='min'):
    header='nodedef> name VARCHAR,label VARCHAR'
  else:
    header='nodedef> name VARCHAR,label VARCHAR, totFriends INT,totFollowers INT, location VARCHAR, description VARCHAR'
  return header
  
def gephiCoreGDFNodeDetails(u2):
  u2=tidyUserRecord(u2)
  details=str(u2.id)+','+u2.screen_name+','+str(u2.friends_count)+','+str(u2.followers_count)+',"'+u2.location+'","'+u2.description+'"'
  return details
  
def gephiOutputNodeDefExtended(f,members,extensions):
  header=gephiCoreGDFNodeHeader()
  for x in extensions:
    y=x.split(' ')
    header+=','+y[0]+' '+y[1]
  f.write(header+'\n')
  for u in members:
    u2=members[u]['user']
    if u2.screen_name!='none': 
      fout=gephiCoreGDFNodeDetails(u2)
      for x in extensions:
        y=x.split(' ')
        if y[1]=='INT':
          fout+=','+str(members[u]['classVals'][y[0]])
        else:
          fout+=',"'+str(members[u]['classVals'][y[0]])+'"'
      f.write(fout+'\n')
   
def tidyUserRecord(u2):
  if u2.location is not None:
    u2.location=u2.location.replace('\r',' ')
    u2.location=u2.location.replace('\n','  ')
    u2.location=u2.location.encode('ascii','ignore')
  else:
    u2.location=''
  if u2.description is not None:
    u2.description=u2.description.replace('\r',' ')
    u2.description=u2.description.replace('\n',' ')
    u2.description=u2.description.encode('ascii','ignore')
  else:
    u2.description=''
  return u2

def gephiOutputEdgeDefInner(api,f,members,typ='friends',maxf=4000):
  f.write('edgedef> user VARCHAR,friend VARCHAR\n')
  i=0
  membersid=[]
  for id in members:
    membersid.append(members[id].id)
  M=len(members)
  Ms=str(M)
  for id in members:
    i=i+1
    friend=members[id]
    foafs={}
    report("- finding "+typ+" of whatever (friends? followers?) was passed in of "+friend.screen_name+' ('+str(i)+' of '+Ms+')')
    #danger hack AJH TH - try to minimise long waits for large friend counts
    if typ == 'friends' and int(friend.friends_count)>0 and int(friend.friends_count)<int(maxf):
      try:
        #foafs=api.friends_ids(friend.id)
        mi=tweepy.Cursor(api.friends_ids,id=friend.id).items()
        foafs=[]
        for m in mi: foafs.append(m)
        #hack bugfix - no idea what's going on
        if isinstance(foafs,tuple): foafs,junk=foafs
      except tweepy.error.TweepError,e:
        report(e)
    elif typ == 'followers':
      if int(friend.followers_count)>0 and int(friend.followers_count)<int(maxf):
        try:
          #foafs=api.followers_ids(friend.id)
          mi=tweepy.Cursor(api.followers_ids,id=friend.id).items()
          foafs=[]
          for m in mi: foafs.append(m)
          #hack bugfix - no idea what's going on
          if isinstance(foafs,tuple): foafs,junk=foafs
        except tweepy.error.TweepError,e:
          report(e)
      else: print 'too many...skipping'
    #print membersid,'.....',foafs
    cofriends=intersect(membersid,foafs)
    #being naughty - changing .status to record no. of foafs/no. in community
    if hasattr(members[id], 'status'):
      members[id].status=0.7+0.3*len(cofriends)/M
      report("...weight: "+str(members[id].status))
    for foaf in cofriends:
      f.write(str(friend.id)+','+str(foaf)+'\n')
 
def gephiOutputEdgeDefExtra(api,f,members,typ='friends',maxf=100000):
  f.write('edgedef> user VARCHAR,friend VARCHAR\n')
  i=0
  membersid=[]
  for id in members:
    membersid.append(members[id].id)
  M=len(members)
  for id in members:
    friend=members[id]
    foafs={}
    report("- finding extra"+typ+" of whatever (friends? followers?) was passed in of "+friend.screen_name)
    if typ =='friends':
      if friend.friends_count>maxf:
        foafs=[]
      else:
        try:
          #foafs=api.friends_ids(friend.id)
          mi=tweepy.Cursor(api.friends_ids,id=friend.id).items()
          foafs=[]
          for m in mi: foafs.append(m)
          if isinstance(foafs,tuple): foafs,junk=foafs
        except tweepy.error.TweepError,e:
          report(e)
    else:
      if friend.followers_count>maxf:
        foafs=[]
      else:
        try:
          #foafs=api.followers_ids(friend.id)
          mi=tweepy.Cursor(api.followers_ids,id=friend.id).items()
          foafs=[]
          for m in mi: foafs.append(m)
          if isinstance(foafs,tuple): foafs,junk=foafs
        except tweepy.error.TweepError,e:
          report(e)
    extrafriends=diffset(foafs,membersid)
    #being naughty - changing .status to record no. of foafs/no. in community
    if hasattr(members[id], 'status'):
      members[id].status=0.7+0.3*len(extrafriends)/M
      report("...weight: "+str(members[id].status))
    for foaf in extrafriends:
      f.write(str(friend.id)+','+str(foaf)+'\n')

def gephiOutputEdgeDefOuter(api,f,members,typ='friends',mode='inclusive',maxf=100000):
  f.write('edgedef> user VARCHAR,friend VARCHAR\n')
  i=0
  membersid=[]
  for id in members:
    membersid.append(members[id].id)
  M=len(members)
  Ms=str(M)
  i=0
  for id in members:
    i=i+1
    friend=members[id]
    foafs={}
    report("- finding "+typ+" of whatever (friends? followers?) was passed in of "+friend.screen_name+' ('+Ms+' of '+str(i)+')')
    try:
      if typ is 'friends':
        if friend.friends_count>maxf: foafs=[]
        else:
          try:
            #foafs=api.friends_ids(friend.id)
            mi=tweepy.Cursor(api.friends_ids,id=friend.id).items()
            foafs=[]
            for m in mi: foafs.append(m)
            if isinstance(foafs,tuple): foafs,junk=foafs
          except:
            foafs=[]
      else:
        if friend.followers_count>maxf: foafs=[]
        else:
          try:
            #foafs=api.followers_ids(friend.id)
            mi=tweepy.Cursor(api.followers_ids,id=friend.id).items()
            foafs=[]
            for m in mi: foafs.append(m)

            if isinstance(foafs,tuple): foafs,junk=foafs
          except:
            foafs=[]
      #cofriends=intersect(membersid,foafs)
      #being naughty - changing .status to record no. of foafs/no. in community
      #if hasattr(members[id], 'status'):
      #  members[id].status=0.7+0.3*len(foafs)/M
      #  report("...weight: "+str(members[id].status))
      if (mode=='inclusive'):
        for foaf in foafs:
          f.write(str(friend.id)+','+str(foaf)+'\n')
      else:
        for foaf in foafs:
          if foaf not in membersid:
            f.write(str(friend.id)+','+str(foaf)+'\n')
    except tweepy.error.TweepError,e:
      report(e)

def gephiOutputFilePlus(api,dirname, members,membersPlus,typ='innerfriends',fname='PlusNet.gdf'):
  report("Generating Gephi file using: "+typ)
  f=openTimestampedFile(dirname,typ+fname)
  gephiOutputNodeDefPlus(f,members,membersPlus)
  if typ is 'innerfriends':
    gephiOutputEdgeDefInner(api,f,members,'friends')
  elif typ is 'innerfollowers':
    gephiOutputEdgeDefInner(api,f,members,'followers')
  elif typ is 'outerfriends':
    gephiOutputEdgeDefOuter(api,f,members,'friends')
  elif typ is 'outerfollowers':
    gephiOutputEdgeDefOuter(api,f,members,'followers')
  elif typ is 'extrafriends':
    gephiOutputEdgeDefExtra(api,f,members,'friends')

  f.close()
  report("...Gephi "+typ+" file generated")
	
	
def gephiOutputFile(api,dirname, members,typ="innerfriends",fname='Net.gdf',maxf=100000):
  report("Generating Gephi file using: "+typ)
  f=openTimestampedFile(dirname,typ+fname)
  gephiOutputNodeDef(f,members)
  if typ is 'innerfriends':
    gephiOutputEdgeDefInner(api,f,members,'friends',maxf=maxf)
  elif typ is 'innerfollowers':
    gephiOutputEdgeDefInner(api,f,members,'followers',maxf=maxf)
  elif typ is 'extrafriends':
    gephiOutputEdgeDefExtra(api,f,members,'friends',maxf=maxf)
  elif typ is 'outerfriends':
    gephiOutputEdgeDefOuter(api,f,members,'friends',maxf=maxf)
  elif typ is 'outerfollowers':
    gephiOutputEdgeDefOuter(api,f,members,'followers',maxf=maxf)
  elif typ is 'extrafollowers':
    gephiOutputEdgeDefExtra(api,f,members,'followers',maxf=maxf)
  f.close()
  report("...Gephi "+typ+" file generated")

def gephiOutputFileByName(api,fname, members,typ="innerfriends",maxf=100000):
  report("Generating Gephi file using: "+typ)
  f=open(fname,'wb+')
  gephiOutputNodeDef(f,members)
  if typ is 'innerfriends':
    gephiOutputEdgeDefInner(api,f,members,'friends',maxf=maxf)
  elif typ is 'innerfollowers':
    gephiOutputEdgeDefInner(api,f,members,'followers',maxf=maxf)
  elif typ is 'extrafriends':
    gephiOutputEdgeDefExtra(api,f,members,'friends',maxf=maxf)
  elif typ is 'outerfriends':
    gephiOutputEdgeDefOuter(api,f,members,'friends',maxf=maxf)
  elif typ is 'outerfollowers':
    gephiOutputEdgeDefOuter(api,f,members,'followers',maxf=maxf)
  elif typ is 'extrafollowers':
    gephiOutputEdgeDefExtra(api,f,members,'followers',maxf=maxf)
  f.close()
  report("...Gephi "+typ+" file generated")


def report_hashtagsearch(dirname,tweeters,tags):
  report("Generating search summary files")
  f=openTimestampedFile(dirname,'tweeps.txt')
  for tweep in tweeters:
    f.write(str(tweep)+'\n')
  f.close()
  f=openTimestampedFile(dirname,'cotags.txt')
  for tag in tags:
    f.write(str(tag)+'\n')
  f.close()
 
def extendUserList(tw,extensions):
  ttx={}
  for t in tw:
    ttx[t]={}
    ttx[t]['user']=tw[t]
    ttx[t]['classVals']={}
    for x in extensions:
      y=x.split(' ')
      ttx[t]['classVals'][y[0]]=y[1]
  return ttx

def deExtendUserList(membersX):
  members={}
  for m in membersX:
    members[m]=membersX[m]['user']
  return members
  
def gephiOutputFileExtended(api,dirname, membersX,extensions,typ="innerfriends",fname='friendsNet.gdf'):
  report("Generating extended Gephi file using: "+typ)
  fname='X'+fname
  f=openTimestampedFile(dirname,fname)
  gephiOutputNodeDefExtended(f,membersX,extensions)
  members=deExtendUserList(membersX)
  if typ is 'innerfriends':
    #gephiOutputEdgeDefInnerFriends(api,f,members)
    gephiOutputEdgeDefInner(api,f,members,'friends')
  f.close()
  report("...extended Gephi "+typ+" file generated")

def openTimestampedFile(fpath,fname,timestamp=True):
  fpath='reports/'+fpath
  now = datetime.datetime.now()
  ts = now.strftime("_%Y-%m-%d-%H-%M-%S")
  checkDir(fpath)
  fpart=fname.split('.')
  if timestamp:
    f=open(fpath+'/'+fpart[0]+'%s.'%ts+fpart[1],'w')
  else:
    f=open(fpath+'/'+fname,'w')
  return f
  
def checkDir(dirpath):
  if not os.path.exists(dirpath):
    os.makedirs(dirpath)

#----------------------------------------------------------------
#return common members of two lists
def intersect(a, b):
     return list(set(a) & set(b))
     
def diffset(a,b):
	#returns items in a not in b
	return filter(lambda x:x not in b,a)
#----------------------------------------------------------------
#networkx code

def createNet(api,members,mode='inner',ftyp='friends'):
  network=nx.DiGraph()
  membersid=[]
  for id in members:
    membersid.append(members[id].id)
  for id in members:
    member=members[id]
    foafs={}
    report("- finding followers ("+mode+ftyp+") of whatever (friends? followers?) was passed in of "+member.screen_name)
    if ftyp is 'friends':
      try:
        #foafs=api.friends_ids(member.id)
        mi=tweepy.Cursor(api.friends_ids,id=member.id).items()
        foafs=[]
        for m in mi: foafs.append(m)
      except tweepy.error.TweepError,e:
        report(e)
    else:
      try:
        #foafs=api.followers_ids(member.id)
        mi=tweepy.Cursor(api.followers_ids,id=member.id).items()
        foafs=[]
        for m in mi: foafs.append(m)
      except tweepy.error.TweepError,e:
        report(e)

    if mode=='inner':
      print "doing inner bits"
      cofriends=intersect(membersid,foafs)
      for foaf in cofriends:
        network.add_edge(member.id,foaf)
    elif mode=='exclouter':
      for foaf in foafs:
        if foaf not in membersid:
          network.add_edge(member.id,foaf)
    else:
      print "doing outer bits"
      for foaf in foafs:
        network.add_edge(member.id,foaf)
  return network
  

#----------------------------------------------------------------
#Yield successive n-sized chunks from l
def chunks(l, n):   
    for i in xrange(0, len(l), n):
        yield l[i:i+n]

    
#----------------------------------------------------------------
def listDetailsByID(tw,l,o,t):
  report("Fetching list details for "+t+"...")
  for u in tweepy.Cursor(l,owner=o,slug=t).items():
    if  type(u) is tweepy.models.User:
      tw[int(u.id)]=u
  return tw
#----------------------------------------------------------------

def listsByUser(api,u):
	return tweepy.Cursor(api.lists,user=u).items()

def listMemberships(api,o):
  lists=tweepy.Cursor(api.lists_memberships,user=o).items()
  memberships={}
  for l in lists:
    '''
    list={}
    list['owner']=l.user.screen_name
    list['name']=l.name
    list['memberCount']=l.member_count
    list['subscriberCount']=l.subscriber_count
    '''
    ltag=l.user.screen_name+'_'+l.name
    memberships[ltag]=l.subscriber_count
  for i in sorted(memberships, key=memberships.get, reverse=True):
    print i,memberships[i]
  return memberships
#----------------------------------------------------------------
def listDetailsByScreenName(tw,l,o,t):
  report("Fetching list details for "+t+"...")
  for u in tweepy.Cursor(l,owner=o,slug=t).items():
    if  type(u) is tweepy.models.User:
      tw[u.screen_name]=u
  return tw
  
def listsmembershipByScreenName(lists,api,u,max=250):
  l=api.lists_memberships
  report("Fetching list memberships for "+u+"...")
  lc=0
  for ul in tweepy.Cursor(l,user=u).items():
    if type(ul) is tweepy.models.List:
      ulu=ul.uri
      if ulu in lists:
      	if u not in lists[ulu]: 
          lists[ulu].append(u)
      else:
        lists[ulu]=[u]
        lc=lc+1
    if max!='all':
      if lc > int(max): return lists
  return lists
#----------------------------------------------------------------


#http://developer.yahoo.com/python/python-caching.html
class DiskCacheFetcher:
    def __init__(self, cache_dir=None):
        # If no cache directory specified, use system temp directory
        if cache_dir is None:
            cache_dir = tempfile.gettempdir()
        self.cache_dir = cache_dir
    def fetch(self, url, max_age=0):
        # Use MD5 hash of the URL as the filename
        filename = md5.new(url).hexdigest()
        filepath = os.path.join(self.cache_dir, filename)
        if os.path.exists(filepath):
            if int(time.time()) - os.path.getmtime(filepath) < max_age:
                #return open(filepath).read()
                report("using cached copy of Twapperkeeper archive")
                fc=open(filepath)
                data=fc.read()
                fc.close()
                return data
        report("fetching fresh copy of Twapperkeeper archive")
        # Retrieve over HTTP and cache, using rename to avoid collisions
        data = urllib.urlopen(url).read()
        fd, temppath = tempfile.mkstemp()
        fp = os.fdopen(fd, 'w')
        fp.write(data)
        fp.close()
        os.rename(temppath, filepath)
        return data
        
#ah tweak
class DiskCacheFetcherfname:
    def __init__(self, cache_dir=None):
        # If no cache directory specified, use system temp directory
        if cache_dir is None:
            cache_dir = tempfile.gettempdir()
        self.cache_dir = cache_dir
    def fetch(self, url, max_age=0):
        # Use MD5 hash of the URL as the filename
        filename = md5.new(url).hexdigest()
        filepath = os.path.join(self.cache_dir, filename)
        if os.path.exists(filepath):
            if int(time.time()) - os.path.getmtime(filepath) < max_age:
                #return open(filepath).read()
                report("using cached copy of fetched url: "+url)
                return filepath
        report("fetching fresh copy of fetched url: "+url)
        # Retrieve over HTTP and cache, using rename to avoid collisions
        data = urllib.urlopen(url).read()
        fd, temppath = tempfile.mkstemp()
        fp = os.fdopen(fd, 'w')
        fp.write(data)
        fp.close()
        os.rename(temppath, filepath)
        return filepath
        
#----------

def getGoogSocialAPIData(userURL,typ='friends'):
  mode='&edo=1'
  if (typ=='followers'):
  	mode='&edi=1'
  elif (typ=='both'):
    mode='&edi=1&edo=1'
  #both not yet implemented
  folk=[]
  gurl='http://socialgraph.apis.google.com/lookup?q='+userURL+mode
  data = simplejson.load(urllib.urlopen(gurl))
  if (typ=='followers'):
    nref='nodes_referenced_by'
  else:
    nref='nodes_referenced'
  for i in data['nodes'][userURL][nref]:
      folk.append(i.replace('http://twitter.com/',''))
  return folk
#------------
#fname="homepageurls2.csv"
def outputHomepageURLs(api,fpath,tw,tag):
  print os.getcwd()
  f=openTimestampedFile(fpath,'homepageurls.txt',False)
  for u in tw:
    un=tw[u]
    if  type(un) is tweepy.models.User:
      l=un.url
      if l:
       urls = re.findall('http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\(\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+', l)
       for l in urls:
        f.write(l+','+tag+'\n')
  f.close()


def opmlFromCSV(fpath='',fname='homepageurls.txt'):
  if fpath=='':
    fin='reports/'+fname
  else:
    fin='reports/'+fpath+'/'+fname
  fo=openTimestampedFile(fpath,'homepageurls.xml')

  writeOPMLHeadopenBody(fo)
  
  f = csv.reader(open(fin, "rb"))
  #url="http://ukwebfocus.wordpress.com"
  first=True
  curr=''
  for line in f:
    url,tag=line
    if curr!=tag:
      if first is True:
        first=False
      else:
        closeOPMLoutline(fo)
      curr=tag
      openOPMLoutline(fo,tag)
    handleOPMLitem(fo,url)

  closeOPMLoutline(fo)
  closeOPMLbody(fo)
            
  fo.close()
 
 
 
def handleOPMLitem(fo,url):
  if url !='':
   try:
    urls = re.findall('http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\(\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+', url)
    for url in urls:
      print "testing",url
      o=url
      url='http://query.yahooapis.com/v1/public/yql/psychemedia/feedautodetect?url='+urllib.quote(url)+'&format=json'
      try:
        data = simplejson.load(urllib.urlopen(url))
        print data
        if data['query']['count']>0:
          print data['query']
          if data['query']['count']==1:
            l=data['query']['results']['link']
            furl=checkPathOnFeedURL(l['href'],o)
            print "*****",furl,l['title']
            handleFeedDetails(fo,furl)
          else:
            for r in data['query']['results']['link']:
              furl=checkPathOnFeedURL(r['href'],o)
              print furl,r['title']
              handleFeedDetails(fo,furl)
      except:
        pass
   except:
     pass

def checkPathOnFeedURL(furl,o):
  if furl.startswith('/'):
    x = urlparse(o)
    furl= 'http://'+x.netloc+furl
  return furl


def writeOPMLHeadopenBody(fo):
  fo.write('<?xml version="1.0" encoding="UTF-8"?>\n')
  fo.write('<opml version="1.0">\n<head>\n\t<title>Generated OPML file</title>\n</head>\n\t<body>\n')

def closeOPMLbody(fo):
  fo.write("</body>\n</opml>")

def openOPMLoutline(f,t):
  f.write('\t\t<outline title="'+t+'" text="'+t+'">\n')

def closeOPMLoutline(f):
  f.write('\t\t</outline>\n')

def writeOPMLitem(f,htmlurl,xmlurl,title):
  title=saxutils.escape(title)
  f.write('\t\t\t<outline text="'+title+'" title="'+title+'" type="rss" xmlUrl="'+xmlurl+'" htmlUrl="'+htmlurl+'"/>\n')

def handleFeedDetails(fo,furl):
  nocomments=True
  url='http://query.yahooapis.com/v1/public/yql/psychemedia/feeddetails?url='+urllib.quote(furl)+'&format=json'
  print "Trying feed url",furl
  try:
    details=simplejson.load(urllib.urlopen(url))
    detail=details['query']['results']['feed']
    #print "Acquired",detail
    for i in detail:
      if i['link']['rel']=='alternate':
        title=i['title'].encode('utf-8')
        hlink=i['link']['href']
        if nocomments is True:
          if not (furl.find('/comments')>-1 or title.startswith('Comments ')):
            writeOPMLitem(fo,hlink,furl,title)
            print 'Using',hlink, furl,title
          else:
            print 'Not using',hlink, furl,title
        else:
          writeOPMLitem(fo,hlink,furl,title)
          print 'Using',hlink, furl,title
        return
  except:
    pass

#-------------------------------
#delicious utils
def getDeliciousTagURL(tag,typ='json', num=100,page=1):
  #need to add a pager to get data when more than 1 page
  # -not pageable? Results limited to curent feed, fixed length?
  return "http://feeds.delicious.com/v2/json/tag/"+tag+"?count=100"

def getDeliciousUrlURL(url):
  durl='http://feeds.delicious.com/v2/json/url/'+md5.new(url).hexdigest()  
  return durl

def getDeliCachedData(url, cachetime=36000):
  fetcher=DiskCacheFetcherfname('cache')
  fn=fetcher.fetch(url, cachetime)
  f=open(fn)
  data=f.read()
  f.close()
  #print 'data----',data
  jdata=simplejson.loads(data)
  return jdata

def getDeliciousUrlData(url):
  durl=getDeliciousUrlURL(url)
  #data = simplejson.load(urllib.urlopen(durl))
  data=getDeliCachedData(durl)
  return data
  
def getDeliciousUserFans(user,fans):
  url='http://feeds.delicious.com/v2/json/networkfans/'+user
  #data = simplejson.load(urllib.urlopen(url))
  data=getDeliCachedData(url)
  for u in data:
    if 'user' in u:
      fans.append(u['user'])
      #time also available: u['dt']
  #print fans
  return fans

def getDeliciousTagsByUser(user):
  tags={}
  url='http://feeds.delicious.com/v2/json/tags/'+user
  #data = simplejson.load(urllib.urlopen(url))
  data=getDeliCachedData(url)
  for tag in data:
    tags[tag]=data[tag]
  return tags

def printDeliciousTagsByNetwork(user,minVal=2):
  f=openTimestampedFile('delicious-socialNetwork','network-tags-'+user+'.gdf')
  f.write(gephiCoreGDFNodeHeader(typ='delicious')+'\n')
 
  network=[]
  network=getDeliciousUserNetwork(user,network)

  for user in network:
    f.write(user+','+user+',user\n')
  f.write('edgedef> user1 VARCHAR,user2 VARCHAR,weight DOUBLE\n')
  for user in network:
    tags={}
    tags=getDeliciousTagsByUser(user)
    for tag in tags:
      if tags[tag]>=minVal:
         f.write(user+',"'+tag.encode('ascii','ignore')+'",'+str(tags[tag])+'\n')
  f.close()

def getDeliciousUserNetwork(user,network):
  url='http://feeds.delicious.com/v2/json/networkmembers/'+user
  #data = simplejson.load(urllib.urlopen(url))
  data=getDeliCachedData(url)
  for u in data:
    if 'user' in u:
      network.append(u['user'])
    #time also available: u['dt']
  #print network
  return network
  
def getDeliciousNetworkFans(user):
  f=openTimestampedFile('delicious-socialNetwork','network-all-'+user+'.gdf')
  f2=openTimestampedFile('delicious-socialNetwork','network-inner-'+user+'.gdf')
  f.write(gephiCoreGDFNodeHeader(typ='min')+'\n')
  f.write('edgedef> user1 VARCHAR,user2 VARCHAR\n')
  f2.write(gephiCoreGDFNodeHeader(typ='min')+'\n')
  f2.write('edgedef> user1 VARCHAR,user2 VARCHAR\n')
  network=[]
  network=getDeliciousUserNetwork(user,network)
  for folk in network:
    time.sleep(1)
    folk2=[]
    print "Fetching data for network member "+folk
    folk2=getDeliciousUserFans(folk,folk2)
    for folk2 in folk2:
      f.write(folk+','+folk2+'\n')
      if folk2 in network:
        f2.write(folk+','+folk2+'\n')
  f.close()
  f2.close()

def getDeliciousUsersByURL(url,users):
  data = getDeliciousUrlData(url)
  for i in data:
    user=i['a']
    if user not in users:
      users.append(user)
  return users

def getDeliciousUsersByTag(tag,users):
  durl=getDeliciousTagURL(tag)
  #data = simplejson.load(urllib.urlopen(durl))
  data=getDeliCachedData(url)
  for i in data:
    user=i['a']
    if user not in users:
      users.append(user)
  return users

def getDeliciousXY(agent,X='fans',Y='fans'):
  ftag=agent
  if X=='bookmarkers':
    ftag=md5.new(agent).hexdigest()
  f=openTimestampedFile('delicious-socialNetwork',X+Y+'-all-'+ftag+'.gdf')
  f2=openTimestampedFile('delicious-socialNetwork','-inner-'+ftag+'.gdf')
  f.write(gephiCoreGDFNodeHeader(typ='min')+'\n')
  f.write('edgedef> user1 VARCHAR,user2 VARCHAR\n')
  f2.write(gephiCoreGDFNodeHeader(typ='min')+'\n')
  f2.write('edgedef> user1 VARCHAR,user2 VARCHAR\n')
  Xs=[]
  if X=='fans':
    Xs=getDeliciousUserFans(agent,Xs)
  elif X=='network':
    Xs=getDeliciousUserNetwork(agent,Xs)
  elif X=='taggers':
    Xs=getDeliciousUsersByTag(agent,Xs)
  elif X=="bookmarkers":
    Xs=getDeliciousUsersByURL(agent,Xs)
  for anX in Xs:
    time.sleep(2)
    Ys=[]
    print "Fetching XY "+Y+" data for "+anX
    if Y=='fans':
      Ys=getDeliciousUserFans(anX,Ys)
    elif Y=='network':
      Ys=getDeliciousUserNetwork(anX,Ys)

    for anY in Ys:
      f.write(anX+','+anY+'\n')
      if anY in Xs:
        f2.write(anX+','+anY+'\n')

  f.close()
  f2.close()

def getDeliciousFanFans(user):
  f=openTimestampedFile('delicious-socialNetwork','fans-all-'+user+'.gdf')
  f2=openTimestampedFile('delicious-socialNetwork','fans-inner-'+user+'.gdf')
  f.write(gephiCoreGDFNodeHeader(typ='min')+'\n')
  f.write('edgedef> user1 VARCHAR,user2 VARCHAR\n')
  f2.write(gephiCoreGDFNodeHeader(typ='min')+'\n')
  f2.write('edgedef> user1 VARCHAR,user2 VARCHAR\n')
  fans=[]
  fans=getDeliciousUserFans(user,fans)
  for fan in fans:
    time.sleep(2)
    fans2=[]
    print "Fetching data for fan "+fan
    fans2=getDeliciousUserFans(fan,fans2)
    for fan2 in fans2:
      f.write(fan+','+fan2+'\n')
      if fan2 in fans:
        f2.write(fan+','+fan2+'\n')
  f.close()
  f2.close()
  
def getDeliciousTaggedURLTagCombos(tag):
  durl=getDeliciousTagURL(tag)
  #data = simplejson.load(urllib.urlopen(durl))
  data=getDeliCachedData(durl)
  uniqTags=[]
  tagCombos=[]
  for i in data:
    url= i['u']
    user=i['a']
    tags=i['t']
    title=i['d']
    for t in tags:
      if t not in uniqTags:
        uniqTags.append(t)
    if len(tags)>1:
      for i,j in combinations(tags,2):
        print i,j
        tagCombos.append((i,j))
  f=openTimestampedFile('delicious-tagCombos',tag+'.gdf')
  f.write(gephiCoreGDFNodeHeader(typ='delicious')+'\n')
  for t in uniqTags:
    f.write(t+','+t+',tag\n')
  f.write('edgedef> tag1 VARCHAR,tag2 VARCHAR\n')
  for i,j in tagCombos:
      f.write(i+','+j+'\n')
  f.close()
 
def getDeliciousBookmarkedURLUserTagsFull(url):
  data=getDeliciousUrlData(url)
  handleDeliciousUsersAndTags('temp','url',data)


def getDeliciousTaggedURLDetailsFull(tag):
  durl=getDeliciousTagURL(tag)
  #data = simplejson.load(urllib.urlopen(durl))
  data=getDeliCachedData(durl)
  handleDeliciousUsersAndTags(tag,'tag',data)
  
def handleDeliciousUsersAndTags(tag,label,data):
  userTags={}
  uniqTags=[]
  for i in data:
    #url= i['u']
    user=i['a']
    tags=i['t']
    #title=i['d']
    if user in userTags:
      for t in tags:
        if t not in uniqTags:
          uniqTags.append(t)
        if t not in userTags[user]:
          userTags[user].append(t)
    else:
      userTags[user]=[]
      for t in tags:
        userTags[user].append(t)
        if t not in uniqTags:
          uniqTags.append(t)
  
  f=openTimestampedFile('delicious-'+label+'Network',tag+'.gdf')
  f.write(gephiCoreGDFNodeHeader(typ='delicious')+'\n')
  for user in userTags:
    f.write(user+','+user+',user\n')
  for t in uniqTags:
    t=unicodedata.normalize('NFKD', t).encode('ascii','ignore')
    f.write(t+','+t+',tag\n')
  f.write('edgedef> user VARCHAR,tag VARCHAR\n')
  for user in userTags:
    for t in userTags[user]:
      t=unicodedata.normalize('NFKD', t).encode('ascii','ignore')
      f.write(user+','+t+'\n')
  f.close()
  
  
#-----------------
#py code
def combinations(iterable, r):
    # combinations('ABCD', 2) --> AB AC AD BC BD CD
    # combinations(range(4), 3) --> 012 013 023 123
    pool = tuple(iterable)
    n = len(pool)
    if r > n:
        return
    indices = range(r)
    yield tuple(pool[i] for i in indices)
    while True:
        for i in reversed(range(r)):
            if indices[i] != i + n - r:
                break
        else:
            return
        indices[i] += 1
        for j in range(i+1, r):
            indices[j] = indices[j-1] + 1
        yield tuple(pool[i] for i in indices)