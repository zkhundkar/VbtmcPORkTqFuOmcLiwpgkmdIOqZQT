from Tkinter import *
from docsvr import DocRequestHandler
import ttk
import tkMessageBox
import os, socket

class ServerManager(Tk):
    settings = {}

    def __init__(self, parent, cmdargs=[]):
        
        self.top = self
        Tk.__init__(self,parent)
        self.parent=parent
        self.configfile='scansvr.ini'
        self.settings=self.readSettings()
        self.initialize(cmdargs)

    def initialize(self, initargs):
        self.status = self.parent
        
        self.top.title('Server Manager')
        self.pid=os.getpid()

        for item in initargs:
            pass
        st=ttk.Style()
        st.theme_use('winnative')
        st.configure('.', font='verdana 12')
        if True:
            
            self.frame = ttk.Frame(self, borderwidth=1)
            self.frame.pack(fill=BOTH,expand=5)

            self.cfm = ttk.Frame(self.frame)
            self.yscrlbr = ttk.Scrollbar(self.cfm)
            self.yscrlbr.pack(side=RIGHT, fill=Y)
            self.xscrlbr = ttk.Scrollbar(self.cfm, orient=HORIZONTAL)
            self.xscrlbr.pack(side=BOTTOM, fill=X)
            self.tbox = Listbox(self.cfm,relief=GROOVE, height=10,width=60, yscrollcommand=self.yscrlbr, xscrollcommand=self.xscrlbr)
            #self.tbox.config(font=('verdana 10')
            self.yscrlbr.config(command=self.tbox.yview)
            self.xscrlbr.config(command=self.tbox.xview)
            self.tbox.pack(side=LEFT,fill=BOTH, expand=5)
            self.cfm.pack(fill=BOTH,expand=5)
            
        # display the menu
            self.menubar=Menu(self.top)
            self.setupMenu()
            self.top.config(menu=self.menubar)
            self.top.wm_resizable(width=200, height=120)

        #self.bind("<Escape>", self.destroy)            

        return  


    def writeTbox(self,s):
        self.tbox.insert(END,s)
        return
   

    def readSettings(self):
        import ConfigParser
        c=ConfigParser.SafeConfigParser()
        c.read(self.configfile)
        C=dict([(a,dict(c.items(a)) ) for a in c.sections()])
        # set up the first available ip address as the default address
        svr_defaults = {"bindto":socket.gethostbyname_ex(socket.gethostname())[2][0],
                        "port":'2240', "loglevel":"WARNING", "logfile":'Server.log',
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

    def saveSettings(self):
        cfg=open(self.configfile,'w')
        for section in self.settings.keys():
            cfg.write("[%s]\n" % section)
            for k in self.settings[section].keys():
                if k == "handler-class": pass
                else:
                    cfg.write("%s= %s\n" % (k.upper(),self.settings[section][k]) )
            cfg.write('\n')
        cfg.flush()
        cfg.close()

        

    def setupMenu(self):
        s = 'setupmenu'
#Create our Python menu
        self.connlist = Menu(self.menubar, tearoff=0)
        self.activeConnections = Menu(self.menubar, tearoff=0)
#Add our Menu to the Base Menu
        self.menubar.add_cascade(label="Server", menu=self.connlist)
#        self.menubar.add_cascade(label="Active", menu=self.activeConnections, state=DISABLED)
#        self.activeConnections.add_cascade(label="Refresh", command='self.checkActives')
#        self.activeConnections.add_cascade(label="Reload", command='self.reloadConnections')
#        self.activeConnections.add_separator()
        self.connlist.add_cascade(label="Start",command=self.startServer )
        self.connlist.add_cascade(label="Halt",command=self.stopServer )
        self.connlist.add_separator()
        self.connlist.add_command(label="Setup",command=self.setupServer)
        self.connlist.add_separator()
        self.connlist.add_command(label="Clear Manager Log",command=self.clearTbox )
        self.connlist.add_command(label="Version",command=self.getVersion )
        self.connlist.add_command(label="Statistics",command=self.getStats )
        self.connlist.add_command(label="Debug On",command=lambda x=True: self.setDebug(x) )
        self.connlist.add_command(label="Debug Off",command=lambda x=False: self.setDebug(x) )
        self.connlist.add_separator()
        self.connlist.add_command(label="Exit",command=self.destroy)
        
#        i=0
#        keyset=self.allConnections.keys()
#        keyset.sort()
#        for c in keyset:
#            self.connlist.add_command(label=c, command= lambda x=c: self.addConnection(x) )
#            i+=1
    def clearTbox(self):
        self.tbox.delete(0,END)

    def _checkServer(self):
        import subprocess as sp
        port = self.settings["SERVER"]["port"].strip()
        p=sp.Popen(["netstat","-ao"],stdout=sp.PIPE)
        s=p.communicate()
        ss=[x for x in s[0].split('\n') if port in x]
        if len(ss)>0:
            return "Server listening: %s" % '\n'.join(ss[0])

    
    def startServer(self):
        import subprocess as sp
        if self._checkServer():
            self.writeTbox("Server already listening on %s" % self.settings["SERVER"]["port"].strip())
            return
        pid=sp.Popen([os.path.join(self.settings["SERVER"]["pydir"],"python.exe"),
                      os.path.join(self.settings["SERVER"]["rootdir"],"docsvr.py"),
                      "-o server"])
        time.sleep(0.5)
        if pid.poll():
            tkMessageBox.showwarning("Start","Could not start server")
        else:
            self.writeTbox("Server running .. [%s]:%s " % (self.settings["SERVER"]["bindto"],
                                                         self.settings["SERVER"]["port"]))
        return
    
    def stopServer(self):
        s=socket.socket(socket.AF_INET,socket.SOCK_STREAM)
        try:
            svr=self.settings["SERVER"]["bindto"]
            s.connect((svr,int(self.settings["SERVER"]["port"])))
        except:
            tkMessageBox.showwarning("Stop Server","Could not connect")
            return
        try:
            ret = s.send("SHUTDOWN\x00")
            ret=s.recv(128)
            self.writeTbox("Server shutdown .. %s" %  ret.strip('\x00'))
            
        except:
            tkMessageBox.showwarning("Stop Server","Could not shutdown")
            return
            
        return

    def setDebug(self,state=False):
        s=socket.socket(socket.AF_INET,socket.SOCK_STREAM)
        try:
            svr=self.settings["SERVER"]["bindto"]
            s.connect((svr,int(self.settings["SERVER"]["port"])))
        except:
            tkMessageBox.showwarning("Stop Server","Could not connect")
            return
        try:
            ret=""
            if state:
                ret = s.send("SETDEBUGON\x00")
                ret=s.recv(128)
            else:
                ret = s.send("NODEBUG\x00")
                ret=s.recv(128)
            self.writeTbox("Debug .. " + ret.strip('\x00'))
            
        except:
            pass            
        return

    def getVersion(self):
        s=socket.socket(socket.AF_INET,socket.SOCK_STREAM)
        try:
            svr=self.settings["SERVER"]["bindto"]
            s.connect((svr,int(self.settings["SERVER"]["port"])))
        except:
            tkMessageBox.showwarning("Stop Server","Could not connect")
            return
        try:
            ret = s.send("VERSION\x00")
            ret=s.recv(128)
            self.writeTbox("Version .. " + ret.strip('\x00'))
            
        except:
            pass            
        return

    def getStats(self):
        s=socket.socket(socket.AF_INET,socket.SOCK_STREAM)
        try:
            svr=self.settings["SERVER"]["bindto"]
            s.connect((svr,int(self.settings["SERVER"]["port"])))
        except:
            tkMessageBox.showwarning("Stop Server","Could not connect")
            return
        try:
            ret = s.send("STATS\x00")
            ret=s.recv(128)
            self.writeTbox("Stats .. %s" % ret.strip('\x00'))
            
        except:
            tkMessageBox.showwarning("Get Stats","Could not get stats")
            return
            
        return
    def setupServer(self):
        ManagerSetup(self,"Server Settings")
        settings=self.settings["SERVER"]
        #tkMessageBox.showwarning("Setup Server","Not implemented")
        self.writeTbox("server %s: port %s" % (settings["bindto"],
                                               settings['port']))
        self.writeTbox("debug %s level %s" % (settings['debug'],
                                              settings['detaillogging']))
        return

class ManagerSetup(Toplevel):

    def __init__(self, parent, title=None):

        Toplevel.__init__(self, parent)
        self.transient(parent)

        if title:
            self.title(title)
        self.parent = parent
        self.settings = parent.settings
        ttk.Style().theme_use('alt')
        st=ttk.Style()
        st.theme_use('winnative')
        st.configure('.', font='verdana 11')
        
        body = ttk.Frame(self)
        self.initial_focus = self.body(body)
        body.pack(padx=5, pady=5)

        self.buttonbox()

        self.grab_set()

        if not self.initial_focus:
            self.initial_focus = self

        self.protocol("WM_DELETE_WINDOW", self.cancel)

        self.geometry("+%d+%d" % (parent.winfo_rootx()+50,
                                  parent.winfo_rooty()+50))

        self.initial_focus.focus_set()

        self.wait_window(self)

    #
    # construction hooks

    def body(self, master):
        # create dialog body.  return widget that should have
        # initial focus.  this method should be overridden
        
        ttk.Label(master, text="Address:").grid(row=0, sticky=E)
        ttk.Label(master, text="Port:").grid(row=1, sticky=E)
        ttk.Label(master, text="Status:").grid(row=2, sticky=E)
        #st.configure('TButton', font=('verdana',12))
        #st.configure('TEntry', font='verdana 10')
        
        s=socket.gethostbyname_ex(socket.gethostname())[2]
        s.extend(['127.0.0.1'])
        port='2240'
        ip=s[0]
        #s.reverse()
        self.debug=IntVar()
        self.debug.set(0)
        #ipaddrs.reverse()
        self.e1 = ttk.Combobox(master,values=tuple(s),width=20)
        self.e2 = ttk.Entry(master,width=22 )
        self.e3 = ttk.Entry(master,width=22, state=ACTIVE )
        self.e4 = ttk.Entry(master,width=30 )
        self.e2.delete(0,END)
#        self.e2.insert(0,'7500')
        self.e1.grid(row=0, column=1, sticky=EW)
        self.e2.grid(row=1, column=1, sticky=EW)
        self.e3.grid(row=2, column=1, sticky=EW)
        self.e4.grid(row=3, column=1, sticky=EW)
        debuglevels=['CRITICAL','ERROR','WARN','INFO','DEBUG','NONE']
        debuglevels.reverse()
        self.debuglevels=debuglevels
        self.cb = ttk.Checkbutton(master, text="Debug?", variable=self.debug, onvalue=True, offvalue=False)
        self.dbl = ttk.Combobox(master,values=tuple(debuglevels))
        if True:
            
            if self.settings["SERVER"]["bindto"].strip() in s:
                ip=self.settings["SERVER"]["bindto"].strip()
            else:
                ip=s[0]
            self.settings["SERVER"]["bindto"] = ip
            self.e1.set(ip)
            self.e2.insert(0,self.settings["SERVER"]["port"])
            csr= self.parent._checkServer()
            self.e3.config(state="active")
            if csr:
                self.e3.insert(0,"Server is running")
            else:
                print "check returned nothing"
                self.e3.delete(0)
            self.e3.config(state="disabled")
            self.e4.insert(0,self.settings["SERVER"]["workingdir"])
            lvl=0
            try:
                lvl=int(self.settings["SERVER"]["detaillogging"])
            except: pass
            if lvl in range(6): pass
            else: lvl=0
            self.dbl.set(debuglevels[lvl])
            if lvl>0:
                self.debug.set(1)
            else: self.debug.set(0)
#        except: pass
        
        self.cb.grid(row=5, column=0, sticky=W)
        self.dbl.grid(row=5, column=1)


        pass

    def buttonbox(self):
        # add standard button box. override if you don't want the
        # standard buttons

        box = ttk.Frame(self)

        w = ttk.Button(box, text="OK", width=10, command=self.ok, default=ACTIVE)
        w.pack(side=LEFT, padx=5, pady=5)
        w = ttk.Button(box, text="Cancel", width=10, command=self.cancel)
        w.pack(side=LEFT, padx=5, pady=5)

        self.bind("<Return>", self.ok)
        self.bind("<Escape>", self.cancel)
        box.pack()

    #
    # standard button semantics

    def ok(self, event=None):

        if not self.validate():
            self.initial_focus.focus_set() # put focus back
            return

        self.withdraw()
        self.update_idletasks()

        self.apply()

        self.cancel()

    def cancel(self, event=None):

        # put focus back to the parent window
        self.parent.focus_set()
        
        self.destroy()

    def validate(self):
        return 1 # override

    def apply(self):
        self.settings["SERVER"]['bindto']=self.e1.get()
        self.settings["SERVER"]['port']= self.e2.get()
        #self.settings["SERVER"]['port']= self.e2.get()
        self.settings["SERVER"]['workingdir']=self.e4.get()
        self.settings["SERVER"]['detaillogging']=0
        try:
            self.settings["SERVER"]['detaillogging']=self.debuglevels.index(self.dbl.get())
        except: pass
        self.parent.saveSettings()

        pass # override

if __name__ == '__main__':
	app=ServerManager(None).mainloop()
	app = None
