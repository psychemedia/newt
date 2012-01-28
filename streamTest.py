import newt,tweepy,time

class StreamListener(tweepy.StreamListener):
    def on_status(self, status):
        try:
            print status.text,str(self.count)
            print '\n %s  %s  via %s\n' % (status.author.screen_name, status.created_at, status.source)
            self.count=self.count-1
            if self.count<0: streamer.disconnect()
        except Exception, e:
            # Catch any unicode errors while printing to console
            # and just ignore them to avoid breaking application.
            pass


api=newt.getTwitterAPI()
authl=newt.getTwitterAuth()

l = StreamListener()
streamer = tweepy.Stream(auth=authl, listener=l, timeout=300.0 )
setTerms = ['this','that']

print "gettong ready"

streamer.count=3

print streamer.count


print "sdsd"

streamer.filter(None,setTerms)

