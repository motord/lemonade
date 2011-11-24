# -*- coding: utf-8 -*-
# __author__ = 'peter'

from google.appengine.ext import deferred
import aisex
from mapreduce import base_handler, mapreduce_pipeline
from bottle import debug, Bottle
from google.appengine.ext.webapp import util
import logging

debug(True)
app=Bottle()

#@cron_only
@app.get('/bots/harvest')
def harvest():
    deferred.defer(aisex.harvest)

class JuiceBottlePipeline(base_handler.PipelineBase):

  def run(self):
    output = yield mapreduce_pipeline.MapperPipeline(
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
