#!/usr/bin/env python2.7

''' Fetch all notes tagged with #Wendler from Catch and parse them '''

import argparse
import base64
import datetime
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
        username = sys.stdin.readline().strip()
        if username:
            break

    return username

def get_password():
    ''' Read password from terminal '''
    while True:
        password = getpass.getpass("Password: ")
        if password:
            break

    return password

def parse_unstructured_text(text):
    ''' Parser for unstructured text '''

    # parser states
    START, FOUND_LIFT, FOUND_QUANTITIES = (0, 1, 2)
    # accepted lift names
    lifts = ('deadlift', 'bench', 'press', 'squat', 'shoulder press')

    state = START
    entries = []
    entry = {'numbers':[]}
    for line in text.split('\n'):
        l = line.lower()
        ls = l.strip()
        if state == START:
            for lift in lifts:
                if ls.startswith(lift):
                    entry["lift"] = lift
                    state = FOUND_LIFT
        elif state == FOUND_LIFT:
            if ls.startswith("warmup"):
                state = FOUND_QUANTITIES
        elif state == FOUND_QUANTITIES:
            if not ls or 'x' not in ls:
                state = START
                entries.append(entry)
                entry = {'numbers':[]}
                continue
            reps, pounds = l.split('x')
            try:
                reps = int(reps)
            except ValueError:
                reps = None

            entry["numbers"].append({"reps":reps,
                "pounds":int(pounds.strip())})


    return entries



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
        self.raw_data = None

    def _make_basic_auth_header(self):
        ''' Basic auth '''
        return {"Authorization":"Basic %s" %(
            base64.b64encode("%s:%s" %(self.username, self.password)))}

    def load_raw_data(self):

        ''' Fetch the raw unstructured workout data from Catch API. Other
        methods will parse this into structured  '''

        self.conn = httplib.HTTPSConnection(API)
        headers = self._make_basic_auth_header()

        req = self.conn.request("GET", "/v2/search?full=1&q=%s" %
                urllib.quote_plus(self.tag), headers=headers)

        res = self.conn.getresponse()

        if res.status != 200:
            sys.stderr.write("%d response from server.\n Reason: %s" %(
                res.status,
                res.reason))
            sys.exit(1)

        data = res.read()

        notes = json.loads(data)

        def parse_rfc3339(s):
            if not s: return None
            return datetime.datetime.strptime(s, '%Y-%m-%dT%H:%M:%S.%fZ')

        self.raw_data = [{"date":parse_rfc3339(note.get("created_at")),
            "text":note.get("text")} for note in notes["notes"]]






def main():
    parser = argparse.ArgumentParser(description='Get Wendler 5-3-1 unstructured data from Catch API')
    parser.add_argument('-t', '--tag', dest='tag',
                               default="#wendler",
                               help='tag to use (default: #wendler)')

    parser.add_argument('-u', '--username', dest='username', help='username to use')

    args = parser.parse_args()

    if not args.username:
        args.username = get_username()
    args.password = get_password()

    gw = GetWendler(username=args.username, password=args.password,
            tag=args.tag)

    gw.load_raw_data()

    for note in gw.raw_data:
        print parse_unstructured_text(note["text"])

if __name__ == "__main__":
    main()

