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
import webapp2
import cgi
import jinja2
import os
from google.appengine.ext import db

# set up jinja
template_dir = os.path.join(os.path.dirname(__file__), "templates")
jinja_env = jinja2.Environment(loader = jinja2.FileSystemLoader(template_dir), autoescape = True)

def get_posts(limit, offset):

    query = """SELECT * FROM Blog_DB
            ORDER BY created DESC
            LIMIT {0} OFFSET {1}""".format(str(limit), str(offset))
    posts = db.GqlQuery(query)
    return posts

class Blog_DB(db.Model):

    title = db.StringProperty(required = True)
    content = db.TextProperty(required = True)
    created = db.DateTimeProperty(auto_now_add = True)
    previous_post_id = db.StringProperty(required = False)
    next_post_id = db.StringProperty(required = False)

class Handler(webapp2.RequestHandler):
    """ A base RequestHandler class for our app.
        The other handlers inherit form this one.
    """

    def renderError(self, error_code):
        """ Sends an HTTP error code and a generic "oops!" message to the client. """

        self.error(error_code)
        self.response.write("Oops! Something went wrong.")

class MainHandler(Handler):
    def get(self):
        """t = jinja_env.get_template("main-page.html")
        content = t.render()
        self.response.write(content)"""
        self.redirect('/blog/')

class NewPost(Handler):
    def get(self):
        t = jinja_env.get_template("create-new-post.html")
        content = t.render()
        self.response.write(content)

    def post(self):
        title = self.request.get('post-title')
        content = self.request.get('post-content')
        content = content.replace("\r\n", "<br />")
        error_css, error_message, error_title, error_content = '', '', '', ''
        next_post_id = ''
        previous_post_id = ''
        db_exists = None
        if Blog_DB.all().count(limit=1):
            previous_post_id = get_posts(1, 0)[0].key().id()
            db_exists = True
        if title and content:
            post_entry = Blog_DB(title = title, content = content, previous_post_id = str(previous_post_id))
            post_entry.put()
            post_id_for_update = str(post_entry.key().id())
            if db_exists:
                update_next_post = Blog_DB.get_by_id(previous_post_id)
                update_next_post.next_post_id = post_id_for_update
                update_next_post.put()


            self.redirect('/blog/' + str(post_entry.key().id()))
        else:
            error_css = 'error_box'
            error_message = 'You need a title and content to make a new post.'
            if not title:
                error_title = 'error_box'
            if not content:
                error_content = 'error_box'
            t = jinja_env.get_template("create-new-post.html")
            content = t.render( title=title,
                                content=content,
                                errorTitle=error_title,
                                errorContent=error_content,
                                errorCss=error_css,
                                errorMessage=error_message)
            error_css, error_message, error_title, error_content = '', '', '', ''
            self.response.write(content)


class Blog(Handler):
    def get(self):
        page = self.request.get("page")
        error = self.request.get("error")
        offset = 0
        result_count = 5
        previous_page = ''
        next_page = ''

        if page.isdigit():
            page = int(page)
            if page > 1:
                next_page = page - 1
        else:
            page = 1

        offset = (page - 1) * result_count

        count = get_posts(6, offset).count(limit=6, offset=offset)

        if count > result_count:
            previous_page = page + 1


        posts = get_posts(5, offset)
        t = jinja_env.get_template("blog.html")
        content = t.render(posts = posts, error=error, page=page, previous_page=previous_page, next_page = next_page)
        self.response.write(content)

class ViewPost(Handler):
    def get(self, id):
        if Blog_DB.get_by_id(int(id)):
            post = Blog_DB.get_by_id(int(id))
            t = jinja_env.get_template("post.html")
            content = t.render(post=post)
            self.response.write(content)
        else:
            self.redirect('/blog/?error=' + str(id))

app = webapp2.WSGIApplication([
    ('/', MainHandler),
    ('/newpost', NewPost),
    ('/blog', Blog),
    ('/blog/', Blog),
    webapp2.Route('/blog/<id:\d+>', ViewPost)
], debug=True)
