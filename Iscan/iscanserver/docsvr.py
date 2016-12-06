__doc__ = r"""
           **************************************************************************
            Module      : docserver
            Author      : Lutfur Khundkar
            Purpose     : Multi-threaded server for proprietary image/document storage and retrieval system
            Copyright   : All rights reserved
            
            Exposes iAlert calls to other modules
                To use iAlert, the following steps must be completed
               1. Call this module's initiAlert sub to create the iAlert
                  COM object.
               2. Call this module's ActivateiAlert function to instruct the
                  com object to connect to the server
               3. Send heartbeats or alerts using this module's
                  'SendHeartbeat' or 'SendAlert' functions.
               4. When finished, use the 'DestroyiAlert' sub to shutdown
                  and prevent memory leaks.
    **************************************************************************
    """

import BaseHTTPServer, select, socket, SocketServer, urlparse
import logging, logging.handlers
import sys
import os
import threading, Queue

import time
import traceback
import ctypes
import ctypes.wintypes


import mmap
WIN32_FIND_DATA = ctypes.wintypes.WIN32_FIND_DATAW

__version__ = '0.19'


def convertToTif(pFilename):

    with open(pFilename,'rb') as fp:
        # convert 
        pass

    return

class DocRequestHandler(SocketServer.StreamRequestHandler):

    responses = {
        100: ('Continue', 'Request received, please continue'),
        101: ('Switching Protocols',
              'Switching to new protocol; obey Upgrade header'),

        200: ('OK', 'Request fulfilled, document follows'),
        201: ('Created', 'Document created, URL follows'),
        202: ('Accepted',
              'Request accepted, processing continues off-line'),
        203: ('Non-Authoritative Information', 'Request fulfilled from cache'),
        204: ('No Content', 'Request fulfilled, nothing follows'),
        205: ('Reset Content', 'Clear input form for further input.'),
        206: ('Partial Content', 'Partial content follows.'),

        400: ('ERROR|UNKNOWN ERROR',
              'Bad request syntax or unsupported method'),
        401: ('Unauthorized',
              'No permission -- see authorization schemes'),
        402: ("ERROR|FILE NOT FOUND"),
        33:  ("ERROR: CORRUPT FILE - FILE NOT SAVED"),
        476: ("ERROR|DELETE FAILED OR NOT PERMITTED"),

        }
    

#    def __init__(self, request, client_addr, server, logger=None):
#        SocketServer.StreamRequestHandler.__init__(self, request, client_addr, server)
    def setLogger(self, logger=None):
        self.logger=logger
        if self.logger: pass
        elif self.server.logger:
            self.logger=self.server.logger
        self.logger.info( "%s","Handling connection .. DocRequestHander constructor")
        self.message_end_delim=chr(0)
        return
    
    def parse_request(self, rbuf):
        r""" TODO - documentation
        """

        if len(rbuf)>0:
            self.raw_requestline = self.raw_requestline + rbuf
            if self.message_end_delim in rbuf:
                return self.raw_requestline.split(self.message_end_delim)[0]
            elif len(self.raw_requestline)>1024:
                raise IOError
            else: return False
        else:
            raise socket.error
            
        return False

    def handle_one_request(self):
        r""" TO - dcoumentation
        """
        try:
            self.close_connection = 0
            self.raw_requestline = ""
            self.streamdata=""
            done=False
            CIP=self.client_address[0]
            while not done:
                done=self.parse_request(self.request.recv(1024))
            self.logger.debug("(%s) IN>  STATUS=%s RAW: %s",CIP, bool(done), self.raw_requestline[:1024])
            if done:
