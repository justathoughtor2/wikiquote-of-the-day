from io import BytesIO

from flask import Flask
from flask import send_file

from requests_html import HTMLSession

from PIL import Image, ImageDraw, ImageFont

import textwrap

import re

import sys

app = Flask(__name__)

@app.route('/')
def wikiquote():
    session = HTMLSession()
    r = session.get('https://en.wikiquote.org/wiki/Wikiquote:Quote_of_the_day?action=render')
    wikitext = r.html.find('div > center > table', first=True).text
    wikitext = wikitext.splitlines()
    wikitext = '\n\n'.join('\n'.join(textwrap.wrap(text, width=110)) for text in wikitext)
    height = 20 + 20 * wikitext.count('\n') if wikitext.count('\n') > 1 else 60
    print(wikitext, file=sys.stdout)
    img = Image.new('RGB', (800,height), color='white')
    fnt = ImageFont.truetype('Montserrat-Regular.ttf', 14)
    d = ImageDraw.Draw(img)
    margin = offset = 10
    d.text((margin, offset), wikitext, font=fnt, fill='black')
    output = BytesIO()
    img.save(output, format='PNG')
    output.seek(0)
    resp = send_file(output, mimetype='image/png')
    resp.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate'
    return resp

@app.errorhandler(500)
def server_error(e):
    print('An error occurred during a request.', file=sys.stderr)
    return 'An internal error occurred.', 500