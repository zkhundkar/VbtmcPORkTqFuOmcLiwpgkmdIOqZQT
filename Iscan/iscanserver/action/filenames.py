from docsvr import DocReqCmd

class doFILENAMES(DocReqCmd):
    """
            'Command format - "FILENAMES FOLDERNAME MASK COUNT"
            'FOLDERNAME and file mask in standard windows format, e.g., \\MYMACHINE\INB\*.tif
            'FOLDERNAME can use UNC or local path
            'Determine drive letter
            
            strDriveLetter = strUnQuoteString(pa$(2))
            
            If pa$(0) = 3 Then 'Number of files to return is specified
                intFilenameCounter = CInt(pa$(3))
    """
    def processCommand(self):
        s=self.translatePath(self.path)
        if not s:
            self.request.send_error(400,"ERROR|FOLDERNAME MISSING")
            return
        elif not os.path.isdir(os.path.dirname(s)):
            self.request.send_error(400,"ERROR|FOLDER IS NOT A VALID FOLDER (%s)" % os.path.dirname(s))
            return
        mask=self.target
        if "*" in mask: pass
        else:
            self.request.send_error(400,"ERROR|INVALID FILE SEARCH MASK (%s)" % mask)
        # Get the next set of files
        cnt=10
        try:
            cnt=int(self.filesize)
        except TypeError:
            pass
        if os.path.isdir(s):
            s=os.path.join(s,mask)
        l = self.getSetOfFiles(s,cnt)
        #print "<filenames>",len(l),l
        self.request.send_ok("OK|FILENAMES|"+"*".join(l))
        return

    def getSetOfFiles(self,path,count):
        #from ctypes.wintypes import WIN32_FIND_DATAW as WIN32_FIND_DATA
        _FindFirstFile = ctypes.windll.kernel32.FindFirstFileW
        _FindNextFile = ctypes.windll.kernel32.FindNextFileW
        _FindClose = ctypes.windll.kernel32.FindClose
        _GetLastError = ctypes.windll.kernel32.GetLastError
        wfd = WIN32_FIND_DATA()

        mask = unicode(path, sys.getfilesystemencoding())
        sHndl = _FindFirstFile(mask, ctypes.byref(wfd))
        filelist=[]
        
        if sHndl != -1:
            newfile=str(wfd.cFileName)
            fnd=0
            if newfile == '.' or newfile == '..': pass
            else:
                filelist.append(newfile)
                fnd+=1            
            while fnd<count and _FindNextFile(sHndl, ctypes.byref(wfd)):
                newfile=str(wfd.cFileName)
                if newfile == '.' or newfile == '..': pass
                else:
                    filelist.append(newfile)
                    fnd+=1
            _FindClose(sHndl)
        return filelist
