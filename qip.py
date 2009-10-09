#!/usr/bin/python

import sys, os, config, time

sys.path.append("%s/lib" % os.path.abspath(sys.path[0]))
from tunnelking.Log import Log

log = Log(config.logging, "qip.py")
log.log(3, "qip started for ip %s" % sys.argv[2])
log.log(3, "args %s" % sys.argv)

try:
	action, ip = sys.argv[1:3]
except:
	sys.exit(1)

if action == "add":
	s = 0
	while s==0:
		time.sleep(0.1)
		log.log(3, "iptables -D FORWARD -s %s -j ACCEPT" % ip)
		s = os.system("iptables -D FORWARD -s %s -j ACCEPT" % ip)
elif action == "delete":
	s = 0
	while s==0:
		time.sleep(0.1)
		log.log(3, "iptables -D FORWARD -s %s -j ACCEPT" % ip)
		s = os.system("iptables -D FORWARD -s %s -j ACCEPT" % ip)
	
	log.log(3, "iptables -A FORWARD -s %s -j ACCEPT" % ip)
	os.system("iptables -A FORWARD -s %s -j ACCEPT" % ip)