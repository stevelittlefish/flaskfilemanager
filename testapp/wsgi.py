"""
WSGI Entry Point (for gunicorn)
"""

import os
import sys

path = os.path.dirname(os.path.realpath(__file__))
include_path = os.path.abspath(os.path.join(path, '..'))

print('Including path: %s' % include_path)
sys.path.append(include_path)

from werkzeug.contrib.fixers import ProxyFix

from app import create_app

__author__ = 'Stephen Brown (Little Fish Solutions LTD)'

application = create_app()
application.wsgi_app = ProxyFix(application.wsgi_app)

