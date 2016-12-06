from docsvr import DocReqCmd

class doFOLDERNAMES(DocReqCmd):
    """       'Command format - "FOLDERNAMES ROOTFOLDERNAME"
            'ROOTFOLDERNAME can use UNC or local path
    """
    def processCommand(self):
        if not self.path:
            self.request.send_error(400,"ERROR| NO ROOTFOLDER GIVEN")
            return

        s=self.translatePath(self.path)
        if not os.path.isdir(s):
            self.request.send_error(400,"ERROR| FOLDER NOT FOUND")
            return
        dd=os.walk(s).next()[1]
        self.request.send_ok("OK|FOLDERNAMES|"+"*".join(dd))
    
        return


