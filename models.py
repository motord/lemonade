# -*- coding: utf-8 -*-
# models

from google.appengine.ext import db
import aetycoon
import hashlib

# Create your models here.
class Squeezed(db.Model):
    created=db.DateTimeProperty(auto_now_add=True)
    lemons=db.StringListProperty()

class Juice(db.Model):
    image=db.LinkProperty()
    download=db.LinkProperty()
    created=db.DateTimeProperty(auto_now_add=True)

class Bottled(db.Model):
    image=db.StringProperty()
    download=db.StringProperty()
    created=db.DateTimeProperty(auto_now_add=True)

class StaticContent(db.Model):
    body = db.BlobProperty()
    content_type = db.StringProperty(required=True)
    status = db.IntegerProperty(required=True, default=200)
    etag = aetycoon.DerivedProperty(lambda x: hashlib.sha1(x.body).hexdigest())
    headers = db.StringListProperty()
    created=db.DateTimeProperty(auto_now_add=True)
    modified=db.DateTimeProperty(auto_now=True)


