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

Some analysis of declensions & strong/weak endings:

| Declension | % Strong Plural | Sample Size |
| ---------- | --------------- | ----------- |
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