#               len(self.raw_requestline) > 65536:
                self.requestline = done
                self.request_version = ''
                self.command = done.split(' ')[0]
                self.logger.info("(%s) IN>  %s",CIP,self.requestline)
                x=self.raw_requestline
                self.streamdata=x[x.index(self.message_end_delim)+1:]
                self.raw_requestline
                    
            if not self.raw_requestline and not self.command:
                self.close_connection = 1
                print "No request received in first 1024 bytes"
                print self.command,'.'+self.raw_requestline+'.'
                self.logger.errors("(%s) SVR> %s No request received after connect",CIP,self.raw_requestline)
                return
            # process admin commands
            if self.command in ('SHUTDOWN','SETDEBUGON','NODEBUG','VERSION','STATS'):
                self.close_connection=1
                self.logger.critical("%s","(%s) ADMIN> %s received" % (CIP,self.command))
                if CIP == '127.0.0.1' or CIP == self.server.server_address[0]:
                    pass
                else:
                    #print "ERROR|COMMAND REMOTE INVOCATION", self.command
                    #print "request",self.command,'received from remote:',CIP #,"(server=",self.server.server_address[0],')'
                    self.logger.critical("(%s) ADMIN> %s received from remote",CIP,self.command)
                    self.send_ok("ERROR|COMMAND INVOKED FROM REMOTE")
                    return
                #print "ready to handle commnd"
                #print "client=",CIP,'.'+self.command+"."
                if self.command=="SHUTDOWN":
                    self.send_ok("OK|SHUTDOWN")
                    self.server._stop_()
                elif self.command=="SETDEBUGON":
                    self.send_ok("OK|SETDEBUGON")
                    self.server._setdebug("ON")
                elif self.command=="NODEBUG":
                    self.send_ok("OK|NODEBUG")
                    self.server._setdebug("OFF")
                elif self.command=="VERSION":
                    print "OK|"+__version__
                    self.send_ok("OK|"+__version__)
                elif self.command=="STATS":
                    self.logger.debug("Found command %s",self.command)
                    rsp="OK|THREAD COUNT="+str(threading.activeCount()-1)
                    try:
                        rsp="%s; TXNS=%d of %d" % (rsp,
                                                   DocServer.request_count,
                                                   DocServer.request_complete)
                    except:
                        self.logger.debug("%s","Error getting txn counts")
                    #print rsp                    
                    self.send_ok(rsp)
                return
                
            self.logger.debug("SVR> Handling command %s",self.command)
            mclass = CmdHandlerFactory(self.command.strip())
            if not mclass:
                self.send_error(501, "ERROR|UNKNOWN COMMAND (%s)" % self.command)
                return
            self.logger.debug("SVR> Found %s handler class",self.command)
            try:
                mclass(self)
            except:
                self.logger.error("%s", "\n\t".join([str(x) for x in sys.exc_info()]))

                self.send_error("ERROR|On Server")
            self.wfile.flush() #actually send the response if not already done.
            mclass=None # mark for gc
        except socket.timeout, e:
            #a read or a write timed out.  Discard this connection
            self.log_error("SVR> Request timed out: %s", self.raw_requestline)
            self.close_connection = 1
            return
        except socket.error, e:
            #a read or a write timed out.  Discard this connection
            self.logger.debug("SVR> Request connection was closed: %s", CIP)
            self.close_connection = 1
            return
        except IOError, e:
            #a read or a write timed out.  Discard this connection
            if len(self.raw_requestline)>0: 
                self.log_warning("(%s) SVR> IO Error: (no message end delimiter in first 1024 bytes) %s", CIP,self.raw_requestline)
            else: 
                self.logger.debug("SVR> Request connection closed by peer [%s]", CIP)
            self.close_connection = 1
            return
        except :
            #a read or a write timed out.  Discard this connection
            self.logger.exception("SVR> Exception")
            self.close_connection = 1
            return

        return
    def handle(self):
        """Handle multiple requests if necessary."""
        self.close_connection = 0
        #print "DocRQH: handle()"
        self.setLogger()
        while not self.close_connection:
            self.handle_one_request()
                

    def send_error(self, code, message=None):
        """Send and log an error reply.

        Arguments are the error code, and a detailed message.
        The detailed message defaults to the short entry matching the
        response code.

        This sends an error response (so it must be called before any
        output has been generated), logs the error, and finally sends
        a piece of HTML explaining the error to the user.

        """

        try:
            short, long = self.responses[code]
        except KeyError:
            short, long = '???', '???'
        if message is None:
            message = short
        explain = long
        if message.startswith('ERROR'): pass
        else: message="ERROR|"+message
        message=message+self.message_end_delim
        self.log_error("OUT> %s", message)
        
        
        # using _quote_html to prevent Cross Site Scripting attacks (see bug #1100201)
        #content = (self.error_message_format %
        #           {'code': code, 'message': _quote_html(message), 'explain': explain})
        self.send_response(message,False)
        return

    error_message_format = "ERROR|UNKNOWN ERROR"
