from io import BytesIO

from flask import Flask
from flask import send_file

from requests_html import HTMLSession

import requests

from PIL import Image, ImageDraw, ImageFont

import textwrap
import re
import sys
import atexit

from apscheduler.schedulers.background import BackgroundScheduler

app = Flask(__name__)

def wikiquote():
    session = HTMLSession()
    
    r_pic = session.get('https://commons.wikimedia.org/wiki/Commons:Picture_of_the_day?action=render')

    wikipic = 'https:' + r_pic.html.find('table > tbody > tr > td.toccolours > a', first=True).attrs['href']
    print(wikipic, file=sys.stdout)

    r_pic_true = session.get(wikipic).html.find('div.fullImageLink > a', first=True).attrs['href']
    print(r_pic_true, file=sys.stdout)

    response = requests.get(r_pic_true)
    img_pic = Image.open(BytesIO(response.content)).convert('RGBA')
    img_pic = img_pic.resize((1920, 1920 * img_pic.height / img_pic.width))

    r_quote = session.get('https://en.wikiquote.org/wiki/Wikiquote:Quote_of_the_day?action=render')

    fnt_sz = min(img_pic.width, img_pic.height) // 60 - img_pic.width // 16 - img_pic.height // 16
    fnt = ImageFont.truetype('Montserrat-Regular.ttf', fnt_sz)

    wikitext = r_quote.html.find('div > center > table', first=True).text
    wikitext = wikitext.splitlines()
    wikitext = '\n\n'.join('\n'.join(textwrap.wrap(text, width=60)) for text in wikitext)
    print(wikitext, file=sys.stdout)
    img_text = Image.new('RGBA', (img_pic.size), color=(0, 0, 0, 64))
    d = ImageDraw.Draw(img_text, mode='RGBA')
    margin = img_pic.size[0] // 16
    offset = img_pic.size[1] // 16
    d.text((margin, offset), wikitext, font=fnt, fill='white')
    
    wikipic_caption = r_pic.html.find('table > tbody > tr > td > div.description', first=True).text
    wikipic_caption = wikipic_caption.splitlines()
    wikipic_caption = '\n\n'.join('\n'.join(textwrap.wrap(text, width=60)) for text in wikipic_caption)
    print(wikipic_caption, file=sys.stdout)
    margin = img_pic.size[0] // 16
    offset = (img_pic.size[1] // 16) * 12
    d.text((margin, offset), wikipic_caption, font=fnt, fill='white')
    
    out = Image.blend(img_pic, img_text, 0.5)

    out.save('qpotd.png', format='PNG')
    print('Image cached successfully.', file=sys.stdout)

scheduler = BackgroundScheduler()
scheduler.add_job(func=wikiquote, trigger="interval", minutes=60)
scheduler.start()

wikiquote()
    
@app.route('/wikiquote-of-the-day')
def image_render():
    resp = send_file('qpotd.png', mimetype='image/png')
    resp.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate'
    return resp

@app.errorhandler(500)
def server_error(e):
    print('An error occurred during a request.', file=sys.stderr)
    return 'An internal error occurred.', 500

# Shut down the scheduler when exiting the app
atexit.register(lambda: scheduler.shutdown())
