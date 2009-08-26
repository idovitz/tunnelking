##################################################
# projectname: tunnelking
# Copyright (C) 2009  IJSSELLAND ZIEKENHUIS
###################################################

import syslog

class Log:
    def __init__(self, loglevel, name):
        syslog.openlog('[TUNNELKING] %s' % name)
        self.loglevel = int(loglevel)
    
    def log(self, msglevel, msg):
        if msglevel <= self.loglevel:
            syslog.syslog(msg)
