#Hello There

I'm [Allison](http://www.decontextualize.com).

This is the repository for my [NaNoGenMo 2014](https://github.com/dariusk/NaNoGenMo-2014/)
entry, *I Waded In Clear Water* ([pdf](http://aparrish.github.io/nanogenmo2014/final.pdf)).

##The procedure

(Taken from the Preface)

This novel was generated from the text of Gustavus Hindman Miller's *Ten
Thousand Dreams, Interpreted*. The "What's In A Dream" section of Miller's book
functions as a dream dictionary: you look up a word, and find out what it means
to dream about that word's referent. Each word has multiple interpretations,
and most of these interpretations can be broken down into what I call an
*action* and a *denotation*:

	To see an oak full of acorns, denotes increase and promotion.

In this entry, `See an oak full of acorns` is the action, and
`increase and promotion` is the denotation. The text of this novel was
made by extracting the actions and changing them to first-person, past-tense
sentences:

	I saw an oak full of acorns.

The denotation for each action is scored using a sentiment analysis algorithm,
and the sentences are printed in order by the sentiment of their corresponding
denotation, from most negative to most positive. (According to the sentiment
analysis algorithm, the first sentence of the novel, "I saw a healthy belly,"
is the worst thing that can happen in a dream; the last sentence, "I waded in
clear water," is the best thing.)

Elaborations, in the form of footnotes, are provided for many sentences. These
elaborations are generated using information in
[ConceptNet](http://conceptnet5.media.mit.edu/) (in particular, the `IsA`,
`HasProperty`, and `AtLocation` relations) and
[WordNet](http://wordnet.princeton.edu/) (for part-of-speech checks, synonyms,
and antonyms).

##This repository

This repository contains the Python code I wrote to generate my NaNoGenMo 2014
entry. It's very rough and hacky but I wanted to make it available to any
curious onlookers.

Usage:

	$ pip install -r requirements.txt
	$ python extract.py <dreams.txt >draft.tex

This generates a LaTeX file, which you can render with the LaTeX tools of
your choice! (I used [TeXShop](http://pages.uoregon.edu/koch/texshop/).)

The file `final.tex` contains my final output as submitted to NaNoGenMo, and
`final.pdf` is the rendered PDF.

##License

The text of the novel is made available under a [Creative Commons
Attribution-ShareAlike 4.0
International](http://creativecommons.org/licenses/by-sa/4.0/) license.

The source code is distributed under an MIT license. See LICENSE for details.

