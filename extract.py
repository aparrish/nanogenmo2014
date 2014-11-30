import sys
import re
import random
import time

from pattern.en import parsetree, Word, conjugate, PAST, sentiment
from pattern.search import search

from elaborate import elaborate_on, ElaborationImpossible
from badwords import is_blacklisted

def phrase_replace(phrase):
	output = ["I", conjugate(phrase[0].lemma, tense=PAST)]
	for word in phrase[1:]:
		if word.string == 'you' and word.chunk.role == 'SBJ':
			output.append('I')
		elif word.string == 'you':
			output.append('me')
		elif word.string == 'her' and word.type == 'PRP$':
			output.append('my')
		elif word.string == 'her' and word.type == 'PRP':
			output.append('me')
		elif word.string in ('him', 'her') and word.chunk.role == 'OBJ':
			output.append('me')
		elif word.string in ('he', 'she') and word.chunk.role == 'SBJ':
			output.append('I')
		elif word.string == 'her':
			output.append('my')
		elif word.string == 'his':
			output.append('my')
		elif word.string == 'your':
			output.append('my')
		elif word.string in ('yourself', 'herself', 'himself'):
			output.append('myself')
		elif word.string in ('hers', 'yours'):
			output.append('mine')
		elif word.type in ('VBP', 'VBZ'):
			output.append(conjugate(word.string, tense=PAST))
		else:
			output.append(word.string)
	output_str = ' '.join(output)
	output_str = output_str.replace("caed n't", "couldn't")
	output_str = output_str.replace("thought me was", "thought I was")
	return output_str

def extract_verb_phrases(tree):
	verb_phrase_matches = search('to|you {VP}', tree)
	phrases = list()
	if len(verb_phrase_matches) > 0:
		possible_matches = list()
		for match in verb_phrase_matches:
			if match.group(1)[0].string == "dream":
				continue
			phrases.append(tree[match.group(1).start:])
	return phrases

def extract_verbs(tree):
	verb_matches = search('to|you {VB*}', tree)
	phrases = list()
	for match in verb_matches:
		if match.group(1)[0].type in ('VBG', 'VBZ'): continue
		if match.group(1)[0].string == "dream": continue
		phrases.append(tree[match.group(1).start:])
	return phrases

def extract_to_dream_that(tree):
	matches = search('to dream that she|he {VB*}', tree)
	phrases = list()
	for match in matches:
		phrases.append(tree[match.group(1).start:])
	return phrases

def extract_gerunds(tree):
	matches = search('to dream of {VBG}', tree)
	phrases = list()
	for match in matches:
		phrases.append(tree[match.group(1).start:])
	return phrases

phrase_scores = list()
para = ""
for line in sys.stdin:
	line = line.strip()
	if line != "":
		para += line + " "
	else:
		#print para
		#print parsetree(para)
		#print "------"
		#print para
		parts = re.split(r'\s*[,;]\s*', para)
		if len(parts) > 1 and not(parts[0].startswith('[')) and not('.' in parts[0]):
			action = parts[0]
			denotes = ' '.join(parts[1:])
			#action = re.sub(r"^to dream (that)?", "", action, count=0, flags=re.I)
			action = re.sub(r"in (your |a )?dreams?", "", action)
			action = re.sub(r"while dreaming", "", action)
			action = re.sub(r"\{[^}]*\}", "", action)
			#print action
			tree = parsetree(action, lemmata=True, relations=True)[0]
			#print tree
			verb_phrases = extract_verb_phrases(tree)
			#print "verb phrases: " + str(verb_phrases)
			verbs = extract_verbs(tree)
			#print "verbs: " + str(verbs)
			dream_thats = extract_to_dream_that(tree)
			#print "dream thats: " + str(dream_thats)
			gerunds = extract_gerunds(tree)
			#print "gerunds: " + str(gerunds)
			phrases = set()
			for phrase in verb_phrases + verbs + dream_thats + gerunds:
				phrases.add(phrase_replace(phrase) + ".")
			#print phrases
			for phrase in phrases:
				if not(is_blacklisted(phrase)):
					phrase_scores.append((phrase, int(sentiment(denotes)[0]*10), denotes))
		para = ""

