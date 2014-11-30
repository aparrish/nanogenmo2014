import json
import sys
import urllib
import random
import time

import requests
import requests_cache

from pattern.en import wordnet, NOUN, VERB, ADJECTIVE, ADVERB
from pattern.en import referenced, INDEFINITE
from jinja2 import Template

cn_baseurl = 'http://conceptnet5.media.mit.edu/data/5.2/'

nn_killfile = [u'organisation', u'album', u'single', u'television show',
	u'film', u'band', 'song', 'video game', 'software', 'other', 'there']

requests_cache.install_cache('elaborate_cache')

cached_requests = 0
fresh_requests = 0
backoff = 1.0

def canonical(query):
	# sort query params in canonical order. requests_cache probably does this
	# on its own, but I was experiencing weirdnesses while developing so I
	# made this just to be sure
	components = list()
	for key in sorted(query.keys()):
		components.append("%s=%s" % (key, urllib.quote_plus(str(query[key]))))
	return '&'.join(components)

def cn_search_get_text(query, lemma):
	global cached_requests, fresh_requests, backoff
	url = cn_baseurl + 'search?' + canonical(query)
	while True:
		resp = requests.get(url)
		obj = resp.json()
		text = list()
		if resp.status_code == 429:
			sys.stderr.write("received 429, backing off: %0.2f\n" % backoff)
			time.sleep(backoff)
			backoff = backoff * 1.5
			continue
		break
	if 'edges' not in obj:
		sys.stderr.write(str(resp.status_code) + " " + str(obj) + "\n")
		raise KeyError
	for edge in obj['edges']:
		text.extend([t for t in edge['text'] if len(t) > 0 and t != lemma and t not in nn_killfile])
	if resp.from_cache:
		sys.stderr.write(resp.url + ' is from cache\n')
		cached_requests += 1
	else:
		sys.stderr.write("!!! " + resp.url + ' not cached, sleeping (%d, %d)\n' % (cached_requests, fresh_requests))
		time.sleep(1)
		fresh_requests += 1
	return text

def underscore(s):
	return s.replace(' ', '_')

def cn_start_isa(lemma):
	query = {'start': '/c/en/' + underscore(lemma), 'rel': '/r/IsA',
			'filter': 'core', 'limit': 10}
	return cn_search_get_text(query, lemma)

def cn_end_isa(lemma):
	query = {'end': '/c/en/' + underscore(lemma), 'rel': '/r/IsA',
			'filter': 'core', 'limit': 10}
	return cn_search_get_text(query, lemma)

def cn_start_has_property(lemma):
	query = {'start': '/c/en/' + underscore(lemma), 'rel': '/r/HasProperty',
			'filter': 'core', 'limit': 10}
	return cn_search_get_text(query, lemma)

def cn_start_at_location(lemma):
	query = {'start': '/c/en/' + underscore(lemma), 'rel': '/r/AtLocation',
			'filter': 'core', 'limit': 10}
	return cn_search_get_text(query, lemma)

def cn_end_at_location(lemma):
	query = {'end': '/c/en/' + underscore(lemma), 'rel': '/r/AtLocation',
			'filter': 'core', 'limit': 10}
	return cn_search_get_text(query, lemma)

def wn_filter_pos(text, pos):
	synsets = wordnet.synsets(text, pos=pos)
	for s in synsets:
		for synonym in s.synonyms:
			if synonym[0].isupper():
				return False
	if len(synsets) > 0:
		return True

class ElaborationImpossible(Exception): pass

class Elaboration(object):
	def __init__(self, text, further):
		self.text = text
		self.further = further

def is_animate(lemma):
	# this "works" but is very eager to grant animacy even for words that have
	# one synset with a person hypernym (things like "rock" count as "animate"
	# because a "rock" can be a person that you depend on)
	hypernyms = list()
	for synset in wordnet.synsets(lemma, pos=NOUN):
		# skip synsets that are proper nouns, as these are always animate!
		if any([s[0].isupper() for s in synset.synonyms]):
			continue
		synonyms = list()
		for s in synset.hypernyms(recursive=True):
			synonyms.extend(s.synonyms)
		if 'person' in synonyms:
			return True
	return False

def synonyms(lemma, pos=NOUN):
	synonyms = list()
	for synset in wordnet.synsets(lemma, pos):
		for synonym in synset.synonyms:
			if synonym != lemma:
				synonyms.append(synonym)
	return synonyms

def antonyms(lemma, pos=NOUN):
	antonyms = list()
	for synset in wordnet.synsets(lemma, pos):
		if synset.antonym is not None:
			antonyms.extend(synset.antonym.synonyms)
	return antonyms

