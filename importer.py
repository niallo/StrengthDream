#!/usr/bin/env python2.7

""" Tool to import unstructured Wendler workout data to SQLite3 """

import argparse
import datetime
import json
import sqlite3
import sys

def parse_unstructured_text(text):
    ''' Parser for unstructured text '''

    # parser states
    START, FOUND_LIFT, FOUND_QUANTITIES = (0, 1, 2)
    # accepted lift names with some normalisations
    lifts = {"deadlift" : "deadlift", "bench" : "bench press", "press" :
            "press", "shoulder press" : "press",  "military press" : "press",
            "squat": "squat"}

    state = START
    entries = []
    entry = {'numbers':[]}
    for line in text.split('\n'):
        l = line.lower()
        ls = l.strip()
        if state == START:
            for lift in lifts:
                if ls.startswith(lift):
                    entry["lift"] = lifts[lift.lower().strip()]
                    if "warmup" in text.lower():
                        state = FOUND_LIFT
                    else:
                        state = FOUND_QUANTITIES
        elif state == FOUND_LIFT:
            if ls.startswith("warmup"):
                state = FOUND_QUANTITIES
        elif state == FOUND_QUANTITIES:
            if entry["numbers"] and (not ls or 'x' not in ls):
                state = START
                entries.append(entry)
                entry = {'numbers':[]}
                continue
            reps, pounds = l.split('x')
            try:
                reps = int(reps)
            except ValueError:
                reps = None
            pounds = pounds.strip()

            entry["numbers"].append({"reps":reps, "pounds":pounds})

    # handle edge end case
    if not entries and entry:
        entries.append(entry)

    return entries

def open_db(filename):
    """ Open SQLite3 database file """
    conn = sqlite3.connect(filename)
    return conn

def load_and_execute_schema(cursor):
    f = open("schema.sql", "r")
    schema = f.read()
    f.close()
    for stmnt in schema.split(';'):
        cursor.execute(stmnt)


class DBCursorRequired(Exception):
    pass

class SessionsRequired(Exception):
    pass

class WendlerLoader(object):

    def __init__(self):
        self.raw_data = None

    def _load_raw_data(self, filename):

        f = open(filename, "r")
        data = f.read()
        f.close()

        notes = json.loads(data)

        def parse_rfc3339(s):
            if not s: return None
            return datetime.datetime.strptime(s, '%Y-%m-%dT%H:%M:%S.%fZ')

        self.raw_data = [{"date":parse_rfc3339(note.get("created_at")),
            "text":note.get("text")} for note in notes["notes"] if "wendler" in
            [tag.lower() for tag in note["tags"]]]

    def load_and_parse(self, filename):
        ''' Load & parse the unstructured data '''

        self._load_raw_data(filename)

        for item in self.raw_data:
            parsed = parse_unstructured_text(item["text"])
            item["entries"] = parsed

        self.parsed_data = self.raw_data

        return self.parsed_data


class SessionWriter(object):

    def __init__(self, dbcursor=None):
        if not dbcursor:
            raise DBCursorRequired()
        self.cur = dbcursor

    def write_schema(self):
        load_and_execute_schema(self.cur)

    def write_sessions(self, sessions=None):
        if not sessions:
            raise SessionsRequired()

        for session in sessions:
            s1 = "INSERT INTO session (session_timestamp, session_text) VALUES (?,?)"
            self.cur.execute(s1, (session["date"], session.get("text")))
            rowid = self.cur.lastrowid
            for session_entry in session["entries"]:
                s2 = "INSERT INTO session_entry (session_id, session_entry_lift, session_entry_reps, session_entry_pounds) VALUES (?, ?, ?, ?)"
                max_numbers = session_entry["numbers"][len(session_entry["numbers"])-1]
                self.cur.execute(s2, (rowid, session_entry["lift"],
                    max_numbers["reps"],
                    max_numbers["pounds"]))

def main():
    parser = argparse.ArgumentParser(
        description='Generate structured SQLite3 DB from Wendler 5-3-1 unstructured data'
        )
    parser.add_argument('-o', '--output', dest='dbfile',
            help='sqlite3 data file to write (default: output.db)',
            default="output.db")

    parser.add_argument('-f', '--file', dest='jsonfile',
        help="json input file to read",
        required=True)

    args = parser.parse_args()

    wl = WendlerLoader()
    wl.load_and_parse(args.jsonfile)

    conn = open_db(args.dbfile)
    cur = conn.cursor()

    sw = SessionWriter(cur)

    sw.write_schema()
    sw.write_sessions(sessions=wl.parsed_data)
    conn.commit()

if __name__ == "__main__":
    main()

