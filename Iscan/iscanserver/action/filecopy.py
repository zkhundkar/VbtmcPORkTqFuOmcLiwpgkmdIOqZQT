from docsvr import DocReqCmd

class doFILECOPY(DocReqCmd):
    def processCommand(self):
        src = self.translatePath(self.path)
        tgt = self.translatePath(self.target)
        if len(src)==0:
            self.request.send_error(400, "ERROR|SOURCE FILE PARAMETER MISSING")
            return
            
        if len(tgt)==0:
            self.request.send_error(400,"ERROR|TARGET FILE PARAMETER MISSING")
            return
            
        if self.validatePFN(src) == 2:
            if self.command == "FILEMOVE" :
                if self.filecopy(src,tgt,True):
                    self.request.send_ok("OK|FILE MOVED")
                else:
                    self.request.send_error(405,"ERROR|FILE COULD NOT BE RENAMED")
            elif self.filecopy(src,tgt):
                self.request.send_ok("OK|FILE COPIED" )
            else:
                self.request.send_error(405,"ERROR|FILE COULD NOT BE COPIED")
                
        else:
            self.request.send_error(400,"ERROR|SOURCE DOESN'T EXIST")
        return

