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

originator = 'pt5obj_v1'
c = Patricia.patricia_connection()

'''
print "Session information: "
CPL.p_session(c.session)
'''
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


obj3_name = "Process B"
obj3_type = 'proc'
print ('\nCreate object name: ' +
	obj3_name + ' type: ' + obj3_type + ' container: ')
Patricia.p_id(o1.id, with_newline=True)
o3 = c.create_object(originator, obj3_name, obj3_type, o1)
Patricia.p_object(o3)


obj4_name = "File B"
obj4_type = 'file'
print ('\nCreate object name: ' +
	obj4_name + ' type: ' + obj4_type + ' container: NONE')
o4 = c.create_object(originator, obj4_name, obj4_type, None)
Patricia.p_object(o4)

print('Lookup or create object: ' + obj4_name + ' ' + obj4_type + ' NONE ')
o4_check = c.get_object(originator, obj4_name, obj4_type, container = None)
Patricia.p_object(o4_check)
if o4.id != o4_check.id:
	print "Lookup returned wrong object!"
	sys.exit(1)

obj5_name = "File C"
obj5_type = 'file'
print ('Create object name: ' +
	obj5_name + ' type: ' + obj5_type + ' container: ')
Patricia.p_id(o1.id, with_newline = True)
o5 = c.create_object(originator, obj5_name, obj5_type, o1)
Patricia.p_object(o5)


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

print ('Looking up object name: ' + obj3_name + ' type: ' + obj3_type)
o3_check = c.lookup_object(originator, obj3_name, obj3_type)
if o3.id != o3_check.id:
	sys.stdout.write('Lookup returned wrong object: ')
	Patricia.p_id(o3_check.id, with_newline = True)
	sys.exit(1)

print ('Looking up object name: ' + obj4_name + ' type: ' + obj4_type)
o4_check = c.lookup_object(originator, obj4_name, obj4_type)
if o4.id != o4_check.id:
	sys.stdout.write('Lookup returned wrong object: ')
	Patricia.p_id(o4_check.id, with_newline = True)
	sys.exit(1)


print ('Looking up object name: ' + obj5_name + ' type: ' + obj5_type)
o5_check = c.lookup_object(originator, obj5_name, obj5_type)
if o5.id != o5_check.id:
	sys.stdout.write('Lookup returned wrong object: ')
	Patricia.p_id(o4_check.id, with_newline = True)
	sys.exit(1)


"""
Right now there is no way to do a lookup and specify a container
print ('Looking up object in wrong container name: ' +
 	obj5_name + ' type: ' + obj5_type + ' container: NONE')
o5_fail = c.lookup_object(originator, obj5_name, obj5_type)
if o5_fail != None:
 	sys.stdout.write('Lookup returned an object: ')
 	CPL.p_id(o4_fail.id, with_newline = True)

print ('Looking up object in wrong container name: ' +
	obj4_name + ' type: ' + obj4_type + ' container: ')
o4_fail = c.lookup_object(originator, obj4_name, obj4_type, o1.id)
if o4_fail != None:
	sys.stdout.write('Lookup returned an object: ')
	CPL.p_id(o5_fail.id, with_newline = True)
"""

print 'Look up non-existent object (type failure)'
o_fail1 = c.try_lookup_object(originator, obj1_name, 'no-type')
if o_fail1:
	print 'Returned an object: '
	Patricia.p_object(o_fail1)

print 'Look up non-existent object (name failure)'
o_fail2 = c.try_lookup_object(originator, 'no-name', obj1_type)
if o_fail2:
	print 'Returned an object: '
	Patricia.p_object(o_fail2)

print 'Look up non-existent object (originator failure)'
o_fail3 = c.try_lookup_object('no-originator', obj1_name, obj1_type)
if o_fail3:
	print 'Returned an object: '
	Patricia.p_object(o_fail3)


print 'Look up all objects with name: ' + obj1_name + ' type: ' + obj1_type
o1_all = c.lookup_all(originator, obj1_name, obj1_type)
i = 0
for t in o1_all:
	Patricia.p_id(t.id, with_newline = True)
	i += 1
	if i >= 10 and len(o1_all) > 10:
		print '  ... (' + str(len(o1_all)) + ' objects total)'
		break

print 'All objects'
all_objects = c.get_all_objects(True)
i = 0
for t in all_objects:
	Patricia.p_id(t.object.id, with_newline = False)
	print ' originator: ' + t.originator + ' name: ' + t.name +' type: '+t.type
	i += 1
	if i >= 10 and len(all_objects) > 10:
		print '  ... (' + str(len(all_objects)) + ' objects total)'
		break