print r"""\documentclass[12pt]{book}
\frenchspacing
\usepackage{makeidx}
\makeindex
\begin{document}
\title{\textit{I Waded In Clear Water}: Interpretations And Elaborations}
\author{Allison Parrish}
\date{November 2014}
\maketitle

\frontmatter
\maketitle

\pagestyle{empty}
%% copyrightpage
\begingroup
\footnotesize
\parindent 0pt
\parskip \baselineskip
\textcopyright{} 2014 Allison Parrish \\
All rights reserved.

This work is licensed with Creative Commons Attribution-ShareAlike 4.0
International. You are free to share (copy and redistribute the material in any
medium or format) and adapt (remix, transform, and build upon the material) for
any purpose, even commercially.

The licensor cannot revoke these freedoms as long as you follow the license
terms.

http://creativecommons.org/licenses/by-sa/4.0/

\endgroup
\clearpage

\chapter{Preface}

This novel was generated from the text of Gustavus Hindman Miller's "Ten
Thousand Dreams, Interpreted." The ``What's In A Dream'' section of Miller's
book functions as a dream dictionary: you look up a word, and find out what it
means to dream about that word's referent. there are multiple interpretations
for each word, and most of these interpretations can be broken down into what I
call an \textit{action} and a \textit{denotation}:

\begin{quote}
To see an oak full of acorns, denotes increase and promotion.
\end{quote}

In this entry, \textit{See an oak full of acorns} is the action, and
\textit{increase and promotion} is the denotation. The text of this novel was
made by extracting the actions and changing them to first-person, past-tense
sentences:

\begin{quote}
I saw an oak full of acorns.
\end{quote}

The denotation for each action is scored using a sentiment analysis algorithm,
and the sentences are printed in order by the sentiment of their corresponding
denotation, from most negative to most positive. (According to the sentiment
analysis algorithm, the first sentence, ``I saw a healthy belly,'' is the worst
thing that can happen in a dream; the last sentence, ``I waded in clear water,''
is the best thing.)

Elaborations, in the form of footnotes, are provided for many sentences. These
elaborations are generated using information in ConceptNet (in particular, the
IsA, HasProperty, and AtLocation relations) and WordNet (for part-of-speech
checks, synonyms, and antonyms).

\mainmatter

"""

current_sentiment = -10
current_chapter = 0
current_chapter_phrases = list()
real_elaborate = True
for phrase_tuple in sorted(phrase_scores, key=lambda x: x[1]) + [('', 11, '')]:
	if current_sentiment != phrase_tuple[1]:
		current_sentiment = phrase_tuple[1]
		current_chapter += 1
		sys.stderr.write('---> chapter %d\n' % current_chapter)
		print 
		print r"\chapter{}"
		print
		print ' '.join(current_chapter_phrases)
		current_chapter_phrases = list()
	sys.stderr.write(phrase_tuple[0] + "\n")
	parsed = parsetree(phrase_tuple[0], lemmata=True)
	if len(parsed) > 0:
		source = parsed[0]
		sentence = []
		footnotes = list()
		for word in source:
			if word.pos in ('NN', 'NNS') and word.string not in ('others',) \
					and random.randrange(5) > 0:
				try:
					if real_elaborate:
						sys.stderr.write("elaborating on " + word.lemma + "\n")
						footnote = elaborate_on(word.lemma)
					else:
						footnote = "Lorem ipsum dolor sit amet"
				except (IndexError, ElaborationImpossible, UnicodeEncodeError):
					sentence.append(word.string)
					continue
				if len(footnote) > 0 and not(is_blacklisted(footnote)):
					sentence.append(r"\index{%s}%s\footnote{%s}" % (word.lemma, word.string, footnote))
				else:
					sentence.append(r"\index{%s}%s" % (word.lemma, word.string))
			else:
				sentence.append(word.string)
		sentence_str = " ".join(sentence)
		sentence_str = sentence_str.replace(' .', '.')
		sentence_str = sentence_str.replace(" '", "'")
		current_chapter_phrases.append(sentence_str)
	else:
		current_chapter_phrases.append(phrase_tuple[0])
	if random.randrange(7) == 0:
		current_chapter_phrases.append("\n\n")

sys.stderr.write('end!')
print r"""
\backmatter
\printindex

\chapter{Attributions}

This work includes data from ConceptNet 5, which was compiled by the
Commonsense Computing Initiative. ConceptNet 5 is freely available under the
Creative Commons Attribution-ShareAlike license (CC BY SA 3.0) from
http://conceptnet5.media.mit.edu. The included data was created by contributors
to Commonsense Computing projects, contributors to Wikimedia projects, Games
with a Purpose, Princeton University's WordNet, DBPedia, OpenCyc, and Umbel.

WordNet Release 3.0 This software and database is being provided to you, the
LICENSEE, by Princeton University under the following license. By obtaining,
using and/or copying this software and database, you agree that you have read,
understood, and will comply with these terms and conditions.: Permission to
use, copy, modify and distribute this software and database and its
documentation for any purpose and without fee or royalty is hereby granted,
provided that you agree to comply with the following copyright notice and
statements, including the disclaimer, and that the same appear on ALL copies of
the software, database and documentation, including modifications that you make
for internal use or for distribution. WordNet 3.0 Copyright 2006 by Princeton
University. All rights reserved. THIS SOFTWARE AND DATABASE IS PROVIDED "AS IS"
AND PRINCETON UNIVERSITY MAKES NO REPRESENTATIONS OR WARRANTIES, EXPRESS OR
IMPLIED. BY WAY OF EXAMPLE, BUT NOT LIMITATION, PRINCETON UNIVERSITY MAKES NO
REPRESENTATIONS OR WARRANTIES OF MERCHANT- ABILITY OR FITNESS FOR ANY
PARTICULAR PURPOSE OR THAT THE USE OF THE LICENSED SOFTWARE, DATABASE OR
DOCUMENTATION WILL NOT INFRINGE ANY THIRD PARTY PATENTS, COPYRIGHTS, TRADEMARKS
OR OTHER RIGHTS. The name of Princeton University or Princeton may not be used
in advertising or publicity pertaining to distribution of the software and/or
database. Title to copyright in this software, database and any associated
documentation shall at all times remain with Princeton University and LICENSEE
agrees to preserve same.

\end{document}
"""
