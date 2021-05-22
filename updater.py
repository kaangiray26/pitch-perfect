#!/usr/bin/python
import sys
import os
import requests
import json
from os.path import normpath as n

class Updater:
    def __init__(self):
        self.arg = sys.argv[1:]
        self.check_version, self.version,  = self.arg[0].strip(), self.arg[1].strip()

    def perform_update(self):
        changelog = requests.get("https://raw.githubusercontent.com/f34rl00/pitch-perfect/master/lib/CHANGELOG").text
        update_data = json.loads(changelog)
        versions = list(update_data.keys())
        versions.reverse()
        versions = versions[versions.index(self.version)+1:]
        file_urls = []
        for version in versions:
            file_urls = list(set(file_urls) | set(update_data[version]))
        print(file_urls)
        if len(file_urls) == 0:
            with open(n(os.path.join("lib", "VERSION")), "w") as f:
                f.write(self.check_version)
            os.execv(sys.executable, ['python', "qt_app.py", "--updatedEmpty"])
            return

        for url in file_urls:
            directory, filename = url.split("/")[-2:]
            if directory == "master":
                path = n(os.path.join(filename))
            else:
                path = n(os.path.join(directory, filename))
            data = requests.get(url).text
            with open(path, "w") as f:
                f.write(data)
        with open(n(os.path.join("lib","VERSION")),"w") as f:
            f.write(self.check_version)
        
        os.execv(sys.executable, ['python', "qt_app.py", "--updatedTrue"])
        return


if __name__ == "__main__":
    updater = Updater()
    try:
        updater.perform_update()
    except ValueError:
        os.execv(sys.executable, ['python', "qt_app.py", "--updatedFalse"])
        
