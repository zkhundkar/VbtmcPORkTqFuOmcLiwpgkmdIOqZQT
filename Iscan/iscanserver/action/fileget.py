from docsvr import DocReqCmd
class doGET(DocReqCmd):
    """ Implements GET, GET-LOCK, WEBGET and WEBGET-LOCK commands
        Only the GET function has been implemented so far"""

    def processCommand(self):
        fpn = self.translatePath(self.path)
        t=None
        try:
            t = self.translatePath(self.target)
            if t[-1] == '\\':
                t= t[:-1]
            self.starget=self.target.strip()
        except :
            pass
        tempfile = ""
        tempfileName=""
		isLocked = ""
		stdtif=False
        if not self.validatePFN(fpn):
            # not exists
            self.request.send_error(400, "ERROR|INVALID SOURCE FILE NAME (%s)" % self.path)
            return
        elif self.target is None:
            # Invalid option - scanwork folder or STREAM not specified
            self.request.send_error(403,"ERROR: BAD WORKING PATH")
            return
        else:
            #standard - write file out to scanwork folder
            #SocketTracking(Val(lblConnectionNum.Caption)).SocketFile = pa(3)
            stdtif=sefl.command.startswith("WEBGET") or fpn.split('.')[-1].upper()=="IIF"
            self.request.logger.debug("%s", str((fpn, self.target)))
            if self.target == "STREAM":
                wdir=self.server.working
                self.request.logger.debug("%s", str((fpn, self.target, wdir)))
                if len(wdir):
                    tempfile = self.server.generateOID(wdir)
                    self.request.logger.debug("%s", str((wdir,tempfile)))
                    #should this include the extension?
                    tempfileName=tempfile.split("\\")[-1]
                
            elif os.path.isdir(t): # target path is a valid directory
                tempfile = self.server.generateOID(t)
                #should this include the extension?
                tempfileName=tempfile.split("\\")[-1]

            else:
                self.request.send_error(404,"ERROR: BAD TARGET PATH "+t)
                return
            isLocked = ""
            if self.check_locks() == "LOCKED" :
			# check_locks will set a lock if possible for the GET-LOCK command
				isLocked="-LOCKED"
                #self.request.send_ok("OK-LOCKED\t"+tempfileName)
                #return
            if self.target=="STREAM":
                # apparently when a file is streamed, it is converted into tiff before streaming
                # file should be locked at this point so we can send the correct one
                filelen = os.path.getsize(fpn)
                self.request.send_ok("OK"+isLocked+"\t"+str(filelen))
                fa=open(fpn,'rb')
                # Maybe convert to standard tif header
                stdTif=False
                if fpn.split('.')[-1].upper() == 'IIF':
                    stdTif = True

				if stdtif:
                    f12=fa.read(12)
                    if f12[6:].startswith("*II"):
                        self.request.wfile.write(f12[6:]+f12[:6])
                    else:
                        self.request.wfile.write(f12)
                    f12=None
                else: pass
                #self.send_response(200,fa.read(),"")
                self.request.wfile.write(fa.read())
                self.request.wfile.flush()
                self.request.close_connection = 1
                self.request.send_ok("\x00OK\t\x00\x00")
                fa.close()
                return
            #print "GET",fpn,tempfile
            self.filecopy(fpn, tempfile)
            #ReturnToLibrary = tempfile
            if not self.validatePFN(tempfile):
                self.request.send_error(405,"ERROR:COULD NOT CREATE TARGET tempfile "+tempfile)
                self.release_lock()
                return
            else:
                self.request.send_ok("OK"+isLocked+"\t"+tempfileName)

        return