#    error_content_type = DEFAULT_ERROR_CONTENT_TYPE

    def send_ok(self, message="OK|"):
        """Send and log an ok reply.

        """
        
        if message.startswith('OK'): pass
        else: message="OK|"+message

        message=message+self.message_end_delim
        try:
            self.logger.debug("(send_ok) %s",message)
        except:
            pass
        self.send_response(message)
        

    def send_response(self, message='ERROR|UNKNOWN ERROR',log=True):
        r"""Send the response header and log the response code.

        Also send two standard headers with the server software
        version and the current date.

        """
        if log:
            self.log_response("(%s) OUT> %s" ,self.client_address[0],  message)
        self.wfile.write(message)


    def log_request(self):
        """Log an accepted request.

        This is called by send_response().

        """
        self.messagetype="info"
        self.log_message('(%s) OUT> %s' , self.client_address[0],self.requestline)

    def log_response(self, fmt, *args):
        """Log a response (for debugging)

        Arguments are the same as for log_message().

        """
        self.messagetype="info"
        self.log_message(fmt % args)

    def log_error(self, fmt, *args):
        """Log an error.

        This is called when a request cannot be fulfilled.  By
        default it passes the message on to log_message().

        Arguments are the same as for log_message().

        XXX This should go to the separate error log.

        """
        self.messagetype="error"
        self.log_message(fmt % args)

    def log_message(self, msg):
        """Log an arbitrary message.

        This is used by all other logging functions.  Override
        it if you have specific logging wishes.

        The first argument, FORMAT, is a format string for the
        message to be logged.  If the format string contains
        any % escapes requiring parameters, they should be
        specified as subsequent arguments (it's just like
        printf!).

        The client ip address and current date/time are prefixed to every
        message.

        """

        if self.logger:
            loglevel=10
            try:
                loglevel=getattr(self.logger,self.messagetype)
                loglevel(msg)
            except:
                self.logger.info(msg)
#            self.logger.log(loglevel, msg)
        else:
            sys.stderr.write("%s - - [%s] %s\n" % (self.client_address[0], self.log_date_time_string(), format%args))
        return

