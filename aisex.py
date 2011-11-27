# -*- coding: utf-8 -*-
# __author__ = 'peter'

from models import Squeezed, Juice, Bottled, StaticContent
import scrapemark
import logging
from google.appengine.api import memcache
from mapreduce import operation as op
from google.appengine.api import urlfetch
from google.appengine.api import images
import urlparse
from google.appengine.ext import deferred
import mechanize
import re

baseurl='http://bt.aisex.com/bt/'

def harvest():
    aisex=[baseurl+'thread.php?fid=5&search=&page=' + str(i) for i in range(5, 0, -1)]
    lemons=[]
    fresh=[]
    for url in aisex:
        lemons.extend(scrapemark.scrape("""
        {*
        <td class=t_two align=left style="padding-left:8px">
         <a target=_blank href='{{ [lemons].url }}'>{{ [lemons].title }}</a>
        </td>
        *}
        """, url=url)['lemons'])
        logging.info(url)
    squeezed=memcache.get('Squeezed::lemons')
    if squeezed is None:
        squeezed=Squeezed.get_by_key_name('squeezed')
        if squeezed is None:
            fresh=[baseurl+lemon['url'] for lemon in lemons]
    else:
        fresh=[baseurl+lemon['url'] for lemon in lemons if lemon['url'] not in squeezed.lemons]
    bucket=[]
    for lemon in fresh:
        logging.info('squeezing '+lemon)
        juices = scrapemark.scrape("""
            <span class='tpc_content'>
            {*
            <img src='{{ [juices].image }}' border=0>
            <a href='{{ [juices].download }}' target=_blank></a>
            *}
            </span>
            """, url=lemon)['juices']
        logging.info(juices)
        for juice in juices:
            juice=Juice(key_name=lemon, image=juice['image'], download=juice['download'])
            juice.put()
        bucket.append(lemon)
    if squeezed is None:
        squeezed=Squeezed(key_name='squeezed', lemons=bucket)
    else:
        squeezed.lemons.extend(bucket)
    squeezed.put()
    memcache.set('Squeezed::lemons', squeezed)

def download_torrent(url):
    br=mechanize.Browser()
    br.open(url)
    br.select_form(nr=0)
    response=br.submit()
    return response.get_data()

def bottle_juice_map(juice):
    logging.info('bottling '+juice.key().name())
    image_url=juice.image
    image_url_components=urlparse.urlparse(image_url)
    image_url_netloc_path=image_url_components.netloc + image_url_components.path
    torrent_url=juice.download
    torrent_url_components=urlparse.urlparse(torrent_url)
    torrent_url_query=torrent_url_components.query
    match=re.search('ref=(.*)', torrent_url_query)
    if match is None:
        pass
    else:
        torrent_file=str(match.groups(0)[0])+'.torrent'
        bottle=Bottled(key_name=juice.key().name(), image=image_url_netloc_path, download=torrent_file)
        try:
            result=urlfetch.fetch(image_url)
            if result.status_code==200:
                image_content=images.resize(result.content, width=300, output_encoding=images.JPEG)
                content=StaticContent(key_name=image_url_netloc_path, body=image_content, content_type='image/jpeg')
                yield op.db.Put(content)
                torrent=download_torrent(torrent_url)
                content=StaticContent(key_name=torrent_file, body=torrent, content_type='application/x-bittorrent')
                yield op.db.Put(content)
                yield op.db.Put(bottle)
        except Exception, err:
            pass
        yield op.db.Delete(juice)
