__gamename__ = "scramble"
__helptext__ = "A trivia scramble game.\n!play scramble [max word len (default 10)] [num words (default 10)]"
__players__ = 1

#Copyright (c) 2010 Thomas Watson

#Permission is hereby granted, free of charge, to any person obtaining a copy
#of this software and associated documentation files (the "Software"), to deal
#in the Software without restriction, including without limitation the rights
#to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
#copies of the Software, and to permit persons to whom the Software is
#furnished to do so, subject to the following conditions:

#The above copyright notice and this permission notice shall be included in
#all copies or substantial portions of the Software.

#THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
#IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
#FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
#AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
#LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
#OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
#THE SOFTWARE.

import os.path
import random

print "[scramble] Loading wordlist..."
wordlist = []
numwords = 0
loaded = False
try:
	f = open(os.path.dirname(__file__)+"/scramble_wordlist.txt")
		
	for x in f.xreadlines():
		wordlist.append(x)
		numwords += 1
		
	loaded = True
	print "[scramble] Wordlist loaded successfully!"
except:
	print "[scramble] Wordlist could not be loaded!"

class Scramble:
	def __init__(self, irc, options):
		pass
	def join(self, user):
		pass
	def start(self):
		pass
	def stop(self):
		pass
	def handlecmd(self, cmd, args, user, nick):
		pass
		
def start(irc, options):
	return Scramble(irc, options)
	
def disp_stats(irc, userdata):
	irc.send("Total words unscrambled: "+str(userdata[0]))