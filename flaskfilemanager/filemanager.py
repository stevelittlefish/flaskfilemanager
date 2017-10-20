"""
Main filemanager package - contains blueprint
"""

import logging
import json
import os
from collections import OrderedDict
import datetime
import io
import shutil

from flask import Blueprint, request, make_response, send_from_directory, abort, url_for
from littlefish import util, imageutil
import PIL.Image

__author__ = 'Stephen Brown (Little Fish Solutions LTD)'


log = logging.getLogger(__name__)

_initialised = False
_access_control_function = None
_FILE_PATH = None
_URL_PREFIX = None

filemanager_blueprint = Blueprint('flaskfilemanager', __name__, static_folder='RichFilemanager',
                                  static_url_path='')


def set_access_control_function(fun):
    global _access_control_function
    _access_control_function = fun


def init(app, register_blueprint=True, url_prefix='/fm', access_control_function=None):
    global _initialised, _FILE_PATH, _URL_PREFIX

    if _initialised:
        raise Exception('Flask Filemanager can only be registered once!')

    _initialised = True

    _FILE_PATH = app.config.get('FLASKFILEMANAGER_FILE_PATH')
    if not _FILE_PATH:
        raise Exception('No FLASKFILEMANAGER_FILE_PATH value in config')
        
    log.info('File Manager Using file path: {}'.format(_FILE_PATH))
    util.ensure_dir(_FILE_PATH)
    
    if access_control_function:
        set_access_control_function(access_control_function)

    if register_blueprint:
        log.info('Registering filemanager blueprint to {}'.format(url_prefix))
        app.register_blueprint(filemanager_blueprint, url_prefix=url_prefix)


def get_root_path():
    return _FILE_PATH


def json_to_response(json_data, mime_type='application/json'):
    log.debug(json_data)
    response = make_response(json_data)
    response.headers['Content-Type'] = mime_type
    return response


def dict_to_response(dict_data, mime_type='application/json'):
    return json_to_response(json.dumps(dict_data), mime_type)


def error(message, short_name=None, code='-1'):
    log.error('Filemanager ERROR {} : {}'.format(code, message))
    return {
        'errors': [
            {
                'id': short_name if short_name else 'Error {}'.format(code),
                'title': message,
                'code': code
            }
        ]
    }


def web_path_to_local(path):
    return path.lstrip('/')


def web_path_to_os_path(path):
    return os.path.join(_FILE_PATH, web_path_to_local(path))


def get_url_path(path):
    # TODO: refactor these fucking functions
    return url_for('flaskfilemanager.userfile', filename='') + path.lstrip('/')


@filemanager_blueprint.route('/index.html')
def index():
    # Access control
    if _access_control_function and not _access_control_function():
        abort(404)
    
    return filemanager_blueprint.send_static_file('index.html')


@filemanager_blueprint.route('/userfiles/<path:filename>')
def userfile(filename):
    root_dir = os.getcwd()
    return send_from_directory(os.path.join(root_dir, _FILE_PATH), filename)


@filemanager_blueprint.route('/connectors/py/filemanager.py')
def connector():
    # Access control
    if _access_control_function and not _access_control_function():
        abort(404)

    log.debug(request.args)

    mode = request.args.get('mode')

    resp = None
    
    if mode == 'initiate':
        resp = initiate()
    elif mode == 'getfolder':
        resp = get_folder()
    elif mode == 'getfile':
        resp = get_file()
    elif mode == 'addfolder':
        resp = add_folder()
    elif mode == 'rename':
        resp = rename_file()
    elif mode == 'move':
        resp = move_file()
    elif mode == 'copy':
        resp = copy_file()
    elif mode == 'editfile':
        resp = edit_file()
    elif mode == 'delete':
        resp = delete_file()
    elif mode == 'download':
        if request.is_xhr:
            # This is really stupid - I don't get why it does this!
            resp = get_file()
        else:
            return download_file()
    elif mode == 'getimage':
        return get_image()
    elif mode == 'readfile':
        resp = error('Non implemented: readfile')
    elif mode == 'summarize':
        resp = error('Non implemented: summarize')

    if resp is not None:
        if 'errors' in resp:
            return dict_to_response(resp)

        return dict_to_response({'data': resp})

    return dict_to_response(error('Unknown GET mode: %s' % mode))


