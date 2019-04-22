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
patricia=False;
list_keyspace_query = "SELECT keyspace_name FROM system_schema.keyspaces;"
keyspaces = session.execute(list_keyspace_query);
for row in keyspaces:
    if row.keyspace_name == 'patricia_jaeger':
        print ('check patriacia ..... yes')
        patricia = True;
        break;
        
if patricia == False:        
    query = """CREATE KEYSPACE patricia_jaeger WITH replication = {'class':'SimpleStrategy', 'replication_factor' : 1};"""
    session.execute(query);


session.execute('USE patricia_jaeger;');

# Create Tables
# object table
create_table_query = """CREATE TABLE object(
                      id uuid,
                      parent_id uuid,
                      originator text, 
                      name text, 
                      type text,
                      birthday bigint,
                      deathtime bigint,
                      trace_id blob,
                      span_id bigint,
                      PRIMARY KEY (id)
                      );""" 
raw = session.execute(create_table_query);

create_table_query = """CREATE TABLE flow(
                        id_p uuid, 
                        id_c uuid,
                        type text, 
                        event text, 
                        ts bigint,
                        PRIMARY KEY (id_p, id_c, type, ts));"""
raw = session.execute(create_table_query);


create_table_query = """CREATE TABLE property(
                        id uuid,
                        version bigint,
                        key text, 
                        value text, 
                        ts bigint,
                        PRIMARY KEY (id, version, key, ts));"""
raw = session.execute(create_table_query);


print(raw)
cluster.shutdown()
