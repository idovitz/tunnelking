#!/usr/bin/python

from ncrypt import *

dhparams = dh.DH()
dhparams.generateParameters(1024, 2)

f = open("ssl/dh1024.pem", "w")
f.write(dhparams.toPEM_Parameters())
f.close()