@filemanager_blueprint.route('/connectors/py/filemanager.py', methods=['POST'])
def post_connector():
    # Access control
    if _access_control_function and not _access_control_function():
        abort(404)

    log.debug('POST: %s' % request.form)
    log.debug('files: %s' % request.files)

    mode = request.form.get('mode')

    resp = None

    if mode == 'upload':
        resp = upload_file()
    elif mode == 'savefile':
        resp = save_file()
    elif mode == 'extract':
        resp = error('Non implemented: extract')

    if resp is not None:
        if 'errors' in resp:
            return dict_to_response(resp)

        return dict_to_response({'data': resp})

    return dict_to_response(error('Unknown POST mode: %s' % mode))


def initiate():
    return {
        'id': '/',
        'type': 'initiate',
        'attributes': {
            'config': {
                'options': {
                    'culture': 'en'
                },
                'security': {
                    'allowFolderDownload': True,
                    'readOnly': False,
                    'extensions': {
                        'ignoreCase': False,
                        'policy': 'DISALLOW_LIST',
                        'restrictions': []
                    }
                }
            }
        }
    }


def get_file(path=None, content=None):
    """
    :param path: relative path, or None to get from request
    :param content: file content, output in data. Used for editfile
    """
    if path is None:
        path = request.args.get('path')

    if path is None:
        return error('No path in request')
    
    filename = os.path.split(path.rstrip('/'))[-1]
    extension = filename.rsplit('.', 1)[-1]
    os_file_path = web_path_to_os_path(path)

    if os.path.isdir(os_file_path):
        file_type = 'folder'
        # Ensure trailing slash
        if path[-1] != '/':
            path += '/'
    else:
        file_type = 'file'

    ctime = int(os.path.getctime(os_file_path))
    mtime = int(os.path.getmtime(os_file_path))

    height = 0
    width = 0
    if extension in ['gif', 'jpg', 'jpeg', 'png']:
        im = PIL.Image.open(os_file_path)
        height, width = im.size
    
    attributes = {
        'name': filename,
        'path': get_url_path(path),
        'readable': 1 if os.access(os_file_path, os.R_OK) else 0,
        'writeable': 1 if os.access(os_file_path, os.W_OK) else 0,
        'created': datetime.datetime.fromtimestamp(ctime).ctime(),
        'modified': datetime.datetime.fromtimestamp(mtime).ctime(),
        'timestamp': mtime,
        'width': width,
        'height': height,
        'size': os.path.getsize(os_file_path)
    }

    if content:
        attributes['content'] = content

    return {
        'id': path,
        'type': file_type,
        'attributes': attributes
    }


def edit_file():
    path = request.args.get('path')
    
    if path is None:
        return error('No path in request')
    
    os_file_path = web_path_to_os_path(path)
    
    # Load the contents of the file
    content = util.read_file(os_file_path).decode()
    return get_file(path=path, content=content)


def get_folder():
    web_path = request.args.get('path')
    if not web_path:
        return error('No path in request')

    # Load the files
    os_path = web_path_to_os_path(web_path)
    file_list = os.listdir(os_path)

    file_list.sort(key=lambda s: s.lower())
    out = OrderedDict()

    for f in file_list:
        if os.path.isdir(os.path.join(os_path, f)):
            wpath = os.path.join(web_path, f)
            out[wpath] = get_file(wpath)

    for f in file_list:
        if not os.path.isdir(os.path.join(os_path, f)):
            wpath = os.path.join(web_path, f)
            out[wpath] = get_file(wpath)

    return out


