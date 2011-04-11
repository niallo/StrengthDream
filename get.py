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

def get_username():
    ''' Read username from terminal '''
    while True:
        sys.stdout.write("Username: ")
        username = sys.stdin.readline()
        if username.strip():
            break

    return username.strip()

def get_password():
    ''' Read password from terminal '''

    while True:
        password = getpass.getpass("Password: ")
        if password:
            break

    return password

class UsernameRequired(Exception):
    pass

class PasswordRequired(Exception):
    pass

class TagRequired(Exception):
    pass

class GetWendler(object):

    def __init__(self, username=None, password=None, tag=None):
        if not username:
            raise UsernameRequired()
        if not password:
            raise PasswordRequired()
        if not tag:
            raise TagRequired()

        self.username = username
        self.password = password
        self.tag = tag

    def _make_basic_auth_header(self):
        ''' Basic auth '''
        return {"Authorization":"Basic %s" %(
            base64.b64encode("%s:%s" %(self.username, self.password)))}

    def get_raw_data(self):

        ''' Fetch the raw unstructured workout data from Catch API. Other
        methods will parse this into structured  '''

        self.conn = httplib.HTTPSConnection(API)
        headers = self._make_basic_auth_header()

        req = self.conn.request("GET", "/v2/search?full=1&q=%s" %
                urllib.quote_plus(self.tag), headers=headers)

        res = self.conn.getresponse()

        if res.status != 200:
            sys.stderr.write("%d response from server.\n Reason: %s" %(res.status,
                res.reason))
            sys.exit(1)

        data = res.read()

        notes = json.loads(data)

        raw_data = [{"date":note.get("created_at"), "text":note.get("text")} for
                note in notes["notes"]]

        return raw_data


def main():
    parser = argparse.ArgumentParser(description='Get Wendler 5-3-1 unstructured data from Catch API')
    parser.add_argument('--tag', dest='tag',
                               default="#wendler",
                               help='tag to use (default: #wendler)')

    parser.add_argument('--username', dest='username', help='username to use')

    args = parser.parse_args()

    if not args.username:
        args.username = get_username()
    args.password = get_password()

    gw = GetWendler(username=args.username, password=args.password,
            tag=args.tag)

    print gw.get_raw_data()

if __name__ == "__main__":
    main()

