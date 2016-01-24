#!/usr/bin/env python
# -*- coding: utf-8 -*- #
from __future__ import unicode_literals

PLUGINS = ['i18n_subsites']

AUTHOR = 'Andreas Dewes'
SITENAME = 'Andreas Dewes'
SITEURL = ''

PATH = 'content'

TIMEZONE = 'Europe/Paris'

#DEFAULT_LANG = 'en'

I18N_SUBSITES = {
    'de': {
        'SITENAME': 'Andreas Dewes',
        }
    }

# Feed generation is usually not desired when developing
FEED_ALL_ATOM = None
CATEGORY_FEED_ATOM = None
TRANSLATION_FEED_ATOM = None
AUTHOR_FEED_ATOM = None
AUTHOR_FEED_RSS = None
THEME="themes/andreas-dewes"
DISPLAY_CATEGORIES_ON_MENU=False
MENUITEMS = [('Blog','/blog')]
ARTICLE_URL = 'blog/{slug}.html'
ARTICLE_SAVE_AS = 'blog/{slug}.html'
PAGE_URL='{slug}.html'
PAGE_SAVE_AS='{slug}.html'
INDEX_SAVE_AS='blog/index.html'
STATIC_PATHS = ['images','scripts','downloads','pages/scripts']
JINJA_EXTENSIONS = ['jinja2.ext.i18n']

DEFAULT_PAGINATION = 10

# Uncomment following line if you want document-relative URLs when developing
#RELATIVE_URLS = True