def rename_file():
    web_old_path = request.args.get('old')
    if not web_old_path:
        return error('No old path specified')

    new_name = request.args.get('new')
    if not new_name:
        return error('No new name specified')

    old_name = os.path.split(web_old_path)[-1]

    if old_name == new_name:
        return error('Old name and new name are the same!')

    os_old_path = web_path_to_os_path(web_old_path)
    path_parts = os.path.split(os_old_path)
    os_new_path = os.path.join(*path_parts[:-1])
    os_new_path = os.path.join(os_new_path, new_name)
    
    web_path_parts = os.path.split(web_old_path)
    web_new_path = os.path.join(*web_path_parts[:-1])
    web_new_path = os.path.join(web_new_path, new_name)

    # Check if the new file exists already
    if os.path.exists(os_new_path):
        return error('A file with that name (%s) already exists' % new_name)

    # Looks like we're good to go!
    try:
        os.rename(os_old_path, os_new_path)
    except Exception as e:
        return error('Operation failed: %s' % e)

    return get_file(web_new_path)


def move_file():
    web_old_path = request.args.get('old')
    if not web_old_path:
        return error('No old path specified')

    web_new_path = request.args.get('new')
    if not web_new_path:
        return error('No new path specified')

    os_old_path = web_path_to_os_path(web_old_path)
    os_new_path = web_path_to_os_path(web_new_path)
    
    # Old path may be a directory, or a file.  It is the thing to be moved
    old_name = os.path.split(os_old_path.rstrip('/'))[-1]
    os_new_path = os.path.join(os_new_path, old_name)

    # Check if the new file exists already
    if os.path.exists(os_new_path):
        return error('A file with that name (%s) already exists' % os_new_path)

    # Looks like we're good to go!
    try:
        os.rename(os_old_path, os_new_path)
    except Exception as e:
        return error('Operation failed: %s' % e)

    return get_file(os.path.join(web_new_path, old_name))


def copy_file():
    web_old_path = request.args.get('source')
    if not web_old_path:
        return error('No old path specified')

    web_new_path = request.args.get('target')
    if not web_new_path:
        return error('No new path specified')

    os_old_path = web_path_to_os_path(web_old_path)
    os_new_dir_path = web_path_to_os_path(web_new_path)
    
    # Old path may be a directory, or a file.  It is the thing to be moved
    old_name = os.path.split(os_old_path.rstrip('/'))[-1]
    os_new_path = os.path.join(os_new_dir_path, old_name)

    # Check if the new file exists already
    if os.path.exists(os_new_path):
        return error('A file with that name (%s) already exists' % os_new_path)

    # Looks like we're good to go!
    try:
        if os.path.isdir(os_old_path):
            shutil.copytree(os_old_path, os_new_path)
        else:
            shutil.copy(os_old_path, os_new_dir_path)
    except Exception as e:
        return error('Operation failed: %s' % e)

    return get_file(os.path.join(web_new_path, old_name))


def add_folder():
    web_path = request.args.get('path')
    if not web_path:
        return error('No path specified')

    name = request.args.get('name')
    if not name:
        return error('No name for new folder')

    os_path = web_path_to_os_path(web_path)

    if not os.path.exists(os_path):
        return error('Path %s doesn\'t exist' % web_path)

    if not os.path.isdir(os_path):
        return error('Path %s is not a directory' % web_path)

    os_new_path = os.path.join(os_path, name)
    if os.path.exists(os_new_path):
        return error('File already exists')

    try:
        os.mkdir(os_new_path)
    except Exception as e:
        return error('Operation failed: %s' % e)

    return get_file(os.path.join(web_path, name))


