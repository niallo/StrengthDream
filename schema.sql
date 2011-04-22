CREATE TABLE session(id INTEGER PRIMARY KEY, session_timestamp DATE, session_text TEXT);
CREATE TABLE session_entry(id INTEGER PRIMARY KEY, session_id INTEGER, session_entry_lift TEXT, session_entry_reps INTEGER, session_entry_pounds INTEGER);
