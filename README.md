# irish-lookup

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


Requirements & Installation
---

Python 3: https://www.python.org/

run the following from the command line:

    pip3 install virtualenv
    virtualenv .virtual
    source .virtual/bin/activate

Then you can lookup a word:

     ./lookup_irish.py rith


There is also a script `populate_google_sheet.py` which is used as part of an Anki deck: https://ankiweb.net/shared/info/1975966926