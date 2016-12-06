from docsvr import DocReqCmd

class doSIZE(DocReqCmd):
    def processCommand(self):
        import ctypes
        a,btotal,bfree=[ctypes.c_ulonglong() for x in range(3)]
        fun=ctypes.windll.kernel32.GetDiskFreeSpaceExA
        if sys.version_info >= (3,):
            fun=ctypes.windll.kernel32.GetDiskFreeSpaceExW
        r=fun('c:',ctypes.byref(a), ctypes.byref(b), ctypes.byref(c))
        pc_free=float(bfree.value*100)/float(btotal.value)
        gb_free=float(bfree.value)/(2**30)
        return

