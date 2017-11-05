import sys
from setuptools import setup

if sys.version_info.major < 3:
    sys.exit('Sorry, this library only supports Python 3')

setup(
    name='flaskfilemanager',
    packages=['flaskfilemanager'],
    include_package_data=True,
    version='0.0.3',
    description='RichFilemanager blueprint for Flask web applications - adds a ckeditor compatible file manager / browser',
    author='Stephen Brown (Little Fish Solutions LTD)',
    author_email='opensource@littlefish.solutions',
    url='https://github.com/stevelittlefish/flaskfilemanager',
    download_url='https://github.com/stevelittlefish/flaskfilemanager/archive/v0.0.3.tar.gz',
    keywords=['flask', 'jinja2', 'filemanager', 'file', 'manager', 'browser', 'ckeditor'],
    license='Apache',
    classifiers=[
        'License :: OSI Approved :: Apache Software License',
        'Framework :: Flask',
        'Development Status :: 5 - Production/Stable',
        'Intended Audience :: Developers',
        'Programming Language :: Python :: 3',
        'Topic :: Software Development :: Libraries'
    ],
    install_requires=[
        'littlefish>=0.0.3',
        'Flask>=0.12.0',
        'Pillow>=4.1.0'
    ],
)