def indef(lemma):
	if lemma in ('someone', 'something'): return lemma
	return referenced(lemma, article=INDEFINITE)

def subj_pronoun(lemma):
	if is_animate(lemma): return "they"
	else: return "it"

def obj_pronoun(lemma):
	if is_animate(lemma): return "them"
	else: return "it"

def copula(lemma):
	if is_animate(lemma): return "were"
	else: return "was"

def ucfirst(s):
	return s[0].upper() + s[1:]

def render(tmpl, **args):
	return Template(tmpl).render(
			subj_pronoun=subj_pronoun, copula=copula, indef=indef, ucfirst=ucfirst,
			choice=random.choice, obj_pronoun=obj_pronoun, synonyms=synonyms,
			antonyms=antonyms, ADJECTIVE=ADJECTIVE, **args)


def elaborate_on_start_isa(lemma):
	"""Check to for things that lemma is (i.e., hypernyms). Then grab a
	property of that."""
	nns = filter(lambda x: wn_filter_pos(x, NOUN), cn_start_isa(lemma))
	if len(nns) == 0:
		raise ElaborationImpossible
	adjs = list()
	for nn in nns[:2]:
		adjs.extend(filter(lambda x: wn_filter_pos(x, ADJECTIVE), cn_start_has_property(nn)))
	if len(adjs) == 0:
		raise ElaborationImpossible
	patterns = [
			"{{adj}}",
			"LEMMA-SUBJ LEMMA-COPULA{{choice([' not', ''])}} {{adj}}",
			"LEMMA-SUBJ {{choice(['seemed', 'appeared'])}} {{adj}}",
			"LEMMA-SUBJ did not {{choice(['seem', 'appear'])}} {{adj}}",
			"you said that LEMMA-SUBJ LEMMA-COPULA{{choice([' not', ''])}} {{adj}}",
			"LEMMA-SUBJ LEMMA-COPULA {{adj}} but not {{choice(synonyms(adj,pos=ADJECTIVE))}}"
			]
	adj = random.choice(adjs)
	if len(antonyms(adj, pos=ADJECTIVE)) > 0:
		patterns.append(
			"LEMMA-SUBJ LEMMA-COPULA both {{adj}} and {{choice(antonyms(adj,pos=ADJECTIVE))}}")
	if len(synonyms(adj, pos=ADJECTIVE)) > 0:
		patterns.append(
			"LEMMA-SUBJ LEMMA-COPULA {{adj}} and {{choice(synonyms(adj,pos=ADJECTIVE))}}")
	return Elaboration(
			render(random.choice(patterns), adj=adj, lemma=lemma),
			{'adj': adj})

def elaborate_on_end_isa(lemma):
	"""Check for things that are lemma (i.e., hyponyms)"""
	nns = filter(lambda x: wn_filter_pos(x, NOUN), cn_end_isa(lemma))
	if len(nns) == 0:
		raise ElaborationImpossible
	patterns = [
			"LEMMA-SUBJ LEMMA-COPULA{{choice([' not', ''])}} {{indef(nn)}}",
			"{{indef(nn)}}",
			"you said LEMMA-SUBJ LEMMA-COPULA{{choice([' not', ''])}} {{indef(nn)}}",
	]
	nn = random.choice(nns)
	if len(synonyms(nn)) > 0:
		patterns.append(
			"LEMMA-SUBJ LEMMA-COPULA {{indef(nn)}} but not {{indef(choice(synonyms(nn)))}}")
	return Elaboration(
			render(random.choice(patterns), nn=nn, lemma=lemma),
			{'nn': nn})

def elaborate_on_start_has_property(lemma):
	adjs = filter(lambda x: wn_filter_pos(x, ADJECTIVE),
			cn_start_has_property(lemma))
	if len(adjs) == 0:
		raise ElaborationImpossible
	patterns = [
			"{{adj}}",
			"LEMMA-SUBJ LEMMA-COPULA {{adj}}",
			"LEMMA-SUBJ {{choice(['looked', 'seemed', 'appeared'])}} {{adj}}",
			"you told me LEMMA-SUBJ LEMMA-COPULA {{adj}}",
			]
	adj = random.choice(adjs)
	if len(antonyms(adj, pos=ADJECTIVE)) > 0:
		patterns.extend([
			"LEMMA-SUBJ {{choice(['looked', 'seemed', 'appeared'])}} {{adj}} and {{choice(antonyms(adj, pos=ADJECTIVE))}}",
			"you told me LEMMA-SUBJ LEMMA-COPULA {{choice(antonyms(adj,pos=ADJECTIVE))}}"
			])
	return Elaboration(
			render(random.choice(patterns), adj=adj, lemma=lemma),
			{'adj': adj})

