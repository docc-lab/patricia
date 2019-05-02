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
"""
Test python bindings.
"""

# Mania: instrument this code with jaeger and then use patricia trace collector
# and then per span create two process. 
# and then add the prov info with the originator python_test.
# I think you should be done by today. 

import Patricia
import sys
import tempfile

originator = 'pt2obj_v1'
c = Patricia.patricia_connection()

# Create objects 
print
print '----- Create tests -----'
print

obj1_name = "Process X"
obj1_type = 'proc'
print ('Create object name: ' + obj1_name 
        + ' type: ' + obj1_type + 
        ' container: void')
o1 = c.create_object(originator, obj1_name, obj1_type)

Patricia.p_object(o1, True)
Patricia.p_object_version(o1.current_version(), True)

obj2_name = "File A"
obj2_type = 'file'
print ('\nCreate object name: ' + obj2_name + ' type: ' + obj2_type +
    ' container: ')
Patricia.p_id(o1.id, with_newline=True)
o2 = c.create_object(originator, obj2_name, obj2_type, o1)
Patricia.p_object(o2)


# Lookup Objects
print
print '----- Lookup Tests -----'
print

print ('Looking up object name: ' + obj1_name + ' type: ' + obj1_type)
o1_check = c.lookup_object(originator, obj1_name, obj1_type)
if o1.id != o1_check.id:
	sys.stdout.write('Lookup returned wrong object: ')
	Patricia.p_id(o1_check.id, with_newline = True)
	sys.exit(1)

print ('Looking up object name: ' + obj2_name + ' type: ' + obj2_type)
o2_check = c.lookup_object(originator, obj2_name, obj2_type)
if o2.id != o2_check.id:
	sys.stdout.write('Lookup returned wrong object: ')
	Patricia.p_id(o2_check.id, with_newline = True)
	sys.exit(1)

# Dependencies
print
print '----- Dependencies -----'
print
print 'data flow DEFAULT from o2 to o1 (no dup)'
r1 = o2.data_flow_to(o1)


#Ancestry
print
print '----- Ancestry -----'
print

for o in [o1, o2]:
	Patricia.p_object(o)
	print 'Data Ancestors: '
	rda = o1.ancestry(direction = Patricia.D_ANCESTORS,
	    flags = Patricia.A_NO_CONTROL_DEPENDENCIES)
	for i in rda:
		print str(i)

	print '\nData Descendants: '
	rdd = o1.ancestry(direction = Patricia.D_DESCENDANTS,
	    flags = Patricia.A_NO_CONTROL_DEPENDENCIES)
	for i in rdd:
		print str(i)

	print '\nControl Ancestors: '
	rca = o1.ancestry(direction = Patricia.D_ANCESTORS,
	    flags = Patricia.A_NO_DATA_DEPENDENCIES)
	for i in rca:
		print str(i)

	print '\nControl Descendants: '
	rcd = o1.ancestry(direction = Patricia.D_DESCENDANTS,
	    flags = Patricia.A_NO_DATA_DEPENDENCIES)
	for i in rcd:
		print str(i)


#Properties
print
print '----- Properties -----'
print

print 'Adding dog/fido to o1'
o1.add_property('dog', 'fido')

print 'Adding cat/nyla to o1'
o1.add_property('cat', 'nyla')

print 'Adding dog/bowser to o2'
o2.add_property('dog', 'bowser')

print 'Getting properties for o1'
print o1.properties()

print 'Getting properties for o2'
print o2.properties()

# Exit
print
print "Closing connection"
c.close()
