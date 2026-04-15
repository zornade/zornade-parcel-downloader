PLUGINNAME = zornade_parcel_downloader
PLUGINS = $(HOME)/.local/share/QGIS/QGIS3/profiles/default/python/plugins
PY_FILES = __init__.py zornade_parcel_downloader.py zornade_dialog.py zornade_api.py zornade_sketching.py
EXTRAS = metadata.txt icon.png README.md LICENSE

%.qm : %.ts
	lrelease $<

# The deploy target only works on unix like operating system where
# the Python plugins directory is located at:
# $HOME/.local/share/QGIS/QGIS3/profiles/default/python/plugins
deploy: compile transcompile
	mkdir -p $(PLUGINS)/$(PLUGINNAME)
	cp -vf $(PY_FILES) $(PLUGINS)/$(PLUGINNAME)
	cp -vf $(EXTRAS) $(PLUGINS)/$(PLUGINNAME)

# The dclean target removes compiled python files from plugin directory
dclean:
	find $(PLUGINS)/$(PLUGINNAME) -iname "*.pyc" -delete

# The depl target removes the plugin from qgis plugin directory
depl:
	rm -rf $(PLUGINS)/$(PLUGINNAME)

# The zip target deploys the plugin and creates a zip file with the deployed
# content. You can then upload the zip file on http://plugins.qgis.org
zip: deploy dclean
	rm -f $(PLUGINNAME).zip
	cd $(PLUGINS); zip -9r $(CURDIR)/$(PLUGINNAME).zip $(PLUGINNAME)

# Create a zip package of the plugin named $(PLUGINNAME).zip. 
# This requires a deployable plugin directory.
package: compile
	# The deploy target only works on unix like operating system where
	# the Python plugins directory is located at:
	# $HOME/.local/share/QGIS/QGIS3/profiles/default/python/plugins
	rm -f $(PLUGINNAME).zip
	zip -9r $(PLUGINNAME).zip $(PLUGINNAME) -x $(PLUGINNAME)/.git/\* \*.pyc

compile:
	# Nothing to compile for this plugin

transcompile:
	# No translations for this plugin

clean:
	rm -f $(PLUGINNAME).zip
