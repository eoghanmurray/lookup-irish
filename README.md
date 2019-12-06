# lookup_irish.py

Scrapes teanglann.ie and focloir.ie and extracts a good English translation for an Irish word combining both websites.

Used from the command line:

<pre>$ ./lookup_irish.py glór

Noun nm1
voice
(human) voice
sound
voice (linguistics)
</pre>

There's a verbose mode also, that prints more info:

![color screenshot of output of './lookup_irish.py -v glór'](verbose.png?raw=true)


Features
---

Makes a cache of all webpages downloaded for faster re-lookup

[irish_lang.py](irish_lang.py) has some handy functions for mutating words (lenite/eclipse), applying articles according to gender and part-of-speech rules ('fuinneog' -> 'an fhuinneog'), and applying HTML hints for masculine/feminine (for use in e.g. flashcards).

Requirements & Installation
---

Python 3: https://www.python.org/

run the following from the command line:

    pip3 install virtualenv
    virtualenv .virtual
    source .virtual/bin/activate
    pip3 install -r requirements.txt

Then you can lookup a word:

     ./lookup_irish.py rith


Anki Deck
---

This project was originally started as a means to automatically provide translations for a top-6,500 Irish words Anki deck available at https://ankiweb.net/shared/info/1975966926

![example showing a noun and a verb](sample-noun-verb.png?raw=true)

The deck is designed to enable learning of plurals and genitive cases of nouns at the same time as the noun, and also to learn the verbal noun form alongside the root of verbs.

Definitions have been provided manually for the first 1,000 words, and then subsequently automatically using this project for the subsequent 5,000, with the first 1,000 being cross checked with the automated translations.  The deck has been further improved with manual notes and additions of common 2/3 word idioms and phrasal verbs (bigrams/trigrams).

The `populate_google_sheet.py` script can be used to update this deck, but appropriate credentials are needed, i.e. access to the <a href="https://docs.google.com/spreadsheets/d/1kiZlZp8weyILstvtL0PfIQkQGzuG7oZfP8n_qkMFAWo">working spreadsheet</a>. Get in contact if that is needed.

The deck is originally based on  the <a href="https://github.com/michmech/irish-word-frequency">Irish Word Frequency List</a> from Michal Boleslav Měchura. There appear to be some biases towards legal terminology in that word list, and these words have been manually demoted where noticed.  Supplemental data is from the <a href="https://www.gaois.ie/en/">Gaois corpus</a>, used to proportionally demote cards for verbal nouns (these are also shown in the root verb card as in 'ag tarraingt' above) and discover candidate bigrams, and some missing word forms were taken from the fantastic top-500 Liostaí Bhreacadh lists published and available for purchase at <a href="http://breacadh.ie/">breacadh.ie</a>.


Typical Masculine/Feminine Endings
---

![example showing cards with 'cht' endings in both feminine and masculine forms](ending-highlighting.png?raw=true)

Some of the typical masculine/feminine endings are colored blue/pink to reinforce the gender of nouns, and where these endings are 'false friends', the are instead marked with a red underline.  'éisteacht' above is indeed feminine, whereas 'ucht' is masculine.

Analysis of selected word endings which are typically masculine or feminine

| Feminine Ending | Feminine | Sample | %Feminine| Masculine Exceptions | Notes |
| ---------- |            ---: |        ---: | ---------- | -------- |-------- |
|-cht | 302 | 332 | 91% | <i>socheolaíocht</i>, <i>bunreacht</i>, <i>comhlacht</i>, <i>complacht</i>, <i>gnólacht</i>, <i>leanacht</i>, <i>líofacht</i>, <i>fanacht</i> <br> other 35 or so masculine exceptions are all the short, one syllable words e.g. <i>sliocht</i>, <i>seacht</i>, <i>fuacht</i>, <i>lucht</i>, <i>locht</i>, <i>acht</i>, <i>ocht</i> etc.
|-áil | 86 | 86 | 100%
|-is | 72 | 72 | 100%
|-óg | 46 | 47 | 98% | <i>dallamullóg</i>
|-int | 32 | 33 | 97% | <i>sáirsint</i>
|-irt | 29 | 29 | 100%
|-eog | 17 | 17 | 100% |  |all nf2 |
|-ail | 15 | 17 | 88% | <i>Earcail</i>, <i>Uncail</i>
|-lann | 14 | 16 | 89% |  <i>salann</i>, <i>anlann</i>
|-ís | 11| 12 | 91% | <i>giúistís</i>
|-íl | 10 | 10 | 100%
|-ailt | 7 | 7 | 100%  |  | all nf2 |
|-úil | 6 | 6 | 100%
| (total feminine) | 1621 | 1621 | 100%

