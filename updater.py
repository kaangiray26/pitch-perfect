#!/usr/bin/python
import sys
import os
import requests
import json
from os.path import normpath as n

arg=sys.argv[1:]
check_version = arg[0]

changelog = requests.get("https://raw.githubusercontent.com/f34rl00/pitch-perfect/master/lib/CHANGELOG").text
update_data = json.loads(changelog)
file_urls = update_data[check_version.strip()]

for url in file_urls:
    directory, filename = url.split("/")[-2:]
    if directory == "master":
        path = n(os.path.join(filename))
    else:
        path = n(os.path.join(directory, filename))
    data = requests.get(url).text
    with open(path, "w") as f:
        f.write(data)
with open(n(os.path.join("lib","VERSION"))) as f:
    f.write(check_version)

print("done.")
