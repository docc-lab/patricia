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
        service_name='pt11',
        validate=True,)
    
# this call also sets opentracing.tracer
tracer = config.initialize_tracer()

obj1_name = "Process A"
# Create objects
print
print '----- Create tests -----'
print

obj1_name = "Process A"
obj1_type = 'proc'
print ('Create object name: ' +
        obj1_name + ' type: ' + obj1_type + ' container: void')
with tracer.start_span(obj1_name) as span:
    time.sleep(1)
    
    fh1 = tempfile.NamedTemporaryFile()
    obj2_name = fh1.name
    obj2_type = 'file'
    print ('Create object name: ' + obj2_name + ' type: ' + obj2_type +
            ' container: ')
    span.log_kv({'type': obj2_type, 'name': obj2_name, 'method': 'write'})
    fh1.write("Hello Patricia\n I am first file");
    time.sleep(1)

    obj3_name = "Process B"
    with tracer.start_span(obj3_name, child_of=span) as span2:        
        time.sleep(1)
    
        fh1.read();
        span2.log_kv({'type': obj2_type, 'name': obj2_name, 'method': 'read'})
        time.sleep(1)

        fh2 = tempfile.NamedTemporaryFile()
        obj4_name = fh2.name
        obj4_type = 'file'
        print ('Create object name: ' +
            obj4_name + ' type: ' + obj4_type + ' container: NONE')
        fh2.write("Hello Patricia\n I am 2nd file");
        span2.log_kv({'type': obj4_type, 'name': obj4_name, 'method': 'write'})
        time.sleep(1)
        fh2.read();
        span2.log_kv({'type': obj4_type, 'name': obj4_name, 'method': 'read'})
        time.sleep(1)
    
    fh3 = tempfile.NamedTemporaryFile()
    obj5_name = fh3.name
    obj5_type = 'file'
    fh3.write("Hello Patricia\n I am 3rd file");
    print ('Create object name: ' +
	obj5_name + ' type: ' + obj5_type + ' container: ')
    span.log_kv({'type': obj5_type, 'name': obj5_name, 'method': 'write'})
    time.sleep(1)
    
    # Lookup Objects
    print
    print '----- Lookup Tests -----'
    print

    fh1.write("I think your paper is accepted")
    print ('Looking up object name: ' + obj2_name + ' type: ' + obj2_type)
    span.log_kv({'type': obj2_type, 'name': obj2_name, 'method': 'update'})
    time.sleep(1)

    fh2.read()
    print ('Looking up object name: ' + obj4_name + ' type: ' + obj4_type)
    span.log_kv({'type': obj4_type, 'name': obj4_name, 'method': 'read'})
    time.sleep(1)

    fh3.read()
    print ('Looking up object name: ' + obj5_name + ' type: ' + obj5_type)
    span.log_kv({'type': obj5_type, 'name': obj5_name, 'method': 'read'})
    time.sleep(1)

fh1.close()
fh2.close()
fh3.close()

time.sleep(2)   # yield to IOLoop to flush the spans - https://github.com/jaegertracing/jaeger-client-python/issues/50

tracer.close() 
