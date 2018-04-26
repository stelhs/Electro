import os, glob, sys, pprint, re, json


class Settings():
    defaultSettings = {"backupInterval": 10 * 60,
                       "lastProjectDir": ""}
    _settings = defaultSettings

    def __init__(self):
        homeDir = os.getenv("HOME")
        self._settingsFile = "%s/.electro" % homeDir

        if not os.path.isfile(self._settingsFile):
            self.save()
            return

        file = open(self._settingsFile, "r")
        jsonText = file.read()
        file.close()
        try:
            settings = json.loads(str(jsonText))
        except:
            print("Bad settings data")
            return
        Settings._settings = settings


    def data(self):
        return Settings._settings


    def set(self, key, value):
        Settings._settings[key] = value
        self.save()


    def save(self):
        file = open(self._settingsFile, "w")
        file.write(json.dumps(Settings._settings, indent=2, sort_keys=True))
        file.close()