def upload_file():
    # This is supposed to handle multiple files, but the frontend only ever seems to send 1...
    web_path = request.form.get('path')
    if not web_path:
        return error('No path in query')

    os_path = web_path_to_os_path(web_path)
    if not os.path.exists(os_path):
        return error('Path %s doesn\'t exist' % web_path)

    if not os.path.isdir(os_path):
        return error('Path %s is not a directory' % web_path)

    # Get uploaded file
    uploaded_file = request.files['files']
    filename = uploaded_file.filename

    os_dest_path = os.path.join(os_path, filename)
    if os.path.exists(os_dest_path):
        return error('Upload failed: file %s already exists' % os_dest_path)

    # Read the file into memory
    data = uploaded_file.read()
    
    log.info('Uploading file to {}'.format(os_dest_path))
    with open(os_dest_path, 'wb') as f:
        f.write(data)

    return [get_file(os.path.join(web_path, filename))]


def save_file():
    # This is supposed to handle multiple files, but the frontend only ever seems to send 1...
    web_path = request.form.get('path')
    if not web_path:
        return error('No path in query')

    os_path = web_path_to_os_path(web_path)
    if not os.path.exists(os_path):
        return error('Path %s doesn\'t exist' % web_path)

    if os.path.isdir(os_path):
        return error('Path %s is a directory' % web_path)

    content = request.form.get('content')
    if content is None:
        return error('No content')

    log.info('Overwriting file {}'.format(os_path))
    with open(os_path, 'w') as f:
        f.write(content)

    return get_file(web_path)


def replace_file():
    web_path = request.form.get('newfilepath')
    if not web_path:
        return error('No path in query')

    os_path = web_path_to_os_path(web_path)
    if not os.path.exists(os_path):
        return error('Path %s doesn\'t exist' % web_path)

    if os.path.isdir(os_path):
        return error('Path %s is not a valid file' % web_path)

    # Get uploaded file
    uploaded_file = next(iter(request.files.values()))

    # Read the file into memory
    data = uploaded_file.read()

    with open(os_path, 'wb') as f:
        f.write(data)

    path_parts = os.path.split(web_path)

    return {
        'Path': os.path.join(*path_parts[:-1]),
        'Name': path_parts[-1],
        'Error': '',
        'Code': 0
    }


def delete_file():
    web_path = request.args.get('path')
    if not web_path:
        return error('No path in query')

    if web_path == '/':
        return error('Can\'t delete root')

    response = get_file(web_path)

    os_path = web_path_to_os_path(web_path)
    if not os.path.exists(os_path):
        return error('File %s doesn\'t exist' % web_path)

    if os.path.isdir(os_path):
        try:
            log.info('Deleting directory: {}'.format(os_path))
            shutil.rmtree(os_path)
        except Exception as e:
            return error('Operation failed: %s' % e)
    else:
        try:
            log.info('Deleting file: {}'.format(os_path))
            os.remove(os_path)
        except Exception as e:
            return error('Operation failed: %s' % e)

    return response


def download_file():
    web_path = request.args.get('path')
    if not web_path:
        abort(400)

    os_path = web_path_to_os_path(web_path)
    if not os.path.exists(os_path):
        abort(404)
    
    if os.path.isdir(os_path):
        return 'TODO: download directory as zip'

    return send_from_directory(_FILE_PATH, web_path_to_local(web_path), as_attachment=True)


def get_image():
    web_path = request.args.get('path')
    if not web_path:
        return error('No path in request')

    thumbnail = request.args.get('thumbnail') == 'true'

    os_path = web_path_to_os_path(web_path)
    if not os.path.exists(os_path):
        abort(404)

    if os.path.isdir(os_path):
        return error('Requested image is actually a directory!')

    if thumbnail:
        image = PIL.Image.open(os_path)
        thumbnail_image = imageutil.resize_pad_image(image, 64, 64)
        thumbnail_io = io.BytesIO()
        thumbnail_image.save(thumbnail_io, format='PNG')
        thumbnail_data = thumbnail_io.getvalue()

        response = make_response(thumbnail_data)
        response.headers['Content-Type'] = 'image/png'
        response.headers['Content-Disposition'] = 'attachment; filename=thumbnail.png'
        return response

    return send_from_directory(_FILE_PATH, web_path_to_local(web_path), as_attachment=True)


