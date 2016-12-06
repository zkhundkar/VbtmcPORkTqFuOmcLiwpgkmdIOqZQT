from docsvr import DocReqCmd
class doFILEDELETE(DocReqCmdCmd):
    def processCommand(self):
        src=self.translatePath(self.path)
        
        if self.validatePFN(src) == 2:
            if self.filedelete(src):
                self.request.send_ok("OK|FILE DELETED")
            else:
                self.request.send_error(400,"ERROR|DELETE FAILED OR NOT PERMITTED")
        else:
            self.request.send_error(400,"ERROR|FILE NOT FOUND")
        return

        """

                """
