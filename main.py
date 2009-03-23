#!/usr/bin/env python

import wsgiref.handlers
import random

from google.appengine.ext import webapp, db
from google.appengine.api import memcache
from google.appengine.ext.webapp import template

class Comic(db.Model):
    name        = db.StringProperty()
    id          = db.StringProperty()
    author      = db.StringProperty()
    title       = db.StringProperty()
    content     = db.BlobProperty()
    date        = db.DateTimeProperty(auto_now_add=True)

def Count():
  return Comic.gql("").count()

def GetComicByName(name):
  data = memcache.get("comic_name"+str(name))
  if data is not None:
    return data
  else:
    result = Comic.gql("WHERE name = :1 LIMIT 1", name).fetch(1)
    if len(result) > 0:
      data = {
               'name': result[0].name,
               'id': result[0].id,
               'author': result[0].author,
               'content': result[0].content,
               'title': result[0].title,
               'date': result[0].date
             }
      memcache.set("comic_name"+str(name), data)
      memcache.set("comic_id"+result[0].id, data)
      return data
    else:
      return None

def GetComicById(id):
  data = memcache.get("comic_id"+str(id))
  if data is not None:
    return data
  else:
    result = Comic.gql("WHERE id = :1 LIMIT 1", "id"+str(id)).fetch(1)
    if len(result) > 0:
      data = {
               'name': result[0].name,
               'id': result[0].id,
               'author': result[0].author,
               'content': result[0].content,
               'title': result[0].title,
               'date': result[0].date
             }
      memcache.set("comic_name"+result[0].name, data)
      memcache.set("comic_id"+str(id), data)
      return data
    else:
      return None

class ServeImage(webapp.RequestHandler):
  def get(self):
    comic = GetComicByName(self.request.path[5:])
    if comic is not None:
      self.response.headers['Content-Type'] = 'image/png'
      self.response.out.write(comic['content'])
    else:
      self.redirect('/images/noimage.png')

      

class UploadComic(webapp.RequestHandler):
    def post(self):
        if 'file' not in self.request.POST:
            self.error(400)
            self.response.out.write("file not specified!")
            return
        
        if (self.request.POST.get('file', None) is None or 
           not self.request.POST.get('file', None).filename):
            self.error(400)
            self.response.out.write("file not specified!")
            return
        
        file_data = self.request.POST.get('file').file.read()
        file_name = self.request.POST.get('file').filename
        
        im = Comic()
        im.name    = file_name
        im.content = file_data
        im.author = self.request.get('author')
        im.title = self.request.get('title')
        im.id = "id"+str(Count()+1)
        im.save()
        self.response.out.write("<script>alert(\"image %r saved." % im.name + "\");window.location='/';</script>Redirecting...")



class MainHandler(webapp.RequestHandler):
  def get(self):
    lat = Count()
    if lat == 0:
      self.response.out.write("This site has not yet been set up. Please contact the sysadmin.")
      return
    if len(self.request.path) <= 1 or int(self.request.path[1]) > lat:
      self.redirect('/'+str(lat))
      return
    num = int(self.request.path[1])
    comic = GetComicById(num)
    if num == lat:
      next = last = "#"
    else:
      next = "/"+str(num + 1)
      last = "/" + str(lat)
    if num == 1:
      prev = first = "#"
    else:
      prev = "/"+str(num-1)
      first = "/1"
    
    templateValues = {'num': num,
                      'prev': prev, 
                      'last': last, 
                      'next': next, 
                      'rand': random.randint(1, lat),
                      'first': first,
                      'name': comic['name'],
                      'title': comic['title'],
                      'author': comic['author'],
                      'mm': comic['date'].month,
                      'dd': comic['date'].day,
                      'yy': comic['date'].year}
    path = 'templates/index.htm'
    self.response.out.write(template.render(path, templateValues))

class AdminHandler(webapp.RequestHandler):
  def get(self):
    templateValues = {'rand':random.randint(1, 9999)}
    path = 'templates/admin.htm'
    self.response.out.write(template.render(path, templateValues))

class ArchiveHandler(webapp.RequestHandler):
  def get(self):
    templateValues = {'comics': range(1, Count()+1)}
    path = 'templates/archive.htm'
    self.response.out.write(template.render(path, templateValues))

class FlushMemcache(webapp.RequestHandler):
  def get(self):
    self.response.out.write(memcache.flush_all())

class FeedHandler(webapp.RequestHandler):
  def get(self):
    result = Comic.gql("ORDER BY date DESC LIMIT 10").fetch(10)
    templateValues = {'comics': result}
    path = 'templates/feed.xml'
    self.response.out.write(template.render(path, templateValues))

def main():
  application = webapp.WSGIApplication([
                                        ('/[0-9]*?', MainHandler),
                                        ('/admin', AdminHandler),
                                        ('/up', UploadComic),
                                        ('/archive', ArchiveHandler),
                                        ('/img/.*?', ServeImage),
                                        ('/fmc', FlushMemcache),
                                        ('/feed.xml', FeedHandler)
                                        ],
                                       debug=True)
  wsgiref.handlers.CGIHandler().run(application)


if __name__ == '__main__':
  main()
