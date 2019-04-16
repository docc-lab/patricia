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

'''connect to Cassandra'''
cluster = Cluster()
session = cluster.connect()
session.execute('USE jaeger_v1_test')

'''connect to Patricia'''
patricia = Patricia.patricia_connection()

q_trace_table_meta = "SELECT * FROM system_schema.tables WHERE keyspace_name='jaeger_v1_test'"
rows = session.execute(q_trace_table_meta)

q_traces_ls = "SELECT trace_id, span_id, start_time, duration, parent_id, refs, operation_name, process.service_name, logs FROM traces"
rows = session.execute(q_traces_ls)


# create empty dataframe
col_names =  ['trace_id', 'span_id', 'object']
pat_object_df = pd.DataFrame(columns = col_names)
pat_object_df.set_index(['trace_id', 'span_id'], inplace=True)

for tr in rows._current_rows:   #traces_sortby_timestamp.iterrows():
    if (not pat_object_df.empty) and (pat_object_df['trace_id']==tr['trace_id']) and (pat_object_df['span_id']== tr['span_id']):
        continue;

    # create a Patricia object and insert into the Patricia
    obj = patricia.create_object(tr.process_service_name, tr.operation_name, 'proc', trace_id=bytearray(tr.trace_id), span_id=tr.span_id, creation_time=tr.start_time, death_time=long(tr.start_time) + long(tr.duration))
    pat_object_df.append({'trace_id': tr.trace_id, 'span_id': tr.span_id, 'object': obj}, ignore_index=True)
    
    # link to span end
    obj.control_flow_to(obj, type=Patricia.CONTROL_START, version = long(tr.start_time) + long(tr.duration))

    if tr.logs:
        for log in tr.logs:
            print("\t" + str(log.ts))
            for field in log.fields:
                print("\t\t" + str(field))
                if field.key == 'type':
                    otype = field.value_string
                elif field.key == 'name':
                    name = field.value_string
                elif field.key == 'method':
                    method = field.value_string
                
            shared_obj =  patricia.get_object(tr.process_service_name, name, otype, creation_time=log.ts)
            if method == 'write':
                shared_obj.data_flow_to(obj, type=Patricia.DATA_INPUT, version=log.ts)
            elif method == 'update':
                shared_obj.data_flow_from(shared_obj, type=Patricia.DATA_TRANSLATION, version=log.ts)
            elif method == 'read':
                shared_obj.data_flow_from(shared_obj, type=Patricia.DATA_GENERIC, version=log.ts)


for tr in rows._current_rows:
    if tr.refs:
        for ref in tr.refs:
            print(ref)
            if ref.ref_type == 'child-of':
                # get parent object
                p_obj = patricia.get_trace_object(trace_id=bytearray(tr.trace_id), span_id=tr.span_id)
                c_obj = patricia.get_trace_object(trace_id=bytearray(tr.trace_id), span_id=tr.span_id)
                c_obj.control_flow_from(p_obj, type=Patricia.CONTROL_START, version = tr.start_time)
                c_obj.control_flow_to(p_obj, type=Patricia.CONTROL_OP, version = p_obj.version())
