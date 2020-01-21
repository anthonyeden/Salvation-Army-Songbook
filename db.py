# Generic SQL wrapper functions for SQLite
import os
import sqlite3

def connect():
    # Create a database connection
    db_filename = 'sahb.sqlite'
    if not os.path.exists(db_filename):
        raise Exception("Cannot find SQLite file")

    db = sqlite3.connect(db_filename)

    return db

def execute(sql, params=()):
    # Execute a SQL Statement
    conn = connect()

    cur = conn.cursor()
    cur.execute(sql, params)

    data = []
    fields = []

    if cur.description:
        for fieldNum, fieldData in enumerate(cur.description):
            fields.append(fieldData[0])

    for row in cur:
        rowData = {}

        for fieldNum, fieldName in enumerate(fields):
            rowData[fieldName] = row[fieldNum]

        data.append(rowData)

    conn.commit()

    if len(data) == 0:
        return []

    return data