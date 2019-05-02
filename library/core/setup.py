#!/usr/bin/env python
'''
Patricia: Provenance, Auditing and Tracing in CEPH

Copyright 2019 NetApp Inc.

Permission is hereby granted, free of charge, to any person obtaining a copy of this software and associated documentation files (the "Software"),
to deal in the Software without restriction, including without limitation the rights to use, copy, modify, merge, publish, distribute, sublicense,
and/or sell copies of the Software, and to permit persons to whom the Software is furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR
THE USE OR OTHER DEALINGS IN THE SOFTWARE.


Contributor(s): Peter Macko, Mania Abdi
'''
#
# setup.py
# Patricia Library
#
from cassandra.cluster import Cluster


# Connect to Cassandra
cluster = Cluster()
session = cluster.connect()

# Create a keyspace
#create_keyspace_query = "CREATE KEYSPACE patricia WITH replication = {'class':'SimpleStrategy', 'replication_factor' : 1};"
#raw = session.execute(create_keyspace_query)

# Check keyspace is valid
list_keyspace_query = "SELECT keyspace_name FROM system_schema.keyspaces;"
keyspaces = session.execute(list_keyspace_query);
for row in keyspaces:
    if row.keyspace_name == 'patricia':
        print ('check patriacia ..... yes')
        session.execute('USE patricia;');



# Create Tables
# object table
create_table_query = """CREATE TABLE object(
                      id timeuuid,
                      container timeuuid,
                      originator text, 
                      name text, 
                      type text,
                      birthday timestamp,
                      PRIMARY KEY (originator, name, type)
                      );""" 
raw = session.execute(create_table_query);

create_table_query = """CREATE TABLE flow(
                        id_p timeuuid, 
                        id_c timeuuid,
                        type text, 
                        event text, 
                        ts timestamp,
                        PRIMARY KEY (id_p, id_c, ts));"""
raw = session.execute(create_table_query);


create_table_query = """CREATE TABLE property(
                        id timeuuid,
                        version timestamp,
                        key text, 
                        value text, 
                        ts timestamp,
                        PRIMARY KEY (id, version, key, ts));"""
raw = session.execute(create_table_query);


print(raw)
cluster.shutdown()