class DocReqCmd:
#class DocRequestHandler2(SocketServer.StreamRequestHandler):

    # The Python system version, truncated to its first component.
    sys_version = "Python/" + sys.version.split()[0]

    # The server software version.  You may want to override this.
    # The format is multiple whitespace-separated strings,
    # where each string is of the form name[/version].
    server_version = "DocSvr/" + __version__

    tmpFile=""

    known_responses=["OK|FILE MOVED", "OK|FILE COPIED", "OK|FILE DELETED",
                     "OK|NOT EXISTS", "OK|EXISTS", "OK|BAD DIR", "OK|BAD CALL",
                     "OK-LOCKED\t"+tmpFile, "OK\tSTREAM"+tmpFile,
                     "OK\t"+tmpFile]

    # The default request version.  This only affects responses up until
    # the point where the request line is parsed, so it mainly decides what
    # the client gets back when sending a malformed request line.
    # Most web servers default to HTTP 0.9, i.e. don't send a status line.
    default_request_version = "Doc/0.9"

    message_end_delim = chr(0)

    def __init__(self, reqhandler):
        self.request=reqhandler
        self.path=None
        self.target=None
        self.command=None
        self.filesize=None
        self.working=None
        self.server=reqhandler.server
        self.lockHandler = reqhandler.server.lockHandler
        if self.getargs():
            self.processCommand()
            self.cleanup()

    def processCommand(self):
        self.request.send_ok("OK|ECHO %s NOT IMPLEMENTED" % self.command)
        return
        

    def parse_quoted_strings(self,s):
        r=""
        quoted=False
        for i in range(len(s)):
            a=s[i]
            if a == " ":
                if not quoted: a=chr(255)
            elif a == '\"':
                quoted = not quoted
            r=r+a
        return r.split(chr(255))


    def getargs(self):
        """Parse a request (internal).

        The request should be stored in self.raw_requestline; the results
        are in self.command, self.path, self.request_version and
        self.headers.

        Return True for success, False for failure; on failure, an
        error is sent back.

        """
        
        self.command = None  # set in case of error on the first line
        self.request_version = version = self.default_request_version
        requestline = self.request.raw_requestline
        OPEN_STREAM = False
        words=[]
        EOM=self.request.message_end_delim
        if EOM in requestline:
            requestline=requestline.split(EOM)[0]
        if '\"' in requestline:
            words=self.parse_quoted_strings(requestline)
        else:
            words=requestline.split(" ")
            
        self.requestline = requestline
        command = None
        path = None
        target = None
        filesize = None
        workdir = None
        if len(words) > 1:
            command = words[0].strip(" ")
            path = words[1].strip(" ")
            try:
                target=words[2].strip(" ")
                workdir=words[3].strip(" ")
                try:
                    filesize = int(workdir)
                    workdir=self.server.working
                except TypeError:
                    pass
            except:
                pass
        elif len(words) < 2:
            command = words[0].strip(" ")
            self.request.send_error(400,"ERROR|MISSING ARGUMENT(S)")
            return False
        elif not words:
            self.request.send_error(400,"ERROR|INVALID ARGUMENT(S)")
            return False
        else:
            self.send_error(400, "Bad request syntax (%s)" % requestline)
            return False
        self.words=words
        try:
            if path.startswith('\"'):
                path=path[1:-1]        
            if target.startswith('\"'):
                target=target[1:-1]
            if workdir.startswith('\"'):
                workdir=workdir[1:-1]
            if workdir[-1]=='\\':
                workdir=workdir[:-1]
        except: pass
        
            
        self.command, self.path, self.target, self.filesize, self.working = (command, path, target, filesize, workdir)
        

        # Examine the headers and look for a Connection directive
        return True

    def cleanup(self):
        """ Cleanup routine - override in any implemented class as necessary """
        pass
    
    def validatePFN(self,path):
        import os.path
        if os.path.isfile(path) or os.path.isdir(path):
            return 2
        elif os.path.isdir(os.path.dirname(path)):
            return 1
        else:
            return 0

    def translatePath(self,path):

        try:
            if path.startswith("\""):
                return path[1:-1]
        except: pass
        
        return path

    def check_locks(self):

        isLocked=""
        try:

            shouldLock = self.check_lock
            if shouldLock:
                isLocked = "LOCKED"
                isLocked = self.LockHandler.lock(self.path)
        except:
            pass
        return isLocked

    def release_lock(self):
        try:
            shouldLock = self.check_lock
            if shouldLock:
                self.LockHandler.release(self.path)
        except:
            pass
        return
    
    def filecopy(self,s,d,rename=False,makepath=True, overwrite=False):
        import shutil, os, os.path
        try:
            if os.path.isfile(d):
                if overwrite:
                    os.remove(d)
                else:
                    return False
            elif not(os.path.isdir(os.path.dirname(d))) and makepath:
                os.mkdirs(os.path.dirname(d))
            if rename:
                os.rename(s,d)
            else:
                shutil.copyfile(s,d)
            return True
        except:
            return False
    
    def filedelete(self,s):
        import os, os.path
        try:
            if os.path.isfile(s):
                os.remove(s)              
        except:
            pass
        return not os.path.isfile(s)