| Masculine Ending | Masculine | Sample |  %Masculine |Feminine Exceptions | Notes |
| ---------- |            ---: |        ---: | ---------- | -------- |-------- |
|-án | 195 | 195 | 100%
|-adh | 103 | 103 | 100%
|-óir | 81 | 88 | 92% | <i>cóir</i>, <i>tóir</i>, <i>onóir</i>, <i>éagóir</i>, <i>altóir</i>, <i>glóir</i>, <i>seanmóir</i> | professions
|-ín | 72 | 80 | 90% | <i>ealaín</i>, <i>muinín</i>, <i>mín</i>, <i>aintín</i>, <i>cín</i>, <i>braillín</i>, <i>vacsaín</i> | diminutive
|-oir | 62 | 69 | 90% | <i>cathaoir</i> <br> other exceptions are short <i>treoir</i>, <i>deoir</i>, <i>coir</i>, <i>aoir</i>, <i>beoir</i>
|-ire | 52 | 65 | 80% | <i>Éire</i>, <i>aire</i>, <i>saoire</i>, <i>náire</i>, <i>trócaire</i>, <i>faire</i>, <i>mire</i>, <i>géire</i>, <i>pónaire</i>, <i>úire</i>, <i>allmhaire</i>, <i>onnmhaire</i>, <i>fuaire</i>
|-ún | 31 | 31 | 100%
|-éad| 28 | 29 | 97% | <i>téad</i>
|-úr | 28 | 30 | 93% | <i>deirfiúr</i>, <i>siúr</i>
|-éal | 26 | 26 | 100%
|-ste | 24 | 28 | 86% | <i>aiste</i>, <i>timpiste</i>, <i>tubaiste</i>, <i>biaiste</i>
|-éir | 18 | 24 | 75% | <i>mistéir</i>, <i>comhréir</i> <br> other exceptions are short: <i>réir</i>, <i>spéir</i>, <i>cléir</i>, <i>céir</i> | professions
|-úir | 4 | 5 | 80% | <i>úir</i> | professions
|-aeir | 1 | 1 | 100% | | only 1: carraeir
| (total masculine) |  2805 | 2805 | 100%

Adjective Agreement
---
How adjectives agree with the preceeding noun is shown by providing sample masculine/feminine & plural nouns, when there is a difference in the agreement:

![example showing an adjective agreeing with a preceeding noun](adjective-agreement.png?raw=true)


Strong Plurals
---
Strong endings for plural nouns are those highlighted in bold; these are endings that don't change in the genitive plural.
Some adjectives agree differently with the preceeding noun if that noun has a strong ending:
e.g. <a href="https://www.teanglann.ie/en/gram/_n_a?n=deoch_fem&a=daor_adj1">ag cheannach na ndeochanna daora</a> (buying the expensive drinks) vs. <a href="https://www.teanglann.ie/en/gram/_n_a?n=bronntanas_masc1&a=daor_adj1">ag cheannach na mbronntanas daor</a> (buying the expensive presents)


Some analysis of noun declensions & strong/weak endings:

| Declension | % Strong Plural | Sample Size |
| ---------- |            ---: |        ---: |
| nm1        |  10%            | 1480        |
| nf2        |  53%            | 806         |
| nf3        |  30%            | 464         |
| nm3        |  79%            | 306         |
| nm4        |  84%            | 764         |
| nf4        |  65%            | 211         |
| nf5        |  74%            | 50          |
| nm2(!)     |  100%           | 2           |
| nm5(!)     |  100%           | 5           |
| nf (other) |  22%            | 139         |
| nm (other) |  23%            | 331         |

