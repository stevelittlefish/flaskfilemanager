"""
Main blueprint for test app
"""

import logging

from flask import Blueprint, render_template

__author__ = 'Stephen Brown (Little Fish Solutions LTD)'

log = logging.getLogger(__name__)

main = Blueprint('main', __name__)


@main.route('/')
def index():
    return render_template('index.html')