class CmdHandlerFactory:

    def get(self, s):
        try:
            mclass = s.lower().replace('-',"")
            mod = __import__("action."+mclass)
            _class = getattr(mod, "do"+s)
            
            return _class
        except (ImportError, AttributeError) as e:
            return None


#doFILEMOVE = doFILECOPY
#doGET-LOCK = doGET
#doWEBGET-LOCK = doWEBGET
#doPUT-LOCK = doPUT

class LockManager():
    def __init__(self):
            self.locks_lock=threading.Semaphore()
            self.lockedFiles={}
    
    def _lock(self,setLock,f):
            self.locks_lock.acquire()
            retval=False
            try:
                if setLock:
                    if f not in self.lockedFiles:
                        self.lockedFiles[f]=time.time()
                        retval = True
            except:
                pass
            self.locks_lock.release()
            if setLock: return retval
            return

    def lock(self,a):
            return self._lock(True,a)
        
    def unlock(self,a):
            self._lock(False,a)
            return
        
class DocThreadingMixIn:
    """Mix-in class to handle each request in a new thread."""

    # Decides how threads will act upon termination of the
    # main process
    daemon_threads = False

    def process_request_thread(self, request, client_address):
        """Same as in BaseServer but as a thread.

        In addition, exception handling is done here.

        """
        try:
            self.logger.debug("(%s) %s",client_address[0],"processing request ")
            self.finish_request(request, client_address)
            self.logger.debug("%s","process request thread: finished request")
            self.shutdown_request(request)
        except TypeError, e:
            print e
        except:
            self.handle_error(request, client_address)
            self.shutdown_request(request)

    def process_request(self, request, client_address):
        """Start a new thread to process the request.
            override in ThreadPoolMixIn
        """
        self.logger.debug("%s","DocThreadingMixin process request")
        t = threading.Thread(target = self.process_request_thread,
                             args = (request, client_address))
 #       t.name="Doc_thr_"+str(t)
        t.daemon = self.daemon_threads
        t.start()

