import ctypes
import ctypes.wintypes
import socket
import sys, os
import os.path
import time

def serverReport(settings=None):

    def readConfig(f):
        import ConfigParser
        c=ConfigParser.SafeConfigParser()
        c.read(f)
        C=dict([(a,dict(c.items(a)) ) for a in c.sections()])
        # set up the first available ip address as the default address
        svr_defaults = {"bindto":socket.gethostbyname_ex(socket.gethostname())[2][0],
                        "port":'2240', "loglevel":"WARNING", "logfile":'IatscanServer.log',
                        "workingdir":os.path.abspath('../scanwork'),
                        "rootdir":os.path.abspath('.')
                        }
        if "SERVER" not in C:
            C["SERVER"]=svr_defaults
        else:
            for k in svr_defaults.keys():
                if k not in C["SERVER"]:
                    C["SERVER"][k]=svr_defaults[k]
        c=None
        return C

    if settings is None:
        inifile = open("scansvr.ini", "r")
        settings = readConfig(inifile)
    
    fa=open("Server Report.txt", 'w')
    fa.write("IATRISCAN INSTALLATION CONFIGURATION"+"\n")
    rdate=time.ctime(time.time()).split(" ")
    fa.write("RUN DATE: "+" ".join([rdate[x] for x in range(len(rdate)) if not x==3])+"\n")
    fa.write("RUN TIME: "+str(rdate[3])+"\n\n")
    
    fa.write("SERVER NAME: "+socket.gethostname() +"\n") 
#   If IsWindowsNT Then
#   fa.write("Server is Windows NT"+"\n")
#   Else
#      Report "Server is Win 98/95/ME"
#   End If

    fa.write("\nSHARED FOLDERS ON THIS SERVER"+"\n")
    fa.write("-".rjust(60,"-")+"\n")
    #FindShares
    fa.write("\nIP ADDRESSES ON THIS MACHINE:".ljust(30," ")+"\n   ".join(socket.gethostbyname_ex(socket.gethostname())[2])+"\n")
    fa.write("-".rjust(60,"-")+"\n\n")

    fa.write("DIRECTORY STRUCTURE IN IATRIC FOLDER"+"\n")
    fa.write("-".rjust(60,"-")+"\n")
      
    startPath = settings["SERVER"]["rootdir"]
    enumPaths(startPath)

    fa.write("\nSERVER CONFIGURATION DETAILS"+"\n")
    fa.write("-".rjust(60,"-")+"\n")
    fa.write("ScanServer installation dir: "+settings["SERVER"]["rootdir"]+"\n")
    fa.write("IP Port:                     "+settings["SERVER"]["port"]+"\n")
    fa.write("IP Address:                  "+settings["SERVER"]["bindto"]+"\n")
    fa.write("Working Directory:           "+settings["SERVER"]["workingdir"]+"\n")
    fa.write("Client Installation Folder   "+"\n") # & ClientSetupFolder
    fa.write("Client Software version      "+"\n") # & LTrim(Str(IatScanClientVer))
   
    if settings["SERVER"]["bindto"] == "":
        tkMessageMsgBox.warning("Iatric Server Report","Report is incomplete\nYou should start and configure the server before running the report.")
    return
    
#Private Declare Function LockFileEx Lib "kernel32" (ByVal hFile As Long, 
#ByVal dwFlags As Long, 
#ByVal dwReserved As Long, 
#ByVal nNumberOfBytesToLockLow As Long, 
#ByVal nNumberOfBytesToLockHigh As Long, 
#lpOverlapped As OVERLAPPED) As Long 
def enumPaths(s):
    """ To do """
    return
    
class OVERLAP_PTR(ctypes.wintypes.Structure):
    _fields_ = [("offset",ctypes.c_ulong),
                ("offsetHigh",ctypes.c_ulong),
                ("pointer",ctypes.c_void_p)]
    
class OVERLAPPED(ctypes.wintypes.Structure):
    _fields_ = [("internal", ctypes.c_ulong),
                ("internalHigh", ctypes.c_ulong),
                ("opointer",OVERLAP_PTR),
                ("hEvent",ctypes.c_void_p)]
                
def lockfile(a):
    _lockfile = ctypes.windll.kernel32.LockFileEx
    dwFlags = ctypes.c_ulong(1)
    dwReserved, nToLockLow = [ctypes.c_ulong() for x in range(2)]
    nLockHigh = ctypes.c_ulong(1)
    lpOverlap = OVERLAPPED 
    hFile=ctypes.c_ulong(open(a,'r').fileno())
    ret = _lockfile(hFile,dwargs,dwReserved,nToLockLow,nLockHigh,ctypes.byref(lpOverlap),hEvent)

    return
    
def unlockfile(a):
    return
    

    
if __name__ == '__main__':
    serverReport()