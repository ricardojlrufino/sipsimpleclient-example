#/usr/bin/python

from application.notification import NotificationCenter
from sipsimple.account import AccountManager
from sipsimple.application import SIPApplication
from sipsimple.core import SIPURI, ToHeader
from sipsimple.lookup import DNSLookup, DNSLookupError
from sipsimple.storage import FileStorage
from sipsimple.session import Session
from sipsimple.streams import MediaStreamRegistry
from sipsimple.threading.green import run_in_green_thread
from threading import Event

class SimpleCallApplication(SIPApplication):

    def __init__(self):
        SIPApplication.__init__(self)
        self.ended = Event()
        self.callee = None
        self.session = None
        notification_center = NotificationCenter()
        notification_center.add_observer(self)

    def call(self, callee):
        self.callee = callee
        self.start(FileStorage('config'))

    @run_in_green_thread
    def _NH_SIPApplicationDidStart(self, notification):
        self.callee = ToHeader(SIPURI.parse(self.callee))
        account = AccountManager().get_account("ricardo.rufino@XXX.com.br");
        try:
            uri = SIPURI(host=account.sip.outbound_proxy.host, port=account.sip.outbound_proxy.port, parameters={'transport': account.sip.outbound_proxy.transport})
            routes = DNSLookup().lookup_sip_proxy(uri, ['udp']).wait()
        except DNSLookupError, e:
            print 'DNS lookup failed: %s' % str(e)
        else:
            
            self.session = Session(account)
	    print 'Routes: %s' % str(routes)	
            self.session.connect(self.callee, routes, streams=[MediaStreamRegistry.AudioStream()])

    def _NH_SIPSessionGotRingIndication(self, notification):
        print 'Ringing!'

    def _NH_SIPSessionDidStart(self, notification):
        audio_stream = notification.data.streams[0]
        print 'Audio session established using "%s" codec at %sHz' % (audio_stream.codec, audio_stream.sample_rate)

    def _NH_SIPSessionDidFail(self, notification):
        print 'Failed to connect'
        self.stop()

    def _NH_SIPSessionDidEnd(self, notification):
        print 'Session ended'
        self.stop()

    def _NH_SIPApplicationDidEnd(self, notification):
        self.ended.set()

# place an audio call to the specified SIP URI in user@domain format
# target_uri="sip:fillipe.patriota@XXX.com.br" 
target_uri="sip:target@XXX.com.br" 
application = SimpleCallApplication()
application.call(target_uri)
print "Placing call to %s, press Enter to quit the program" % target_uri
raw_input()
application.session.end()
application.ended.wait()
