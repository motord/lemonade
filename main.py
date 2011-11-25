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
from bottle import debug, Bottle, request, response, template, HeaderDict
from google.appengine.api import memcache
from models import Bottled, Squeezed, StaticContent, Juice
import logging
import bottle
import datetime

bottle.TEMPLATE_PATH.insert(0, './templates/')

debug(True)
app=Bottle()

@app.get('/test')
def test():
    juice=Juice(key_name='test', image='http://pics.dmm.co.jp/mono/movie/1dandy044/1dandy044pl.jpg', download='http://www.jandown.com/link.php?ref=CUWjjPJP0q')
    juice.put()

def page_filter(config):
    regexp = r'[234].html'

    def to_python(match):
        return int(match[0])

    def to_url(number):
        return str(number)+'.html'

    return regexp, to_python, to_url

app.router.add_filter('page', page_filter)

@app.get('/<page:page>')
def scroll(page):
    path=str(page)+'.html'
    content=memcache.get(path)
    if content is None:
        content=StaticContent.get_by_key_name(path)
        if content is None:
            bottles=Bottled.gql("ORDER BY created DESC LIMIT 25 OFFSET " + str(page*25-24))
            content=StaticContent(key_name=path, body=str(template('page.html', bottles=bottles)), content_type='text/html')
            content.put()
        memcache.set(path, content, 43200)

    return _output(content)

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
            else:
                return
        memcache.set(path, content, 43200)

    return _output(content)

HTTP_DATE_FMT = "%a, %d %b %Y %H:%M:%S GMT"

def _output(content):
    """Output the content in the datastore as a HTTP Response"""
    serve = True
    # check modifications and etag
    if 'If-Modified-Since' in request.headers:
        last_seen = datetime.datetime.strptime(
            request.headers['If-Modified-Since'], HTTP_DATE_FMT)
        if last_seen >= content.modified.replace(microsecond=0):
            serve = False
    if 'If-None-Match' in request.headers:
        etags = [x.strip('" ')
                 for x in request.headers['If-None-Match'].split(',')]
        if content.etag in etags:
            serve = False

    headers = {}
    if content.content_type:
        headers['Content-Type'] = content.content_type
    last_modified = content.modified.strftime(HTTP_DATE_FMT)
    headers['Last-Modified'] = last_modified
    headers['ETag']= '"%s"' % (content.etag,)
    for header in content.headers:
        key, value = header.split(':', 1)
        headers[key] = value.strip()
    if serve:
        response.body = content.body
        for key, value in headers.iteritems():
            response.set_header(key, value)
        response.content_type=content.content_type
        response.status=int(content.status)
    else:
        response.status=304
    return response

def main():
    util.run_wsgi_app(app)


if __name__ == '__main__':
    main()
