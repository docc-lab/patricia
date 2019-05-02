#!/usr/bin/env python

'''
Copyright 2019 NetApp Inc.

Permission is hereby granted, free of charge, to any person obtaining a copy of this software and associated documentation files (the "Software"), 
to deal in the Software without restriction, including without limitation the rights to use, copy, modify, merge, publish, distribute, sublicense, 
and/or sell copies of the Software, and to permit persons to whom the Software is furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, 
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER 
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR 
THE USE OR OTHER DEALINGS IN THE SOFTWARE.


Author: Mania Abdi, Peter Macko
'''

"""
test.py
"""

# Mania: instrument this code with jaeger and then use patricia trace collector
# and then per span create two process. 
# and then add the prov info with the originator python_test.
# I think you should be done by today. 

import CPL
import sys
import tempfile
import logging
import time
from jaeger_client import Config
import uuid

log_level = logging.DEBUG
logging.getLogger('').handlers = []
logging.basicConfig(format='%(asctime)s %(message)s', level=log_level)

config = Config(
        config={ # usually read from some yaml config
            'sampler': {
                'type': 'const',
                'param': 1,
            },
            'logging': True,
        },  
        service_name='ceph-service-2',
        validate=True,)
    
# this call also sets opentracing.tracer
tracer = config.initialize_tracer()

od = {
        "name": sys.argv[1],
        "type": "data"
}
idod = uuid.uuid3(uuid.NAMESPACE_DNS, str(od))


om = {
        "name": sys.argv[1],
        "type": "meta"
}
idom = uuid.uuid3(uuid.NAMESPACE_DNS, str(om))

with tracer.start_span("Radosgw-Read") as span1:
    time.sleep(1)
    '''
    with tracer.start_span("Read-Meta", child_of=span1) as span_meta:
        time.sleep(1)
        
        with tracer.start_span("OSD", child_of=span_meta) as span_osd1:
            obj2_name = str(idom);
            obj2_type = 'file'
            span_osd1.log_kv({'type': obj2_type, 'name': obj2_name, 'method': 'read'})
            time.sleep(1)
    '''
    with tracer.start_span("Read-Data", child_of=span1) as span_data:
        time.sleep(1)

        with tracer.start_span("OSD", child_of=span_data) as span_osd2:
            obj3_name = str(idod);
            obj3_type = 'file'
            span_osd2.log_kv({'type': obj3_type, 'name': obj3_name, 'method': 'read'})
            time.sleep(1)


tracer.close() 