class ThreadPoolMixIn(DocThreadingMixIn):
    """
    use a thread pool instead of a new thread on every request
    """
    maxQueueLen = maxThreads = 25
    minThreads = 4
    pool_timeout = 10
    allow_reuse_address = True  # seems to fix socket.error on server restart

    def updatePoolStats(self,latest):
        
        """ Use this to set up and manage a set of worker threads in pool 
            so that we can expand or shrink the pool in times of high or low demand """
            
        # Need to make the following logic thread-safely
        # add current time and update running average of last 10 reqs
        locked=False
        try:
            locked=self.poolLock.acquire()
            self.logger.debug("%s","Pool is locked for updates")
            if len(self.pool_stats)+1>10:
                oldest,latency=self.pool_stats.pop(0)
            DocServer.request_complete+=1
            self.logger.debug("Qued %15.3f, wait %5.3f", latest,time.time()-latest)
            self.pool_stats.append((latest,time.time()-latest))
            self.poolLock.release()
            self.logger.debug("%s","Pool is open for updates")
        except: 
            if locked: 
                self.poolLock.release()
                self.logger.debug("%s","Pool is locked for updates")
        return
        
    def managePool(self,new_request=None):
        locked=False
        try:
            if len(self.pool_stats)>1:
                delay=0
                locked=self.poolLock.acquire()
                self.logger.debug("%s","Pool is locked for management by "+str(self))
                if new_request:
                    if DocServer.request_count:
                        DocServer.request_count+=1
                    else:
                        DocServer.request_count=1
                    self.logger.debug("%s","Added new request - # "+str(DocServer.request_count))
                n=len(self.pool_stats)
                for a in self.pool_stats:
                    delay+=a[1]
                self.poolLock.release()
                delay=delay/float(n)
                self.logger.debug("%s","Pool is open after management")
                self.logger.debug("Average delay = %6.3f",delay)
                if delay>2.0:
                    if threading.activeCount() < maxThreads:
                        # start a few more
                        pass
                if delay < 0.25 and (threading.activeCount()>minThreads):
                        # end a fe threads
                    pass
        except:
            if locked:
                self.poolLock.release()
                self.logger.debug("%s","Pool is open (after except) after management")
        #print "Number of active thread %d" % threading.active_count()

        return

    def __init__(self):
        """
        Initialize Queue and start up a small block of threads to handle requests
        
        We can add or remove threads based on traffic.
        The maximum number of threads will be limited to maxThreads so we don't overwhelm
        the machine
        """
        # set up the threadpool
        self.logger.debug("Setting up threadpool")
        try:
            nthr = int(self.settings["SERVER"]["minthreads"])
            mthr = int(self.settings["SERVER"]["maxthreads"])
            nreq = int(self.settings["SERVER"]["maxrequest"])
            nto = float(self.settings["SERVER"]["pool-timeout"])

            if mth > self.minTheads:
                self.maxThreads = mth
            
            if nth > self.minThreads and nth < self.maxThreads:
                self.minThreads = nth

            if nreq > 10:
                self.maxQueueLen = nreq

            if nto > 1.0:
                self.pool_timeout = nto
            alow_reuse_address = bool(self.settings["SERVER"]["reuse-address"])
            
        except:
            pass

        self.request_pool = Queue.Queue(self.maxQueueLen)
        self._shutdown_event = threading.Event()
        self.pool_stats=[]
        self.poolLock=threading.Semaphore()

        for x in range(self.minThreads):
            t = threading.Thread(target = self.process_request_thread)
            t.setDaemon(1)
            t.name="_thr_"+str(x+1).rjust(3,"0")
            t.start()
        self.logger.debug("%s threads",str(self.minThreads))
            
    def process_request_thread(self):
        """
        obtain request from queue instead of directly from server socket
        """
        while True:
            try:
                self.logger.debug("%s","Blocked waiting for request ")
                request, client_address, que_time = self.request_pool.get(self.pool_timeout, self.pool_timeout)
                self.updatePoolStats(que_time)
                DocThreadingMixIn.process_request_thread(self, request, client_address)
                self.logger.debug("(%s) %s",client_address[0],"processing request complete")
                self.request_pool.task_done()
            except Queue.Empty:
                self.logger.debug("%s","ThreadPoolMixin get request - empty queue")
                sys.exc_clear()
                self.managePool()
                if self._shutdown_event.isSet():
                    self.logger.warning("%s", "Shutting down ")
                    return
            
    def process_request(self, request, client_address):
        """Start a new thread to process the request."""
        self.logger.debug("%s","DocThreadingMixin process request")
        # if all threads are busy, start 3 new ones
        self.managePool(1)
        # otherwise, just place the request in the pool
        self.request_pool.put((request, client_address,time.time()))
        return

    def join2(self):
        """
        Wait on the pool to clear and shut down the worker threads.
            # A nicer place for this would be shutdown(), but this being a mixin,
            # that method can't safely do anything with that method, thus we add
            # an extra method explicitly for clearing the queue and shutting
            # down the workers.
        """

        self.request_pool.join()
        self._shutdown_event.set()

