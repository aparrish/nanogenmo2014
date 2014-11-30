# Copyright (c) 2013 Darius Kazemi
# 
# Permission is hereby granted, free of charge, to any person
# obtaining a copy of this software and associated documentation
# files (the "Software"), to deal in the Software without
# restriction, including without limitation the rights to use,
# copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the
# Software is furnished to do so, subject to the following
# conditions:
# 
# The above copyright notice and this permission notice shall be
# included in all copies or substantial portions of the Software.
# 
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND,
# EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES
# OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND
# NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT
# HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY,
# WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING
# FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR
# OTHER DEALINGS IN THE SOFTWARE.

badwords = [
	"skank",
	"wetback",
	"bitch",
	"cunt",
	"dick",
	"douchebag",
	"dyke",
	"fag",
	"nigga",
	"nigger",
	"negro",
	"tranny",
	"trannies",
	"paki",
	"pussy",
	"retard",
	"slut",
	"titt",
	"tits",
	"wop",
	"whore",
	"chink",
	"fatass",
	"shemale",
	"daygo",
	"dego",
	"dago",
	"gook",
	"kike",
	"kraut",
	"spic",
	"twat",
	"lesbo",
	"homo",
	"fatso",
	"lardass",
	"jap",
	"biatch",
	"paki",
	"tard",
	"gimp",
	"gyp",
	"chinaman",
	"chinamen",
	"golliwog",
	"crip",
	"rape",
	"raping",
	"molest",
	"abuse",
	"abusing",
	"abusive",
	"child"
]

def is_blacklisted(s):
	for word in badwords:
		if word in s.lower():
			return True
	return False

if __name__ == '__main__':
	import sys
	for line in sys.stdin:
		line = line.strip()
		if not is_blacklisted(line):
			print line

