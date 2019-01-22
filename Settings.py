"""
 * Save/restore editor settings
 *
 * Copyright (c) 2018 Michail Kurochkin
 *
 * Permission is hereby granted, free of charge, to any person obtaining a copy
 * of this software and associated documentation files (the "Software"), to deal
 * in the Software without restriction, including without limitation the rights
 * to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
 * copies of the Software, and to permit persons to whom the Software is
 * furnished to do so, subject to the following conditions:
 *
 * The above copyright notice and this permission notice shall be included in
 * all copies or substantial portions of the Software.
 *
 * THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
 * IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
 * FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
 * AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
 * LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
 * OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
 * THE SOFTWARE.
 """

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
        file.write(json.dumps(Settings._settings, indent=2, sort_keys=True, ensure_ascii=False))
        file.close()

