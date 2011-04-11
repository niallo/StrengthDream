#!/usr/bin/env python2.7

''' Fetch all notes tagged with #Wendler from Catch and parse them '''

import argparse
import base64
import getpass
import httplib
import json
import sys
import urllib

API = "api.catch.com"

def get_creds():
    ''' Read credentials from terminal '''
    sys.stdout.write("Username: ")
    username = sys.stdin.readline()

    password = getpass.getpass("Password: "), sys.stdin)

    return username, password


class GetWendler(object):

    def __init__(self, username, password):
        self.username = username
        self.password = password

    def _make_basic_auth_header(self):
        ''' Basic auth '''
        return {"Authorization":"Basic %s" %(
            base64.b64encode("%s:%s" %(self.username, self.password)))}

    def get_raw_data(self):

        ''' Fetch the raw unstructured workout data from Catch API. Other
        methods will parse this into structured  '''

        self.conn = httplib.HTTPSConnection(API)
        p = {"q":"#wendler"}
        params = urllib.urlencode(p)

        req = self.conn.request("GET", "/v2/search", params, headers)

        res = self.conn.getresponse()

        if res.status != 200:
            sys.stderr.write("%d response from server.\n Body: %s" %(res.status,
                res.body))
            sys.exit(1)

        data = response.read()

        notes = json.loads(data)

        raw_data = [{"date":note.get("created_at"), "text":note.get("text")} for
                note in notes]

        return raw_data


def main():


if __name__ == "__main__":
    main()

