#!/usr/bin/env python2.7

""" Tool to query and report on workout data from SQLite3 """

import argparse
import sqlite3
import sys


def open_db(filename):
    """ Open SQLite3 database file """
    conn = sqlite3.connect(filename)
    return conn

class Querier(object):

    def __init__(self, dbcursor):
        self.cur = dbcursor


    def query(self, lift):
        q = """select session_timestamp, session_entry_lift, session_entry_reps,
        session_entry_pounds from session join session_entry on session.id ==
        session_entry.session_id where session_entry_lift == ?"""

        res = self.cur.execute(q, (lift,))
        f = open("%s.txt" %(lift), "w")

        def wendler_1rm(weight, reps):
            # Weight x Reps x .0333 + Weight = Estimated 1RM
            return weight * reps * 0.0333 + weight

        for row in res.fetchall():
            print row
            date = row[0].split(' ')[0]
            val = wendler_1rm(row[3], row[2])
            line = "%s,%d\n" %(date, val)

            f.write(line)

        f.close()


def main():
    parser = argparse.ArgumentParser(
        description='Generate SIMILE timeplot data from SQLite3 db'
        )
    parser.add_argument('-i', '--input', dest='dbfile',
            help='sqlite3 data file to read (default: output.db)',
            default="output.db")

    args = parser.parse_args()

    conn = open_db(args.dbfile)
    cur = conn.cursor()

    q = Querier(cur)
    for lift in ("bench press", "press", "deadlift", "squat"):
        q.query(lift)

if __name__ == "__main__":
    main()
