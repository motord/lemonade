#!/usr/bin/env python
#
# Copyright 2007 Google Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#
from google.appengine.ext import webapp, db
from google.appengine.ext.webapp import util
from bottle import debug, Bottle, request, response, template
from google.appengine.api import memcache
from models import Bottled, Squeezed, StaticContent, Juice
import logging
import bottle

bottle.TEMPLATE_PATH.insert(0, './templates/')

debug(True)
app=Bottle()

@app.get('/test')
def test():
    juice=Juice(key_name='test', image='http://pics.dmm.co.jp/mono/movie/1dandy044/1dandy044pl.jpg', download='http://www.jandown.com/link.php?ref=CUWjjPJP0q')
    juice.put()

def page_filter(config):
    regexp = r'[234].json'

    def to_python(match):
        return int(match[0])

    def to_url(number):
        return str(number)+'.json'

    return regexp, to_python, to_url

app.router.add_filter('page', page_filter)

@app.get('/<page:page>')
def scroll(page):
    path=str(page)+'.json'
    json=memcache.get(path)
    if json is None:
        json=StaticContent.get_by_key_name(path)
        if json is None:
            bottles=Bottle.gql("ORDER BY created DESC LIMIT 25 OFFSET :1", page*25-24)
            json=StaticContent(key_name=path, body=str(template('page.json', bottles=bottles)), content_type='application/json')
            json.put()
        memcache.set(path, json, 1800)
    response.content_type=json.content_type
    return json.body

@app.get('/<path:path>')
def get_content(path):
    if path=='':
        path='index.html'
    memcache.delete(path)
    content=memcache.get(path)
    if content is None:
        content=StaticContent.get_by_key_name(path)
        if content is None:
            if path=='index.html':
                bottles=Bottled.gql("ORDER BY created DESC LIMIT 25")
                content=StaticContent(key_name=path, body=str(template('index.html', bottles=bottles)), content_type='text/html')
                content.put()
                memcache.set(path, content, 1800)
                response.content_type=content.content_type
                return content.body
        else:
            memcache.set(path, content, 1800)
    response.content_type=content.content_type
    return content.body


def main():
    util.run_wsgi_app(app)


if __name__ == '__main__':
    main()
