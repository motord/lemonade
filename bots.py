# -*- coding: utf-8 -*-
# __author__ = 'peter'

from google.appengine.ext import deferred, db
import aisex
from mapreduce import base_handler, mapreduce_pipeline
from bottle import debug, Bottle
from google.appengine.ext.webapp import util
from google.appengine.api import memcache
from models import StaticContent
import logging

debug(True)
app=Bottle()

#@cron_only
@app.get('/bots/harvest')
def harvest():
    deferred.defer(aisex.harvest)

@app.get('/bots/done')
def regenerate():
    logging.info('regenerating site')
    contents=['index.html','2.json','3.json','4.json']
    memcache.delete_multi(contents)
    try:
        db.delete(StaticContent.get_by_key_name(contents))
    except Exception, err:
            pass

class LemonPipeline(mapreduce_pipeline.MapperPipeline):
    def get_callback_url(self):
        return '/bots/done'

class JuiceBottlePipeline(base_handler.PipelineBase):

  def run(self):
    output = yield LemonPipeline(
        "bottle_juice",
        "aisex.bottle_juice_map",
        "mapreduce.input_readers.DatastoreInputReader",
        params={
            "entity_kind": "models.Juice", "batch_size": 4
        },
        shards=4)

#@cron_only
@app.get('/bots/bottle')
def bottle():
    pipeline = JuiceBottlePipeline()
    pipeline.start()

def main():
    util.run_wsgi_app(app)


if __name__ == '__main__':
    main()
