# -*- coding: utf-8 -*-
import urllib
import os

from google.appengine.api import users
from google.appengine.ext import ndb
from google.appengine.datastore.datastore_query import Cursor

import webapp2
import jinja2

template_dir = os.path.join(os.path.dirname(__file__), 'templates')
jinja_env = jinja2.Environment(loader = jinja2.FileSystemLoader(template_dir), autoescape=True)

class Handler(webapp2.RequestHandler):

  def render(self, template, **kw):
    self.write(self.render_str(template,**kw))

  def render_str(self, template, **params):
    template = jinja_env.get_template(template)
    return template.render(params)

  def write(self, *a, **kw):
    self.response.write(*a, **kw)


COMMENT = 'Visitor'

def comment_key(comments_section=COMMENT):
    return ndb.Key('Comment', comments_section)

# [START post]
# These objects will represent our Post.
class Post(ndb.Model):
    """For representing an individual post entry."""
    content = ndb.StringProperty(indexed=False)
    date = ndb.DateTimeProperty(auto_now_add=True)
# [END post]

# [START main_page]
class MainPage(Handler):
    def get(self):
        comments_section = self.request.get('comments_section',COMMENT)

        if comments_section == COMMENT.lower(): comments_section = COMMENT
        posts_to_fetch = 5
        cursor_url = self.request.get('continue_posts')
        arguments = {
            'comments_section': comments_section,
            'error': self.request.get('error', '')
        }

# [START query]
        posts_query = Post.query(ancestor = comment_key(comments_section)).order(-Post.date)
        posts, cursor, more = posts_query.fetch_page(posts_to_fetch, start_cursor =
            Cursor(urlsafe=cursor_url))
# [END query]

        if more:
            arguments['continue_posts'] = cursor.urlsafe()

        # Push past posts data into jinja2 to process the HTML.
        arguments['posts'] = posts
        self.render('posts.html', **arguments)

# [END main_page]

# [START comment]
class PostComment(webapp2.RequestHandler):
    def post(self):
        comments_section = self.request.get('comments_section',COMMENT)
        post = Post(parent=comment_key(comments_section))
        content = self.request.get('content')

        if type(content) != unicode:
            content = unicode(content,'utf-8')

        # start validation
        content = content.strip()
        error = ''
        if len(content) == 0:
            # the content is invalid
            error = "Please enter a valid comment"
        else:
            post.content = content
            # Write to the Google Database only if comment is valid
            post.put()
       
        # Redirect the site
        query_params = {
            'comments_section': comments_section,
            'error': error
        }

        self.redirect('/?' + urllib.urlencode(query_params))
# [END comment]

app = webapp2.WSGIApplication([
    ('/', MainPage),
    ('/sign', PostComment),
], debug=True)