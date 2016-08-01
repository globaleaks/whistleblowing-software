import json
import os

from globaleaks.settings import GLSettings

from . import Config


def validate_input(raw_json):
    if not isinstance(raw_json, dict):
        raise ValueError
    #if len(raw_json) != 2:
    #    raise ValueError
    for k, val in raw_json.iteritems():
        if not isinstance(val, list): raise ValueError
        for item in val:
          if len(item.keys()) != 3: raise ValueError
    return raw_json


def load_json_config(store):
    fpath = os.path.join(GLSettings.root_path, 'globaleaks', 'models', 'config.json')
    with open(fpath, 'r') as f:
        r = json.loads(f.read())
        config_opts = validate_input(r)

        for gname, group in config_opts.iteritems():
            for item_def in group:
                item = Config(gname, item_def['name'], item_def['type'], item_def['val'])
                store.add(item)
