#!/usr/bin/env python

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

