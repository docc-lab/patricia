#!/usr/bin/env python
import pandas as pd
from graphviz import Digraph
from cassandra.cluster import Cluster
from cassandra.cluster import Cluster
from cassandra.policies import DCAwareRoundRobinPolicy

import sys
sys.path.insert(0, "/home/maniaa/core-provenance-library-1.01/bindings/python/CPL")
#import CPL
import sys
import tempfile
import logging
import time
from jaeger_client import Config


def pandas_factory(colnames, rows):
    return pd.DataFrame(rows, columns=colnames)

dot = Digraph(comment='Provenance Graph')

cluster = Cluster()
session = cluster.connect()
session.execute('USE jaeger_v1_test')

session.row_factory = pandas_factory
session.default_fetch_size = None


q_trace_table_meta = "SELECT * FROM system_schema.tables WHERE keyspace_name='jaeger_v1_test'"
q_traces_ls = "SELECT trace_id, span_id, start_time, duration, parent_id, process.service_name FROM traces"

rows = session.execute(q_trace_table_meta)

rows = session.execute(q_traces_ls)
traces_sortby_timestamp = rows._current_rows.sort_values(by=['start_time'])
traces_sortby_timestamp['end_time'] = traces_sortby_timestamp.apply(lambda row: row.start_time + row.duration, axis=1)
traces_grouped = traces_sortby_timestamp.loc[traces_sortby_timestamp['process.service_name'] == 'python_test'].groupby('trace_id');

print(traces_grouped)
for name,group in traces_grouped:
   ''' loop over each trace and for each span create start and end node'''
   print(group)

