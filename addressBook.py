#!/usr/bin/python
#-*- encoding:utf-8 -*-

import os
import sys
import csv
import json

class unsupportedTypeError(Exception):
    pass

class contactBook:
    def __init__(self):
        self.accepted = ["csv", "vcf", "json"]
        self.check_config()
        self.refresh_data()

    def check_config(self):
        if "contacts.json" not in os.listdir("."):
            with open('contacts.json', 'a+') as conf:
                conf.write("{}")
                conf.close()
        return

    def refresh_data(self):
        with open('contacts.json',) as self.f:
            self.data = json.load(self.f)

    def parse(self, path, filetype):
        if filetype == "csv":
            with open(path) as csv_file:
                csv_reader = csv.reader(csv_file, delimiter=',')
                line = 0
                toAdd = {}
                for row in csv_reader:
                    if line == 0:
                        columns = row
                        name_index = columns.index("Display Name")
                        email_index = columns.index("Primary Email")
                    else:
                        info = row
                        name = info[name_index]
                        email = info[email_index]
                        if len(email) > 1:
                            toAdd[email] = name
                    line += 1
                return toAdd

        elif filetype == "vcf":
            toAdd = {}
            f = open(path, "r").read().splitlines()
            for row in f:
                if row.startswith("FN:"):
                    name = row[3:]
                elif row.startswith("EMAIL:"):
                    email = row[6:]
            if len(email) > 1:
                toAdd[email] = name
                return toAdd
        
        elif filetype == "json":
            toAdd = {}
            f = open(path,)
            data = json.load(f)
            for key in data.keys():
                name = data[key]
                email = key
                if len(email) > 1:
                    toAdd[email] = name
            return toAdd

    def add_contact(self, name, email):
        self.refresh_data()
        print("Adding contact")
        f = open('contacts.json',)
        data = json.load(f)
        toAdd= {email : name}
        data.update(toAdd)
        with open('contacts.json', 'w') as conf:
            json.dump(data, conf, indent=4, sort_keys=True)
        return

    def getContacts(self):
        self.refresh_data()
        return self.data

    def import_contacts(self, files):
        self.refresh_data()
        print("Importing contacts")
        f = open('contacts.json',)
        data = json.load(f)
        toAdd = {}
        for f in files.keys():
            filetype = files[f][files[f].rfind(".")+1:]
            if filetype not in self.accepted:
                raise unsupportedTypeError("Filetype not supported!")
            else:
                gotList = self.parse(f, filetype)
                if gotList:
                    toAdd.update(gotList)
        data.update(toAdd)
        with open('contacts.json', 'w') as conf:
            json.dump(data, conf, indent=4, sort_keys=True)
        print("Done")
        return

    def export_contacts(self, filetype):
        self.refresh_data()
        if filetype == "json":
            with open('contacts.json', "r") as f:
                return (f.read(), "contacts.json")
        elif filetype == "csv":
            csv_content = "Display Name,Primary Email\n"
            for key in self.data.keys():
                csv_content += "%s,%s\n" %(self.data[key], key)
            return (csv_content, "contacts.csv")


