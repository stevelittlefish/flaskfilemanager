# Flask File Manager

This project creates an easy to integrate package with a Flask blueprint to add a RichFilemanager
to your project.

## Initialisation

To use this in your project basically do the following:

```python
# Create the webapp
app = Flask(__name__)

# This is where the path for the uploads is defined
app.config['FLASKFILEMANAGER_FILE_PATH'] = 'tmp-webapp-uploads'

# You'll obviously do some more Flask stuff here!

# Initialise the filemanager
flaskfilemanager.init(app)
```

This will initialise the filemanager and add the blueprint to your project.

## Access Control

To set an access control function to the filemanager, for example to prevent people who aren't
logged in from accessing it, do the following:

```
def my_access_control_function():
	"""
	:return: True if the useris allowed to access the filemanager, otherwise False
	"""
	# You can do whatever permission check you need here
	return 'logged_in' in session and session['role'] == 'admin'

# Then when you init the filemanager do:
flaskfilemanager.init(app, access_control_function=my_access_control_function)
```

This will result in a 404 being displayed for all users who don't have the correct session values.

## Integration into your Flask app

To generate links to the filemanager:

```python
filemanager_link = url_for('flaskfilemanager.index')
file_download_link = url_for('flaskfilemanager.userfile, filename='/my_folder/uploaded_file.txt')
```

## TODO: ckeditor integration

This is easy.  Ask me if you need this and I'll write it up

## More info coming soon.