class DocServer (ThreadPoolMixIn,
                           SocketServer.TCPServer):
    request_count=0
    request_complete=0
    last_oid=0
    def __init__ (self, server_address, RequestHandlerClass, logger=None,start=True):
        SocketServer.TCPServer.__init__ (self, server_address,
                                            RequestHandlerClass,start)
        settings = {"server-ip":'127.0.0.1',"port":'2347',"debug":False,"logfile":'DocServer.log',
                    "rootpath":os.path.abspath('.'), "handler-class":DocRequestHandler}
        self.logger = self.logSetup(settings)
        self.serve_forever()

    def __init__ (self):
        self.configfile='scansvr.ini'
        
        self.settings=self.__readConfig()
        settings=self.settings["SERVER"]

        SocketServer.TCPServer.__init__(self, None, None,False)
        #ThreadPoolMixIn.__init__(self)
        self.logger = self.logSetup(settings)
        self.server_address=(settings['bindto'],int(settings['port']))
        self.RequestHandlerClass = settings["handler-class"]
        self.socket = socket.socket(self.address_family,
                                    self.socket_type)
        self.logger.info("%s","\n\n")
        sep="".join(["=" for x in range(30)])
        self.logger.critical("%s",sep+"\tStarting up .. \t"+sep)
        self.working=self.settings["SERVER"]["workingdir"]      
        self.lockHandler = LockManager()
        ThreadPoolMixIn.__init__(self)

        # set up mmap file to dynamically share last processed transaction in thread
        #fm = open('docsvr txns.log','wb')
        #self.mm = mmap.mmap(fm.fileno(),0)
        #try:
        #    self.mm.seek(self.mm.find("thread"))
        #    r=self.mm.readline()
        #    if len(r)>0:
        #        mm.write('0')
        #except:
        #    pass
        try:
            self.server_bind()
            self.logger.critical( "SVR> %s","Bound to: "+str(self.server_address)+" .. Listening")
            self.server_activate()
            self.serve_forever()
        except:
            self.logger.info( "SVR> Could not start server on %s: %d",self.server_address[0],
                              self.server_address[1])
            self.server_close()
            raise

    def _setdebug(self,level):
        if level == "ON":
            self.logger.setLevel(10) #DEBUG
        else:
            self.logger.setLevel(30) #WARNING
                              
                              
        return

    def __readConfig(self):
        import ConfigParser
        c=ConfigParser.SafeConfigParser()
        c.read(self.configfile)
        C=dict([(a,dict(c.items(a)) ) for a in c.sections()])
        # set up the first available ip address as the default address
        svr_defaults = {"bindto":socket.gethostbyname_ex(socket.gethostname())[2][0],
                        "port":'2240', "loglevel":"WARNING", "logfile":'DocServer.log',
                        "workingdir":os.path.abspath('../scanwork'),
                        "rootdir":os.path.abspath('.'),
                        "minthreads":'4', "maxthreads":'12', "maxrequest":'20',"pool-timeout":"10",
                        "handler-class":DocRequestHandler}
        if "SERVER" not in C:
            C["SERVER"]=svr_defaults
        else:
            for k in svr_defaults.keys():
                if k not in C["SERVER"]:
                    C["SERVER"][k]=svr_defaults[k]
        c=None
        return C
        
    def __lock(self,toLock,e):
        # toLock is True is entity is to be locked, False to unlock
        isLocked=False
        
        return isLocked
    def generateOID(self,tpath):
#        import os.path, os
#        import time
        oid=self.last_oid+1
        tf=os.path.join(tpath,str(oid).rjust(8,"0")+".tmp")
        max_tries=100
        while os.path.isfile(tf) and max_tries>0:
            #check if old enough to delete currently 5 min
            if time.time()-os.path.getctime(tf)>300:
                os.remove(tf)
            else:
                oid+=1
                tf=os.path.join(tpath,str(oid).rjust(8,"0")+".tmp")
                max_tries+=-1
        self.last_oid=oid
        return tf
                
    def _start_(self, *args):
        """ This function should read a config file for initial parameters and create an instance of the server
        """
        settings=defaults
        logger=self.logSetup(settings)
        DocServer(server, settings["handler-class"],logger)
        return

    def _stop_(self,*args):

        self._shutdown_event.set()
        self.logger.warning("%s", "Shutdown flags set")
        self.shutdown()

        return
    allow_reuse_address = 1    # Seems to make sense in testing environment

    def server_bind(self):
        """Override server_bind to store the server name."""
        SocketServer.TCPServer.server_bind(self)
        host, port = self.socket.getsockname()[:2]
        self.server_name = socket.getfqdn(host)
        self.server_port = port
      
    def logSetup (self, kwargs):
#        filename = "DocServer.log"
        filename = None
        log_size = 2
        daemon=None
        try:
            filename = kwargs['logfile']
            if kwargs["clearlogfile"] and filename:
                fa=open(filename,'w')
                fa.write('')
                fa.flush()
                fa.close()
        except: pass
            
