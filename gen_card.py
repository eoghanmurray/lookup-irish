#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from teanglann import get_teanglann_definition
import argparse
import pystache

parser = argparse.ArgumentParser(
    description="Lookup English definitions of Irish words from the wonderful "
    "https://www.teanglann.ie/ and https://www.focloir.ie/")

arg = parser.add_argument
arg(
    '-v', '--verbose',
    help='List of matching words from foclóir '
    'and full definition from teanglann',
    action='store_true')
arg(
    'irish-word',
    help="Irish word to look up")

if __name__ == '__main__':
    args = vars(parser.parse_args())
    if args:
        GA = args['irish-word']
        PoS, EN, Gender = get_teanglann_definition(GA, verbose=args['verbose'])
        renderer = pystache.Renderer()
        front = renderer.render_path('anki-cards/front-template.html', {
            'GA': GA,
        })
        # back includes front
        back = renderer.render_path('anki-cards/back-template.html', {
            'GA': GA,
            'EN': EN,
            'Part of Speech': PoS,
            'Gender': Gender,
            'FrontSide': '[FrontSide]'
        })
        # probably Pystache can do the foll. (raw html) but hacking it for now
        entire = back.replace('[FrontSide]', front)
        page = '<html>'
        page += '<head>'
        page += f'<title>{GA} - preview of Anki flashcard</title>'
        page += f'<link type="text/css" src="style.css" />'
        page += '</head>'
        page += '<body>'
        page += entire
        page += '</body>'
        page += '</html>'
        with open(f'anki-cards/{GA}.html', 'w') as f:
            f.write(page)
