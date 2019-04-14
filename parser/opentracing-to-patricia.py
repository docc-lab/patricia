#!/usr/bin/env python
import pandas as pd
from cassandra.cluster import Cluster
from cassandra.cluster import Cluster
from cassandra.policies import DCAwareRoundRobinPolicy

import sys
sys.path.insert(0, "/home/maniaa/patricia/library/core")
#import CPL

import Patricia
import tempfile
import logging
import time
from jaeger_client import Config
import unicodedata
import base64

reload(sys)
sys.setdefaultencoding('utf8')

service_name = 'pt10'

def pandas_factory(colnames, rows):
    return pd.DataFrame(rows, columns=colnames)

'''connect to Cassandra'''
cluster = Cluster()
session = cluster.connect()
session.execute('USE jaeger_v1_test')

session.row_factory = pandas_factory
session.default_fetch_size = None

'''connect to Patricia'''
patricia = Patricia.patricia_connection()

q_trace_table_meta = "SELECT * FROM system_schema.tables WHERE keyspace_name='jaeger_v1_test'"
q_traces_ls = "SELECT trace_id, span_id, start_time, duration, parent_id, refs, process.service_name FROM traces"

rows = session.execute(q_trace_table_meta)

rows = session.execute(q_traces_ls)
traces_sortby_timestamp = rows._current_rows.sort_values(by=['start_time'])
traces_sortby_timestamp['end_time'] = traces_sortby_timestamp.apply(lambda row: row.start_time + row.duration, axis=1)
#traces_grouped = traces_sortby_timestamp.loc[traces_sortby_timestamp['process.service_name'] == service_name].groupby('trace_id');

# put all traces in a table

# create empty dataframe
col_names =  ['trace_id', 'span_id', 'object', 'birthday']
pat_object_df = pd.DataFrame(columns = col_names)
pat_object_df.set_index(['trace_id', 'span_id'], inplace=True)

for index, tr in traces_sortby_timestamp.iterrows():
    if (not pat_object_df.empty) and (pat_object_df['trace_id']==tr['trace_id']) and (pat_object_df['span_id']== tr['span_id']):
        continue;

    # create a Patricia object and insert into the Patricia
    obj = patricia.create_object(tr['process.service_name'], str(tr['trace_id']), 'span')
    pat_object_dict.append({'trace_id': tr['trace_id'], 'span_id': tr['span_id'], 'object': obj, 'birthday': tr['start_time']})



#for index, tr in traces_sortby_timestamp.iterrows():
#    if tr.refs:
#        print(tr.refs[0].ref_type)
#print(traces_sortby_timestamp['trace_id'].values[0])
#print(traces_sortby_timestamp['refs'])