#        try: 
#            log_size=int(kwargs['log-size'])
#        except: pass

        logger = logging.getLogger ("DocServer")
        l=kwargs['loglevel']
        try:
            lnum = int(kwargs['detaillogging'].strip()) *10
            if lnum in range(10,51,10):
                l=lnum
            logger.setLevel (logging.getLevelName(l))
        except:
            logger.setLevel (logging.WARNING)
        if not filename:
            if not daemon:
                # display to the screen
                handler = logging.StreamHandler ()
            else:
                handler = logging.handlers.RotatingFileHandler (DEFAULT_LOG_FILENAME,
                                                                maxBytes=(log_size*(1<<20)),
                                                                backupCount=5)
        else:
            handler = logging.handlers.RotatingFileHandler (filename,
                                                            maxBytes=(log_size*(1<<20)),
                                                            backupCount=5)
        fmt = logging.Formatter ("[%(asctime)-12s] %(threadName)s %(levelname)-8s: %(message)s")
#                                 "%Y-%m-%d %H:%M:%S"
#                                 "%(levelname)-8s {%(name)s %(threadName)s}"
#                                 " %(message)s" )
        handler.setFormatter (fmt)
            
        logger.addHandler (handler)
        #self.logger = logger
        return logger

def manage_server(p,s):
    s=socket.socket(socket.AF_INET,socket.SOCK_STREAM)
    s.connect(('127.0.0.1',p))
    s.send("%s \x00" % s)
    print s.recv(512)
def set_as_service(svcname,svcpath,svcargs=None):
    import _winreg
    # check if service already exists
    h2=None
    hk=_winreg.OpenKey(_winreg.HKEY_LOCAL_MACHINE, "SYSTEM\\CurrentControlSet\\Services")
    try:
        hk2=_winreg.OpenKey(hk,svcname)
        # service is already set up
        pass
    except:
        pass
    if hk2: _winreg.CloseKey(hk2)
    _winreg.CloseKey(hk)
    """
    Step 1: 
    Download and install Windows Resource Kit. 
    Which was found in my box: C:\Program Files (x86)\Windows Resource Kits\Tools\srvany.exe . 

    Then open command prompt and hit

    sc create "[YourService]" binPath="C:\Program Files (x86)\Windows Resource Kits
    \Tools\srvany.exe" start=auto DisplayName="[YourService Monitor]"

    [SC] CreateService SUCCESS


    Step 2: make a file.reg with following contents and double click on it
    [HKEY_LOCAL_MACHINE\SYSTEM\CurrentControlSet\Services\[YourService]\Parameters]
    "Application"="C:\\[YourService Executable].exe"

     """
    return
    
if __name__ == '__main__':

    import argparse

    parser = argparse.ArgumentParser(description='Document Server Functions')
    parser.add_argument('-ip',
                       help='ip address for server')

    parser.add_argument('-p', type=int, 
                       help='port for server')

    parser.add_argument('-r', 
                       help='root directory')

    parser.add_argument('-o', type=str, 
                       help='manager, server, shutdown, setdebug, nodebug')
    args = parser.parse_args()
    if args.o:
        args.o=args.o.strip('\r\n').strip(" ")
    print  args.ip,args.p,args.o,args.r

    if args.r and False:
        print "moving from ",os.path.abspath('.')
        os.chdir(args.r.strip(' ').strip())
        print "to", os.path.abspath('.')

    if args.o == 'server':
        print 'starting server'
        #a=DocServer()
        a=None
        print "exiting main()"
    elif args.o == 'manager':
        print "starting manager"
        app=ServerManager(None)
        app.mainloop()
        print 'manager done'

    elif args.p and args.o:
        print "manage server"
        manage_server(args.p, args.o.upper())
    elif False:
        print 'start server'
        app=ServerManager(None).mainloop()
    else:
        print "Unknown option", args
