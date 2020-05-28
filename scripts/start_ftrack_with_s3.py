import ftrack_api.structure.id
import sys
import os
import logging

'''
Starts ftrack using a plugin which registers a location
'''
logging.basicConfig()
plugin_logger = logging.getLogger()
plugin_logger.setLevel(logging.INFO)

root_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir))

sys.path.append(os.path.join(root_dir, "accessor"))

plugin_paths = [os.path.join(root_dir, "plugins")]

session = ftrack_api.Session(plugin_paths=plugin_paths, auto_connect_event_hub=True)
session.event_hub.wait()
