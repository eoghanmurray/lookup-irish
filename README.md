# irish-lookup

Scrapes teanglann.ie and focloir.ie and extracts a good English translation for an Irish word combining both websites.

Can be used from the command line:

<pre>$ ./lookup_irish.py glór

<span style="background-color:#C4A000"><font color="#2E3436">glór</font></span> foclóir: {&apos;singing voice&apos;, &apos;sound&apos;, &apos;music&apos;, &apos;tone&apos;, &apos;speaking voice&apos;, &apos;voice&apos;, &apos;call&apos;}

<span style="background-color:#CC0000">glór</span> Noun nm1
<font color="#4E9A06">voice</font> [glór 1 , masculine ( genitive singular -óir, plural glórtha ). <font color="#C4A000"> voice. </font>]
1. <font color="#75507B">(human) </font><font color="#4E9A06">voice</font> [<font color="#C4A000"> human voice. </font>
    glór an duine, glór daonna, human voice.
    labhairt de ghlór ard, íseal, to speak in a loud, low, voice.
    d’aithin mé do ghlór, i recognized your voice.
    bhí tocht ina ghlór, his voice was broken (with emotion)]
2. [<font color="#C4A000"> speech, utterance. </font>
    aird a thabhairt ar ghlór duine, to heed the voice of s.o.
    glór díomhaoin, amaideach, idle, foolish, talk.
    éisteacht le glórtha ban, to listen to women’s talk.
    glórtha seanbhan, old wives’ tales.
    glór gan aird, heedless talk(er).
    glór i gcóitín, (i) childish talk, prattle, (ii) prattler.
    glór mór ar bheagán cúise, a lot of fuss about nothing]
3. <font color="#4E9A06">sound</font> [<font color="#C4A000"> sound, noise. </font>
    glór na habhann, na gaoithe, na báistí, the sound of the river, of the wind, of the rain.
    glór trumpaí, the voice of trumpets.
    glór caointe, sound of crying; whinging sound.
    tá glór i mo chluasa, there is a murmuring in my ears.
    glór bodhar, toll, dull, hollow, sound]
4. <font color="#4E9A06">voice (linguistics)</font> [linguistics : <font color="#C4A000"> voice. </font>
    gan ghlór, voiceless]

<span style="background-color:#CC0000">glór</span>  None
[glór 2 = gleoir]

Noun nm1
voice
(human) voice
sound
voice (linguistics)
</pre>


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