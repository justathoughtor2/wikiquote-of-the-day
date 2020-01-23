import logging

from io import BytesIO

from flask import Flask
from flask import send_file

from requests_html import HTMLSession

from PIL import Image, ImageDraw, ImageFont

import re

app = Flask(__name__)

@app.route('/')
def hello():
    session = HTMLSession()
    r = session.get('https://en.wikiquote.org/wiki/Wikiquote:Quote_of_the_day?action=render')
    wikitext = re.sub('(.{70,80} )', '\\1\n', r.html.find('div > center > table', first=True).text, flags=re.DOTALL)
    height = 30 + 30 * wikitext.count('\n') if wikitext.count('\n') > 1 else 90
    logging.info(wikitext)
    img = Image.new('RGB', (800,height), color='white')
    fnt = ImageFont.truetype('Montserrat-Regular.ttf', 14)
    d = ImageDraw.Draw(img)
    d.multiline_text((10,10), wikitext, font=fnt, fill='black', spacing=6)
    output = BytesIO()
    img.save(output, format='PNG')
    output.seek(0)
    resp = send_file(output, mimetype='image/png')
    resp.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate'
    return resp

@app.errorhandler(500)
def server_error(e):
    logging.exception('An error occurred during a request.')
    return 'An internal error occurred.', 500