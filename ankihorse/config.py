import json
import os


CONFIG_FILE = os.path.join(os.path.dirname(__file__), 'config.json')


class ConfigParser(object):
    def __init__(self):
        self.contents = {}

    def read(self, *files):
        success = []
        for f in files:
            try:
                with open(f, 'r') as fp:
                    self.contents.update(json.load(fp))
                success.append(f)
            except IOError:
                pass
        return success

    def write(self, fp):
        json.dump(self.contents, fp, indent=2)

    def add_section(self, section):
        self.contents[section] = {}

    def has_section(self, section):
        return section in self.contents

    def has_option(self, section, option):
        return section in self.contents and option in self.contents[section]

    def get(self, section, option):
        return self.contents[section][option]

    def set(self, section, option, value):
        self.contents[section][option] = value

