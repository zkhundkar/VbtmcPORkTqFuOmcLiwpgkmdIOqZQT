from docsvr import DocReqCmd

class doFILEVERIFY(DocReqCmdCmd):

    def processCommand(self):
        src=self.translatePath(self.path)
        r=["BAD DIR","NOT EXISTS","EXISTS","BAD CALL"]
        try:
            r=r[self.validatePFN(src)]
        except:
            r="BAD CALL"
        self.request.send_ok("OK|%s" % r)
        
        return

class doVERIFY(DocReqCmd):

    def processCommand(self):
        src=self.translatePath(self.path)


        if self.validatePFN(src) == 2:
			# non-standard response, but client will hang if this is not just "OK"


            self.request.send_ok("OK")
        else:
            self.request.send_error(400,"ERROR: SOURCE FILE NOT FOUND")

        return
