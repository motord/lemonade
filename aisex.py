# -*- coding: utf-8 -*-
# __author__ = 'peter'

from models import Lemon, Squeezed, Juice, Bottled, StaticContent
import scrapemark
import logging
from google.appengine.api import memcache
from mapreduce import operation as op
from google.appengine.api import urlfetch
from google.appengine.api import images
import urlparse

baseurl='http://bt.aisex.com/bt/'

def harvest():
    aisex=[baseurl+'thread.php?fid=4&search=&page=' + str(i) for i in range(5, 0, -1)]
    for url in aisex:
        lemons = scrapemark.scrape("""
        {*
        <td class=t_two align=left style="padding-left:8px">
         <a target=_blank href='{{ [lemons].url }}'>{{ [lemons].title }}</a>
        </td>
        *}
        """, url=url)['lemons']
        logging.info(url)
#        logging.info(lemons)
        for lemon in lemons:
            key=lemon['url']
            fruit=memcache.get('Squeezed::'+key)
            if fruit is None:
                fruit=memcache.get('Lemon::'+key)
                if fruit is None:
                    fruit=Squeezed.get_by_key_name(key)
                    if fruit is None:
                        fruit=Lemon.get_or_insert(baseurl+lemon['url'])
                        memcache.set('Lemon::'+key, fruit)
                    else:
                        memcache.set('Squeezed::'+key, fruit)

def squeeze_lemon_map(lemon):
    logging.info('squeezing '+lemon.key().name())
    squeezed=Squeezed.get_or_insert(lemon.key().name())
    memcache.set('Squeezed::'+squeezed.key().name().partition(baseurl)[2], squeezed)
    juices = scrapemark.scrape("""
        <span class='tpc_content'>
        {*
        <img src='{{ [juices].image }}' border=0>
        <a href='{{ [juices].download }}' target=_blank></a>
        *}
        </span>
        """, url=lemon.key().name())['juices']
    logging.info(juices)
    for juice in juices:
        juice=Juice(parent=squeezed, image=juice['image'], download=juice['download'])
        yield op.db.Put(juice)
    memcache.delete('Lemon::'+lemon.key().name().partition(baseurl)[2])
    yield op.db.Delete(lemon)

def bottle_juice_map(juice):
    logging.info('bottling '+juice.parent_key().name())
    image_url=juice.image
    image_url_components=urlparse.urlparse(image_url)
    image_url_netloc_path=image_url_components.netloc + image_url_components.path
    torrent_url=juice.download
    torrent_url_components=urlparse.urlparse(torrent_url)
    bottle=Bottled(parent=juice.parent(), image=image_url_netloc_path, download=torrent_url)
    try:
        result=urlfetch.fetch(image_url)
        if result.status_code==200:
            image_content=images.resize(result.content, width=300, output_encoding=images.JPEG)
            content=StaticContent(key_name=image_url_netloc_path, body=image_content, content_type='image/jpeg')
            yield op.db.Put(content)
            yield op.db.Put(bottle)
    except Exception, err:
        pass
    yield op.db.Delete(juice)
