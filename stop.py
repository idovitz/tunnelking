#!/usr/bin/python

import os, sys, signal

try:
	sys.argv[1]
except:
	print "USAGE: stop.py [pid]"
	sys.exit()

si, so, se = child_stdin, child_stdout, child_stderr = os.popen3("pidof openvpn")

pids = so.read().strip().split(" ")

if sys.argv[1] in pids:
	os.kill(int(sys.argv[1]), signal.SIGTERM)