# Dependencies
print
print '----- Dependencies -----'
print
print 'data flow DEFAULT from o2 to o1 (no dup)'
r1 = o2.data_flow_to(o1)
#if not r1:
#	print 'ERROR: ignoring duplicate'
#	sys.exit(1)


print 'data flow CPL.DATA_INPUT from o2 to o1 (w/dup)'
r2 = o2.data_flow_to(o1, Patricia.DATA_INPUT)
#if r2:
#	print 'ERROR: should have ignored duplicate'
#	sys.exit(1)

print 'data flow CPL.DATA_INPUT from o3 to o2 (no dup)'
r3 = o3.data_flow_to(o2, Patricia.DATA_INPUT)
#if not r3:
#	print 'ERROR: ignoring duplicate'
#	sys.exit(1)

print 'control flow CPL.CONTROL_START from o3 to o1 (no dup)'
r4 = o3.control_flow_to(o1, Patricia.CONTROL_START)
#if not r4:
#	print 'ERROR: ignoring duplicate'
#	sys.exit(1)

print 'data flow CPL.DATA_TRANSLATION from o1 to o3'
r5 = o1.data_flow_to(o3, Patricia.DATA_TRANSLATION)
#if not r5:
#	print 'ERROR: ignoring duplicate'
#	sys.exit(1)

print 'data flow DEFAULT from o1 ver. 0 to o5 (no dup)'
print o1.specific_version_index(0)
r6 = o1.specific_version_index(0).data_flow_to(o5)
#if not r6:
#	print 'ERROR: ignoring duplicate'
#	sys.exit(1)

print 'data flow DEFAULT from o1 ver. 0 to o5 (w/dup)'
print o5
r7 = o5.data_flow_from(o1.specific_version_index(0))
#if r7:
#	print 'ERROR: not ignoring duplicate'
#	sys.exit(1)

print 'data flow DEFAULT from o1 ver. 0 to o5 (w/dup)'
r8 = o5.data_flow_from(o1, version=0)
#if r8:
#	print 'ERROR: not ignoring duplicate'
#	sys.exit(1)

print 'control flow DEFAULT from o1 to o5 (no dup)'
r9 = o5.control_flow_from(o1)
#if not r9:
#	print 'ERROR: ignoring duplicate'
#	print '       the current version of o1 is ' + str(o1.version())
#	print '       ancestors of o5:'
#	a = o5.ancestry()
#	for e in a:
#		print '         ' + str(e.ancestor)
#	sys.exit(1)


#Object info
print
print '----- Object Info -----'
print

print 'Object info'
for o in [o1, o2, o3, o4, o5]:
	Patricia.p_object(o)



#Ancestry
print
print '----- Ancestry -----'
print

for o in [o1, o2, o3]:
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

print 'Adding cat/kimi to o3'
o3.add_property('cat', 'kimi')

print 'Getting properties for o1'
print o1.properties()

print 'Getting properties for o2'
print o2.properties()

print 'Getting properties for o3'
print o3.properties()

print 'Getting all objects with dog/fido property'
tuples = c.lookup_by_property('dog', 'fido')
i = 0
for t in tuples:
	print str(t)
	i += 1
	if i >= 10 and len(tuples) > 10:
		print '  ... (' + str(len(tuples)) + ' tuples total)'
		break

'''
# Create new version
print
print '----- New Version -----'
print

print 'Version of o1: ' + str(o1.version())
print 'New version of o1: ' + str(o1.new_version())
print 'New version of o1: ' + str(o1.new_version())
print 'New version of o1: ' + str(o1.new_version())
print ''

# File API
print
print '----- File API -----'
print

fh1 = tempfile.NamedTemporaryFile()
fh2 = tempfile.NamedTemporaryFile()

print "create_object_for_file(" + fh1.name + ")";
f1 = CPL.current_connection().create_object_for_file(fh1.name)
CPL.p_id(f1.id, True)

print "get_object_for_file(" + fh2.name + ")";
f2 = c.get_object_for_file(fh2.name)
CPL.p_id(f2.id, True)

print "get_object_for_file(" + fh1.name + ", F_LOOKUP_ONLY)";
f1x = c.get_object_for_file(fh1.name, CPL.F_LOOKUP_ONLY)
CPL.p_id(f1.id, True)
if f1 != f1x:
	sys.stdout.write('Lookup returned wrong object: ')
	CPL.p_id(f1x.id, with_newline = True)
	sys.exit(1)

fh1.close()
fh2.close()
'''

# Exit
print
print "Closing connection"
c.close()
