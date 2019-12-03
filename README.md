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


There is also a script `populate_google_sheet.py` which is used as part of an Anki deck: https://ankiweb.net/shared/info/1975966926

---

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

---


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