def elaborate_on_start_at_location(lemma):
	"""lemma->at_location->something, i.e., 'nn is in lemma'"""
	# either I'm getting this wrong, or some of the entries on conceptnet are
	# getting it wrong
	nns = filter(lambda x: wn_filter_pos(x, NOUN), cn_start_at_location(lemma))
	if len(nns) == 0:
		raise ElaborationImpossible
	patterns = [
			"LEMMA-SUBJ LEMMA-COPULA in {{indef(nn)}}",
			"{{choice(['we', 'I', 'you'])}} {{choice(['found', 'saw'])}} LEMMA-OBJ in {{indef(nn)}}",
			"LEMMA-SUBJ LEMMA-COPULA {{choice(['found', 'seen', 'discovered'])}} in {{indef(nn)}}"
			]
	nn = random.choice(nns)
	return Elaboration(
			render(random.choice(patterns), nn=nn, lemma=lemma),
			{'nn': nn})

def elaborate_on_end_at_location(lemma):
	"""something->at_location->lemma, i.e. 'lemma is in nn'"""
	# either I'm getting this wrong, or some of the entries on conceptnet are
	# getting it wrong
	nns = filter(lambda x: wn_filter_pos(x, NOUN), cn_end_at_location(lemma))
	if len(nns) == 0:
		raise ElaborationImpossible
	patterns = [
			"{{indef(nn)}} was{{choice([' not', ''])}} in LEMMA-OBJ",
			"{{indef(nn)}} was within LEMMA-OBJ",
			"{{choice(['we', 'I', 'you'])}} found {{indef(nn)}} in LEMMA-OBJ",
			"{{choice(['we', 'I', 'you'])}} found {{indef(nn)}} {{choice(['within', 'there'])}}"
	]
	nn = random.choice(nns)
	return Elaboration(
			render(random.choice(patterns), nn=nn, lemma=lemma),
			{'nn': nn})

def random_conjoin(strs):
	out = list()
	i = 0
	while i < len(strs)-1:
		if (len(strs[i].split()) >= 3 and len(strs[i+1].split()) >= 3) \
				and random.randrange(2) == 0:
			out.append(', and '.join([strs[i], strs[i+1]]))
			i += 2
		else:
			out.append(strs[i])
			i += 1
	if i < len(strs):
		out.append(strs[-1])
	return [ucfirst(s) + "." for s in out]

def parenthesized(strs):
	out = list()
	if len(strs) <= 1: return strs
	count = 0
	for i, s in enumerate(strs):
		if i > 0 and random.randrange(5) == 0 and count == 0:
			out.append("(" + s + ")")
			count += 1
		else:
			out.append(s)
	return out
	

def elaborate_on(lemma):
	elaborations = [
			elaborate_on_start_isa,
			elaborate_on_end_isa,
			elaborate_on_start_has_property,
			elaborate_on_start_at_location,
			elaborate_on_end_at_location]
	to_elaborate = lemma.decode('utf8')
	elaboration_strs = []
	repeat_lemma = True
	random.shuffle(elaborations)
	for elab_func in elaborations:
		try:
			elab = elab_func(to_elaborate)
		except ElaborationImpossible:
			continue
		# hack cohesion things. this is really primitive but it does the job and
		# sometimes makes the text pleasantly weird
		elab_text = ""
		if repeat_lemma:
			article = random.choice(['the', 'my', 'your', 'our', 'this'])
			elab_text = elab.text.replace('LEMMA-SUBJ', article + ' ' + to_elaborate)
			elab_text = elab_text.replace('LEMMA-COPULA', 'was')
			elab_text = elab_text.replace('LEMMA-OBJ', article + ' ' + to_elaborate)
			repeat_lemma = False
		else:
			elab_text = elab.text.replace('LEMMA-SUBJ', subj_pronoun(to_elaborate))
			elab_text = elab_text.replace('LEMMA-COPULA', copula(to_elaborate))
			elab_text = elab_text.replace('LEMMA-OBJ', obj_pronoun(to_elaborate))
		elaboration_strs.append(elab_text)
		if 'nn' in elab.further and random.randrange(2) == 0:
			to_elaborate = elab.further['nn']
			repeat_lemma = True
	conjoined = random_conjoin(elaboration_strs)
	parens = parenthesized(conjoined)
	return ' '.join(parens)

if __name__ == '__main__':
	from pprint import pprint
	print elaborate_on(sys.argv[1])

