from docsvr import DocReqCmd

class doPUT(DocReqCmd):
    """ Handler for PUT command
        Expected format of command/args
        PUT <srcfile> <tgtfile>chr(0) -> <srcfile> should exist in a reachable folder,
                                        typically the working directory
            In case of a failure, should the server delete the src file or does the client do the cleanup

        PUT STREAM <tgtfile> <size>chr(0)<bytestream>
            S
    """
    def processCommand(self):
        if not self.target:
            self.request.send_error(400,"ERROR: TARGET PATH NOT FOUND")
            return
        wdir=self.working
        if self.path=="STREAM":
            try:
                if self.filesize>99999999:
                    self.request.send_error(400,"ERROR|SIZE OF STREAMED FILE EXCEEDS 100MB")
                    return
            except TypeError:
                self.request.send_error(400,"Invalid size of bytestream in PUT STREAM ("+str(self.filesize)+")")
                return
            tmpfile=self.server.generateoid(wdir)
            s=os.path.join(wdir,tmpfile)
            bytes_recv=nbytes=len(self.datastream)
            fa=open(s,'wb')
            if nbytes>0:
                fa.write(self.datastream)
            # this will block until self.filesize bytes have been read from the socket
            # we may need to set up a "time out" for this
            # If there weren't enough bytes read, do we just trash what was received?
            fa.write(self.request.rfile.read(self.filesize-nbytes))
            fa.flush()
            fa.close()
        s= self.translatePath(self.path)
        if not self.validatePFN(s) == 2:
            self.request.send_error(400,"ERROR| SOURCE FILE NOT FOUND")
            return
        elif os.path.getsize(s)<128:
            self.request.send_error(400,"ERROR| SOURCE FILE < 100 bytes (may be corrupt)")
            return
            
        t=self.translatePath(self.target)
        t_status=self.validatePFN(t)
        if t_status == 1:
            # Normal - target file doesn't exist, but path does
            self.filecopy(s,t,"True")
        elif t_status == 2:
            # Delete existing target file
            self.filedelete(t)
            self.filecopy(s,t,"True")
        elif t_status == 0:
            try:
                os.makedirs(os.path.dirname(t))
                self.filecopy(s,t,"True")
                
            except:
                # could not create target directory
                self.request.send_error(400,"ERROR: TARGET PATH ("+str(t)+") COULD NOT BE CREATED" )
                # may be delete source file if it is in the working directory
                return
        else:
            self.request.send_error(400,"ERROR| UNKNOWN CONDITION (%d %s)" % (t_status,t))
            return
        #verify that the file was correctly copied over    
        if self.validatePFN(t) == 2:
            self.request.send_ok("OK")
        else:
            self.request.send_error(400,"ERROR|COULD NOT VERIFY PUT")
        return
            
    def cleanup(self):
        """ TO DO - clean up source file in working directory """
        return
            
