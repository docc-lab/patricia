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
import sys
from cassandra.cluster import Cluster
import random
import uuid
import CPLDirect
import datetime
import time
import calendar

def unix_time(dt):
    epoch = datetime.datetime.utcfromtimestamp(0)
    delta = dt - epoch
    return delta.total_seconds()

def unix_time_millis(dt):
    return long(unix_time(dt) * 1000.0)


def cpl_data_dependency(n):
    return ((1 << 8) | (n))

def cpl_control_dependency(n):
    return ((2 << 8) | (n))

def cpl_version_dependency(n):
    return ((1 << 8) | (n))

def get_dependency_category(d):
    return ((d) >> 8);


#
# Constants
#
#
# Constants
#

NONE = CPLDirect.CPL_NONE
VERSION_NONE = -1
DEPENDENCY_CATEGORY_DATA = 1 
DEPENDENCY_CATEGORY_CONTROL = 2
DEPENDENCY_CATEGORY_VERSION = 3
DEPENDENCY_NONE = 0

DATA_INPUT = cpl_data_dependency(0)
DATA_GENERIC = cpl_data_dependency(0)
DATA_IPC = cpl_data_dependency(1)
DATA_TRANSLATION = cpl_data_dependency(2)
DATA_COPY = cpl_data_dependency(3)

CONTROL_OP = cpl_control_dependency(0) 
CONTROL_GENERIC = cpl_control_dependency(0) 
CONTROL_START = cpl_control_dependency(1) 
VERSION_PREV = cpl_version_dependency(0)
VERSION_GENERIC = cpl_version_dependency(0)



D_ANCESTORS=0
D_DESCENDANTS=1

S_OK = CPLDirect.CPL_S_OK
OK = CPLDirect.CPL_OK
S_DUPLICATE_IGNORED = CPLDirect.CPL_S_DUPLICATE_IGNORED
S_NO_DATA = CPLDirect.CPL_S_NO_DATA
S_OBJECT_CREATED = CPLDirect.CPL_S_OBJECT_CREATED
E_INVALID_ARGUMENT = CPLDirect.CPL_E_INVALID_ARGUMENT
E_INSUFFICIENT_RESOURCES = CPLDirect.CPL_E_INSUFFICIENT_RESOURCES
E_DB_CONNECTION_ERROR = CPLDirect.CPL_E_DB_CONNECTION_ERROR
E_NOT_IMPLEMENTED = CPLDirect.CPL_E_NOT_IMPLEMENTED
E_ALREADY_INITIALIZED = CPLDirect.CPL_E_ALREADY_INITIALIZED
E_NOT_INITIALIZED = CPLDirect.CPL_E_NOT_INITIALIZED
E_PREPARE_STATEMENT_ERROR = CPLDirect.CPL_E_PREPARE_STATEMENT_ERROR
E_STATEMENT_ERROR = CPLDirect.CPL_E_STATEMENT_ERROR
E_INTERNAL_ERROR = CPLDirect.CPL_E_INTERNAL_ERROR
E_BACKEND_INTERNAL_ERROR = CPLDirect.CPL_E_BACKEND_INTERNAL_ERROR
E_NOT_FOUND = CPLDirect.CPL_E_NOT_FOUND
E_ALREADY_EXISTS = CPLDirect.CPL_E_ALREADY_EXISTS
E_PLATFORM_ERROR = CPLDirect.CPL_E_PLATFORM_ERROR
E_INVALID_VERSION = CPLDirect.CPL_E_INVALID_VERSION
E_DB_NULL = CPLDirect.CPL_E_DB_NULL
E_DB_KEY_NOT_FOUND = CPLDirect.CPL_E_DB_KEY_NOT_FOUND
E_DB_INVALID_TYPE = CPLDirect.CPL_E_DB_INVALID_TYPE
O_FILESYSTEM = CPLDirect.CPL_O_FILESYSTEM
O_INTERNET = CPLDirect.CPL_O_INTERNET
T_ARTIFACT = CPLDirect.CPL_T_ARTIFACT
T_FILE = CPLDirect.CPL_T_FILE
T_PROCESS = CPLDirect.CPL_T_PROCESS
T_URL = CPLDirect.CPL_T_URL
L_NO_FAIL = CPLDirect.CPL_L_NO_FAIL
I_NO_CREATION_SESSION = CPLDirect.CPL_I_NO_CREATION_SESSION
I_NO_VERSION = CPLDirect.CPL_I_NO_VERSION
I_FAST = CPLDirect.CPL_I_FAST
A_NO_PREV_NEXT_VERSION = CPLDirect.CPL_A_NO_PREV_NEXT_VERSION
A_NO_DATA_DEPENDENCIES = (1 << 1)
A_NO_CONTROL_DEPENDENCIES = (1 << 2)
F_LOOKUP_ONLY = 0
F_ALWAYS_CREATE = CPLDirect.CPL_F_ALWAYS_CREATE
F_CREATE_IF_DOES_NOT_EXIST = CPLDirect.CPL_F_CREATE_IF_DOES_NOT_EXIST


#
# Private constants
#

__data_dict = ['data input', 'data ipc', 'data translation', 'data copy']
__control_dict = ['control op', 'control start']


#
# Global variables
#

_patricia_connection = None


#
# Private utility functions
#

def __getSignedNumber(number, bitLength):
	'''
	Print out a long value as a signed bitLength-sized integer.
	Thanks to:
	http://stackoverflow.com/questions/1375897/how-to-get-the-signed-integer-value-of-a-long-in-python
	for this function.
	'''
	mask = (2 ** bitLength) - 1
	if number & (1 << (bitLength - 1)):
		return number | ~mask
	else:
		return number & mask


def __patricia_id_t__eq__(self, other):
	'''
	Compare this and another ID, and return true if they are equal
	'''
	return self.lo == other.lo and self.hi == other.hi


def __patricia_id_t__ne__(self, other):
	'''
	Compare this and another ID, and return true if they are not equal
	'''
	return self.lo != other.lo  or self.hi != other.hi


def __patricia_id_t__str__(self):
	'''
	Create and return a string representation of this object
	'''
	return "%x:%x" % (self.hi, self.lo)

#
# Public utility functions
#
def current_connection():
	'''
	Return the current CPL connection object, or None if not connected
	'''
	global _patricia_connection
	return _patricia_connection


def dependency_type_to_str(val):
	'''
	Given a dependency (edge) type, convert it to a string

	Method calls::
		strval = dependency_type_to_str(val)
	'''
	which = val >> 8
	if which == DEPENDENCY_CATEGORY_DATA:
		if (val & 7) < len(__data_dict):
			return __data_dict[val & 7]
		else:
			return 'data unknown'
	elif which == DEPENDENCY_CATEGORY_CONTROL:
		if (val & 7) < len(__control_dict):
			return __control_dict[val & 7]
		else:
			return 'control unknown'
	elif which == DEPENDENCY_CATEGORY_VERSION:
		return 'version'
	else:
		return 'unknown'


def copy_id(idp):
	'''
	Construct a identifier.
	'''
	i = idp
	return i


def p_id(id, with_newline = False):
    print("id: " + str(id));

def p_object(obj, with_session = False):
	'''
	Print information about an object

	Method calls:
		p_object(obj, with_session = False)
	'''
	i = obj.info()
        #if i is None:
        #        return; 

	p_id(i.object.id)
	print(' version: ' + str(i.version))
	sys.stdout.write('container_id: ')
	if i.container is not None:
		p_id(i.container.object.id)
		print(' container version: ' + str(i.container.version))
	else:
		sys.stdout.write('none')
		print(' container version: none')
	print('originator: ' + i.originator + ' name:' + i.name +
	    ' type: ' + i.type)


def p_object_version(obj_ver, with_session = False):
	'''
	Print information about a version of an object

	Method calls:
		p_object_version(obj_ver, with_session = False)
	'''
	i = obj_ver.info()
	if with_session:
		print('creation_time: ' + str(i.creation_time))
		p_session(i.session)


def p_session(session):
	'''
	Print information about a session

	Method calls:
		p_session(session)
	'''
	#si = session.info()
	#sys.stdout.write('session ')
	#p_id(si.session.id, with_newline = True)
	#print(' mac_address: ' + si.mac_address + ' pid: ' + str(si.pid))
	#print('\t(' + str(si.start_time) + ')' + ' user: ' +
	#    si.user + ' cmdline: ' + si.cmdline + ' program: ' + si.program)



#
# Information about a specific version of a provenance object
#
class patricia_object_version_info:
	'''
	Information about a specific version of a provenance object
	'''

	def __init__(self, object_version, session, creation_time):
		'''
		Create an instance of this object
		'''

		self.object_version = object_version
		self.session = session
		self.creation_time = creation_time


class patricia_object_property:
        '''
        Information about a specific version of a provenance object
        '''

        def __init__(self, object, object_version, key, value):
                '''
                Create an instance of this object
                '''
                self.object = object
                self.object_version = object_version
                self.key = key
                self.value = value

        def json(self):
            return {'object': str(self.object),
                    'timestamp': self.object_version.version,
                    'key': self.key,
                    'value': self.value}

#
# Object & version
#
class patricia_object_version:
        '''
        Stores a reference to a provenance object and a version number
        '''

        def __init__(self, object, version):
                '''
                Create an instance of this object
                ''',
                self.object = object
                self.version = version


        def __eq__(self, other):
                '''
                Compare this and the other object, and return true if they are equal
                '''
                return self.object.id==other.object.id and self.version==other.version


        def __ne__(self, other):
                '''
                Compare this and the other object, and return true if they are not equal
                '''
                return self.object.id!=other.object.id or self.version!=other.version


        def __str__(self):
                '''
                Create and return a human-readable string representation of this object
                '''
                return "id:" + str(self.object) + ",version:" + str(self.version)

        def json(self, prefix=""):
                return {prefix + "_id": str(self.object),
                        prefix + "_version": str(self.version)}

        def jsons(self):
                return {"timestamp": self.version}

        def info(self):
                '''
                Return the corresponding cpl_object_version_info for this specific
                version of the object.
                '''
                # get object creation time 
                query_get_object = "SELECT * FROM object WHERE id={} ALLOW FILTERING;".format(str(self.object.id))
                query_res = _patricia_connection.session.execute(query_get_object);
                info = query_res._current_rows[0];

                _info = patricia_object_version_info(self, 0,
                                info.birthday)
                return _info

            
        def control_flow_to(self, dest, type=CONTROL_OP):
                '''
                Add a control flow edge of type from self to dest.
                '''
                return self.object.control_flow_to(dest, type, self.version)


        def data_flow_to(self, dest, type=DATA_INPUT):
                '''
                Add a data flow edge of type from self to dest.
                '''
                return self.object.data_flow_to(dest, type, self.version)

#
# Provenance ancestry entry
#
class patricia_ancestor:
        '''
        Stores the same data as a cpl_ancestry_entry_t, but in a Python
        class that we manage.
        '''
        def __init__(self, aid, aversion, did, dversion, type, direction):
		'''
		Create an instance of patricia_ancestor
		'''
		self.ancestor = patricia_object_version(patricia_object(aid), aversion)
		self.descendant = patricia_object_version(patricia_object(did), dversion)
		self.type = type


		if direction == D_ANCESTORS:
			self.base  = self.descendant
			self.other = self.ancestor
		else:
			self.base  = self.ancestor
			self.other = self.descendant


        def __str__(self):
		'''
		Create a printable string representation of this object
		'''
		arrow = ' -- '
		if self.other == self.ancestor:
			arrow = ' --> '
		else:
			arrow = ' <-- '
		return (str(self.base) + arrow + str(self.other) +
			' type:' + dependency_type_to_str(self.type))
                
        def json(self):
                '''
                Create a json format
                '''
                js = {'direction': '', 'type': dependency_type_to_str(int(self.type)), 'other_originator' : self.other.object.info().originator, 'other_name' : self.other.object.info().name,
                        'other_type' : self.other.object.info().type}
                js.update(self.base.json("base"))
                js.update(self.other.json("other"))

                arrow = ' -- '
                if self.other == self.ancestor:
                        arrow = ' --> '
                        js['direction'] = 'ancestor'
                else:
                        arrow = ' <-- '
                        js['direction'] = 'descendant'
                return js;

        def jsons(self, verbose=False):
                '''
                Create a json format
                '''
                if verbose:
                    js = {'direction': '', 'type': dependency_type_to_str(int(self.type)), 'other': {'originator' : self.other.object.info().originator, 'name' : self.other.object.info().name,
                        'type' : self.other.object.info().type, 'version': self.other.version}, 'base' : {'version': self.base.version}}
                else:
                    js = {'direction': '', 'type': dependency_type_to_str(int(self.type)), 'other': {'id': str(self.other.object), 'timestamp': self.other.version}, 'base' : {'timestamp': self.base.version}}

                arrow = ' -- '
                if self.other == self.ancestor:
                        arrow = ' --> '
                        js['direction'] = 'ancestors'
                else:
                        arrow = ' <-- '
                        js['direction'] = 'descendants'
                return js;
#
# CPL Connection
#

class patricia_connection:
	'''
	Core provenance library connection -- maintains state for the current
	session and the current database backend.
	'''
	def __init__(self, cstring="DSN=CPL;"):
		'''
		Constructor for CPL connection.

		** Parameters **
			** cstring **
			Connection string for database backend

		** Note **
		Currently the python bindings support only ODBC connection.
		RDF connector coming soon.
		'''
		global _patricia_connection

		self.connection_string = cstring
		self.closed = False

		def get_current_session():
                    if _patricia_connection == None:
                        #establish connection with Cassandra
                        cluster = Cluster()
                        session = cluster.connect()
                        session.execute('USE patricia_jaeger;');
                    return cluster, session;

		self.backend, self.session = get_current_session()

		_patricia_connection = self


	def __del__(self):
		'''
		Destructor - automatically closes the connection.
		'''
		if self == _patricia_connection and not self.closed:
			self.close()

        def close(self):
                '''
                Close database connection and session
                '''
                global _patricia_connection

                if self != _patricia_connection or self.closed:
                        return

                self.backend.shutdown();
                _patricia_connection = None
                self.closed = True

	def __create_or_lookup_cpl_object(self, originator,
		     name, otype, trace_id=None, span_id=None, creation_time=None, death_time=None, create=None, container=None):
		'''
		** Parameters **
			originator 
			name: originator-local name
			type: originator-local type
			create:
				None: lookup or create
				True: create only
				False: lookup only
			container:
				Id of container into which to place this object.
				Only applies to create
		'''
                if creation_time is None:
                        birthday = datetime.datetime.now();
                else:
                        birthday = creation_time;

		if container is None:
			container_id = 'null'
		else:
			container_id = container.id

                if death_time is None:
                        death_time = 0
                else:
                        death_time = death_time


                if otype == 'artifact':
                    o = {
                        "name": name,
                        "originator": originator,
                        "type": otype
                        }
                    idp = uuid.uuid3(uuid.NAMESPACE_DNS, str(o))
                else:
                    idp = uuid.uuid1();

		if create == None:
                    if trace_id and span_id:
                        query = """INSERT INTO object (id,parent_id,originator,name,type,birthday,deathtime,trace_id,span_id) VALUES ({}, {}, %s, %s, %s, %s, %s, %s, %s) IF NOT EXISTS; """.format(str(idp), str(container_id))
                        params = [originator, name, otype, birthday,death_time,bytearray(trace_id), span_id]
                    else:
                        query = """INSERT INTO object (id,parent_id,originator,name,type,birthday,deathtime) VALUES ({}, {}, %s, %s, %s, %s, %s) IF NOT EXISTS; """.format(str(idp), str(container_id))
                        params = [originator, name, otype, birthday, death_time]

                    print(query)
                    ret = self.session.execute(query, params);
                    if ret._current_rows[0].applied == False:
                        print("Object already inserted")
                        idp = ret._current_rows[0].id
		elif create:
                    query = """INSERT INTO object (id,parent_id,originator,name,type,birthday,deathtime,trace_id,span_id) VALUES ({},{}, %s, %s, %s, %s, %s, %s, %s); """.format(str(idp), str(container_id))
                    params = [originator, name, otype, birthday,death_time,bytearray(trace_id), span_id]
                    print(query)
                    ret = self.session.execute(query, params);
		else:
                    query = """SELECT * from object where originator='{}' and name='{}' and type='{}' ALLOW FILTERING;""".format(str(originator), str(name), str(otype));
                    print(query)
                    ret = self.session.execute(query);
                    if len(ret._current_rows) > 0:
                        idp = ret._current_rows[0].id
            
		r = patricia_object(idp)
                return r

        def __create_or_lookup_trace_object(self, trace_id, span_id, create=None):

                if create == None:
                    print('None')
                
                elif create:
                    print('None')
                else:
                    query = "SELECT * from object where trace_id= %s and span_id= %s ALLOW FILTERING;"
                    params = [bytearray(trace_id), span_id]
                    print(query)
                    ret = self.session.execute(query, params);
                    print(ret._current_rows)
                    if len(ret._current_rows) > 0:
                        idp = ret._current_rows[0].id
                        r = patricia_object(idp)
                        return r


	def get_all_objects(self, fast=False):
		'''
		Return all objects in the provenance database. If fast = True, then
		fetch only incomplete information about each object, so that it is
		faster.
		'''
                select_all_query = """SELECT * from object ALLOW FILTERING;""";
                query_res = self.session.execute(select_all_query);

                l = []
                if len(query_res._current_rows) <= 0:
                    print("No object found");
                    return l;

                for row in query_res._current_rows:
                    obj = patricia_object(row.id)
                    if row.parent_id == None:
                        container = None
                    else:
                        obj_container = patricia_object(row.parent_id)
                        obj_container_version = obj_container.version();
                        container = patricia_object_version(obj_container,
                                                        obj_container_version)
                    
                    l.append(patricia_object_info(object=obj, version=obj.version(),
                                        creation_session=0, creation_time = row.birthday, death_time=row.deathtime, originator=row.originator, name=row.name,
                                        type=row.type, container=container))

                    #print(l)
		return l
			

	def get_object(self, originator, name, type, container=None, creation_time=None):
		'''
		Get the object, with the designated originator (string),
		name (string), and type (string), creating it if necessary.

		If you want an object in a specific container, set the container
		parameter to the ID of the object in which you want this object
		created.
		'''
		return self.__create_or_lookup_cpl_object(originator, name, type,
				create=None, container=container, creation_time=creation_time)

        def get_trace_object(self, trace_id, span_id):
                '''
                Get the object, with the designated originator (string),
                name (string), and type (string), creating it if necessary.

                If you want an object in a specific container, set the container
                parameter to the ID of the object in which you want this object
                created.
                '''
                return self.__create_or_lookup_trace_object(trace_id, span_id, create=False)

	def create_object(self, originator, name, type, trace_id=None, span_id=None, creation_time=None, death_time=None, container=None):
		'''
		Create object, returns None if object already exists.
		'''
		return self.__create_or_lookup_cpl_object(originator, name, type, creation_time=creation_time,
				death_time=death_time, trace_id=trace_id, span_id=span_id, create=True, container=container)


	def lookup_object(self, originator, name, type):
		'''
		Look up object; raise LookupError if the object does not exist.
		'''
		o = self.__create_or_lookup_cpl_object(originator, name, type,
				create=False)
		return o


	def try_lookup_object(self, originator, name, type):
		'''
		Look up object; returns None if the object does not exist.
		'''
		try:
                    o = self.__create_or_lookup_cpl_object(originator, name, type,
                            create=False)
		except LookupError:
                    o = None
		return o


	def lookup_by_property(self, key, value):
		'''
		Return all objects that have the key/value property specified; raise
		LookupError if no such object is found.
		'''
                '''
                Return all objects that have the specified originator, name,
                and type (they might differ by container).
                '''
                select_all_query = """SELECT * from property where key='{}' and value='{}' ALLOW FILTERING;""".format(key, value);
                query_res = self.session.execute(select_all_query);

                l = []
                if len(query_res._current_rows) <= 0:
                    print("No object found");
                    return l;

                for row in query_res._current_rows:
                    obj = patricia_object(row.id)
                    l.append(obj)

                return l

	def try_lookup_by_property(self, key, value):
		'''
		Return all objects that have the key/value property specified, but do
		not fail if no such object is found -- return an empty list instead.
		'''
		try:
                    o = self.lookup_by_property(key, value)
		except LookupError:
                    o = []
		return o


	def lookup_all(self, originator, name, type):
		'''
		Return all objects that have the specified originator, name,
		and type (they might differ by container).
		'''
                select_all_query = """SELECT * from object where originator='{}' and name='{}' and type='{}' ALLOW FILTERING;""".format(originator, name, type);
                query_res = self.session.execute(select_all_query);

                l = []
                if len(query_res._current_rows) <= 0:
                    print("No object found");
                    return l;

                for row in query_res._current_rows:
                   obj = patricia_object(row.id)
                   l.append(obj)

		return l


        def lookup_by_id(self, id):
                '''
                Return the object that have the specific id.
                '''
                return patricia_object(id)

#
# Information about a provenance session
#
class cpl_session_info:
	'''
	Information about a provenance session
	'''

	def __init__(self, session, mac_address, user, pid, program, cmdline,
			start_time):
		'''
		Create an instance of this object
		'''
		self.session = session
		self.mac_address = mac_address
		self.user = user
		self.pid = pid
		self.program = program
		self.cmdline = cmdline
		self.start_time = start_time


class patricia_object_info:
        '''
        Information about a provenance object
        '''

        def __init__(self, object, version, creation_session, creation_time,
                        originator, name, type, container,death_time):
                '''
                Create an instance of this object
                '''

                self.object = object
                self.version = version
                self.creation_time = creation_time
                self.death_time = death_time
                self.originator = originator
                self.name = name
                self.type = type
                self.container = container

        def json(self):
            f = lambda parent : parent.object if parent else 'null'
            return {'id': str(self.object),
                    'name': self.name, 
                    'type': self.type, 
                    'originator': self.originator,
                    'creation_time': self.creation_time,
                    'death_time': self.death_time,
                    'timestamp': self.version,
                    'parent' : str(f(self.container))
                    };


class patricia_object:
        '''
        CPL Provenance object
        '''


        def __init__(self, id):
                '''
                Create a new instance of a provenance object from its internal ID
                '''
                self.id = copy_id(id)


        def __eq__(self, other):
                '''
                Compare this and the other object and return true if they are equal
                '''
                return self.id == other.id


        def __ne__(self, other):
                '''
                Compare this and the other object and return true if they are not equal
                '''
                return self.id != other.id


        def __str__(self):
                '''
                Return a string representation of this object
                '''
                return str(self.id)

        def update_birthday(self, birthday):
            query = """UPDATE object SET birthday = {} WHERE id = {};""".format(birthday, str(self.id))
            query_res = _patricia_connection.session.execute(query);

        def add_parent(self, parent):
            query = """UPDATE object SET parent_id = {} WHERE id = {};""".format(str(parent.id), str(self.id))
            query_res = _patricia_connection.session.execute(query);
            
        
        def version(self):
                '''
                Determine the current version of this provenance object
                '''
                query_object_version = "SELECT MAX(ts) FROM flow WHERE id_c={} ALLOW FILTERING;".format(str(self.id))
                query_res = _patricia_connection.session.execute(query_object_version);
                
                version = query_res._current_rows[0].system_max_ts;
                if version == None:
                     # query Cassandra to get the entry from object table with object id
                    query_get_object = "SELECT * FROM object WHERE id={} ALLOW FILTERING;".format(str(self.id))
                    query_res = _patricia_connection.session.execute(query_get_object);
                    if len(query_res._current_rows) <= 0:
                        return 0;

                    object = query_res._current_rows[0];
                    version = object.birthday;
                
                return version;
        

        def current_version(self):
                '''
                Get a cpl_object_version object for the current version.
                '''
                return patricia_object_version(self, self.version())


        def specific_version_index(self, v):
                '''
                Get a cpl_object_version object for the specified version. Note that
                the specified version number does not get validated until info() is
                called.
                '''
                # query Cassandra to get the entry from object table with object id
                query_get_object = "SELECT ts FROM flow WHERE id_c={} ALLOW FILTERING;".format(self.id)
                query_res = _patricia_connection.session.execute(query_get_object);
                if len(query_res._current_rows) <= 0:
                        return 0;

                versions = [row.ts for row in query_res._current_rows]
                version = v; 
                if v < len(versions):
                    version = versions[v];

                return patricia_object_version(self, version)

        def get_all_versions(self, v=None):
                '''
                Get a cpl_object_version object for the specified version. Note that
                the specified version number does not get validated until info() is
                called.
                '''
                if v == None:
                    v = self.version();

                # query Cassandra to get the entry from object table with object id
                query_get_object = "SELECT ts FROM flow WHERE id_c={} and ts<={} ALLOW FILTERING;".format(self.id, v)
                query_res = _patricia_connection.session.execute(query_get_object);
                
                versions = []
                versions.append(patricia_object_version(self, long(self.info().creation_time)))
                
                for row in query_res._current_rows:
                    if long(self.info().creation_time) != long(row.ts):
                        versions.append(patricia_object_version(self, long(row.ts)))

                    
                return versions;
        
        
        def specific_version(self, v):
                '''
                Get a cpl_object_version object for the specified version. Note that
                the specified version number does not get validated until info() is
                called.
                '''
                # query Cassandra to get the entry from object table with object id
                query_get_object = "SELECT * FROM flow WHERE id_c={} and ts<{} ALLOW FILTERING;".format(self.id, v)
                query_res = _patricia_connection.session.execute(query_get_object);
                
                if len(query_res._current_rows) <= 0:
                     # query Cassandra to get the entry from object table with object id
                    query_get_object = "SELECT * FROM object WHERE id={} ALLOW FILTERING;".format(str(self.id))
                    query_res = _patricia_connection.session.execute(query_get_object);
                    if len(query_res._current_rows) <= 0:
                        return 0;

                    object = query_res._current_rows[0];
                    version = object.birthday;
                else:
                    versionings = [[row.id_c, row.ts] for row in query_res._current_rows]
                    versionings.sort(key = lambda x: x[1])
                    version = versionings[-1][1];
               
                return patricia_object_version(self, version)


        def last_version_before(self, v):
                '''
                Get a cpl_object_version object for the specified version. Note that
                the specified version number does not get validated until info() is
                called.
                '''
                # query Cassandra to get the entry from object table with object id
                query_get_object = "SELECT * FROM flow WHERE id_c={} and ts<{} ALLOW FILTERING;".format(self.id, v)
                query_res = _patricia_connection.session.execute(query_get_object);

                if len(query_res._current_rows) <= 0:
                     # query Cassandra to get the entry from object table with object id
                    query_get_object = "SELECT * FROM object WHERE id={} ALLOW FILTERING;".format(str(self.id))
                    query_res = _patricia_connection.session.execute(query_get_object);
                    if len(query_res._current_rows) <= 0:
                        return 0;

                    object = query_res._current_rows[0];
                    version = unix_time_millis(object.birthday);
                else:
                    versionings = [[row.id_c, row.ts] for row in query_res._current_rows]
                    versionings.sort(key = lambda x: x[1])
                    version = versionings[-1][1];

                return patricia_object_version(self, version)


        def info(self):
                '''
                Return cpl_object_info_t corresponding to the current object.
                '''
                # query Cassandra to get the entry from object table with object id
                query_get_object = "SELECT * FROM object WHERE id={} ALLOW FILTERING;".format(str(self.id))
                query_res = _patricia_connection.session.execute(query_get_object);
                if len(query_res._current_rows) <= 0:
                        return 0;
                
                object = query_res._current_rows[0];
                version = self.version();
                if version == 0: 
                    version = object.birthday;

                # get container version number 
                if object.parent_id == None:
                    container = None
                else:
                    container_obj = patricia_object(object.parent_id);
                    container_version = container_obj.version();
                    container = patricia_object_version(container_obj,
                            container_version)

                # create an object_info object 
                _info = patricia_object_info(object=self, version=version,
                                creation_session=0, creation_time=object.birthday,
                                originator=str(object.originator), name=str(object.name), type=str(object.type), container=container, death_time=object.deathtime)

                return _info

        # I guess I totally ignored the concept of versioning here. 
        def control_flow_to(self, dest, type=CONTROL_OP, timestamp=None):
                '''
                Add control flow edge of type from self to dest. If version
                is specified, then add flow to dest with explicit version,
                else add to most recent version.

                Allowed types:
                        CPL.CONTROL_OP (default)
                        CPL.CONTROL_START

                CPL.CONTROL_GENERIC is an alias for CPL.CONTROL_OP.
                '''
                #inset into flow table with self.id, dest.id, timestamp, type
                if timestamp is None:
                    timestamp = long(round(time.time() * 1000)) 
               
                query = """INSERT INTO flow (id_p,id_c,type,event,ts) VALUES ({}, {}, '{}', '{}',{});""".format(self.id, dest.id, type, None, timestamp);
                print(query)
                ret = _patricia_connection.session.execute(query);
 
                return True;


        def data_flow_to(self, dest, type=DATA_INPUT, timestamp=None):
                '''
                Add data flow edge of type from self to dest. If version
                is specified, then add flow to dest with explicit version,
                else add to most recent version.

                Allowed types:
                        CPL.DATA_INPUT (default)
                        CPL.DATA_IPC
                        CPL.DATA_TRANSLATION
                        CPL.DATA_COPY

                CPL.DATA_GENERIC is an alias for CPL.DATA_INPUT.
                '''
                #inset into flow table with self.id, dest.id, timestamp, type
                if timestamp is None:
                    timestamp = long(round(time.time() * 1000))

                query = """INSERT INTO flow (id_p,id_c,type,event,ts) VALUES ({}, {}, '{}', '{}',{});""".format(self.id, dest.id, type, None, timestamp);
                ret = _patricia_connection.session.execute(query);
                return True;



        def control_flow_from(self, src, type=CONTROL_OP, timestamp=None):
                '''
                Add control flow edge of the given type from src to self. If version
                is specified, then add flow to dest with explicit version, else add
                to most recent version.

                Allowed types:
                        CPL.CONTROL_OP (default)
                        CPL.CONTROL_START

                CPL.CONTROL_GENERIC is an alias for CPL.CONTROL_OP.
                '''
                #inset into flow table with self.id, dest.id, timestamp, type
                #if version is None:
                #    version = self.version()
                if timestamp is None:
                    timestamp = long(round(time.time() * 1000))

                query = """INSERT INTO flow (id_p,id_c,type,event,ts) VALUES ({}, {}, '{}', '{}', {});""".format(src.id, self.id, type, None, timestamp);
                print(query)
                ret = _patricia_connection.session.execute(query);
                return True;


        def data_flow_from(self, src, type=DATA_INPUT, timestamp=None):
                '''
                Add data flow edge of the given type from src to self. If version
                is specified, then add flow to dest with explicit version, else add
                to most recent version.

                Allowed types:
                        CPL.DATA_INPUT (default)
                        CPL.DATA_IPC
                        CPL.DATA_TRANSLATION
                        CPL.DATA_COPY

                CPL.DATA_GENERIC is an alias for CPL.DATA_INPUT.
                '''
                if timestamp is None:
                    timestamp = long(round(time.time() * 1000))

                query = """INSERT INTO flow (id_p,id_c,type,event,ts) VALUES ({}, {}, '{}', '{}',{});""".format(src.id, self.id, type, None, timestamp);
                ret = _patricia_connection.session.execute(query);
                return True;

#        def has_ancestor(self, other):
#                '''
#                Return True if the other object is an ancestor of the object.
#                '''
#                ancestors = self.ancestry()
#                for a in ancestors:
#                        if a.ancestor.object == other:
#                                return True
#                return False

	
	def ancestry(self, version=None, direction=D_ANCESTORS, flags=0):
		'''
		Return a list of cpl_ancestor objects
		'''
                if version is None:
                    version = self.version();

                l = []
                if direction == D_ANCESTORS:
                     select_ancestry_query = """SELECT * from flow where id_c={} and ts<={} and ts>={} ALLOW FILTERING;""".format(self.id, str(version), str(self.specific_version(version).version));
                     query_res = _patricia_connection.session.execute(select_ancestry_query);
                     if len(query_res._current_rows) <= 0:
                        return l;
               
                     query_res._current_rows.sort(key=lambda tr: tr.ts) 
                     self_last_version_entry = max(query_res._current_rows, key=lambda row:row.ts)
                     print(self_last_version_entry)
                     parent = patricia_object(self_last_version_entry.id_p);
                     category_type = get_dependency_category(int(self_last_version_entry.type))
                     if category_type == DEPENDENCY_CATEGORY_DATA and (flags & A_NO_DATA_DEPENDENCIES) != 0:
                         print("Do not add entry")
                     elif category_type == DEPENDENCY_CATEGORY_CONTROL and (flags & A_NO_CONTROL_DEPENDENCIES) != 0:
                         print ("Do not add entry")
                     elif self_last_version_entry.id_c != self_last_version_entry.id_p:

                         a = patricia_ancestor(parent.id, parent.specific_version(self_last_version_entry.ts).version,
                             self.id, self_last_version_entry.ts,
                             self_last_version_entry.type, direction)
                         l.append(a)


                     
                     query_res._current_rows.remove(self_last_version_entry)

                     if len(query_res._current_rows) <= 0:
                         return l;

                     ancestry_entry = max(query_res._current_rows, key=lambda row:row.ts)
                     category_type = get_dependency_category(int(ancestry_entry.type))
                     if category_type == DEPENDENCY_CATEGORY_DATA and (flags & A_NO_DATA_DEPENDENCIES) != 0:
                         print("Do not add entry")
                     elif category_type == DEPENDENCY_CATEGORY_CONTROL and (flags & A_NO_CONTROL_DEPENDENCIES) != 0:
                         print ("Do not add entry")
                     else :
                         a = patricia_ancestor(self.id, ancestry_entry.ts, self.id, self_last_version_entry.ts, 
                             ancestry_entry.type, direction)
                         l.append(a)
                 
                else:
                    select_ancestry_query = """SELECT id_p, type, MIN(ts) from flow where id_c={} and ts>{} ALLOW FILTERING;""".format(self.id, version);
                    query_res = _patricia_connection.session.execute(select_ancestry_query);

                    if len(query_res._current_rows) > 0:
                        self_descendant_version = query_res._current_rows[0].system_min_ts;
                        self_type = query_res._current_rows[0].type;
                        id_p = query_res._current_rows[0].id_p;
                        
                        if self_descendant_version != None and version != self_descendant_version:
                            a = patricia_ancestor(self.id, version,
                                    self.id, self_descendant_version,
                                    self_type, direction)
                            l.append(a)
                           

                    if self_descendant_version:
                        select_ancestry_query = """SELECT * from flow where id_p={} and ts>={} and ts<{} ALLOW FILTERING;""".format(self.id, version, self_descendant_version);
                        query_res = _patricia_connection.session.execute(select_ancestry_query);
                    else:
                        select_ancestry_query = """SELECT * from flow where id_p={} and ts>={} ALLOW FILTERING;""".format(self.id, version);
                        query_res = _patricia_connection.session.execute(select_ancestry_query);
                            
                    if len(query_res._current_rows) <= 0:
                        return l;

                    for row in query_res._current_rows:
                        category_type = get_dependency_category(int(row.type))
                        if row.id_p == row.id_c:
                            print("Do not add entry")
                        elif category_type == DEPENDENCY_CATEGORY_DATA and (flags & A_NO_DATA_DEPENDENCIES) != 0:
                            print("Do not add entry")
                        elif category_type == DEPENDENCY_CATEGORY_CONTROL and (flags & A_NO_CONTROL_DEPENDENCIES) != 0:
                            print ("Do not add entry")
                        else :
                            a = patricia_ancestor(self.id, version,
                                    row.id_c, row.ts,
                                    int(row.type), direction)
                            l.append(a)

                return l

        
        def add_property(self, name, value):
                '''
                Add name/value pair as a property to current object.
                '''
                query = """INSERT INTO property (id,version,key,value,ts) VALUES ({}, {}, '{}', '{}', {});""".format(self.id, self.version(), str(name), value, unix_time_millis(datetime.datetime.now()));
                ret = _patricia_connection.session.execute(query);
                return 0;


	def properties(self, key=None, version=None):
                if version is None:
                    version = self.version()

                if key is None or key == '':
                    select_all_query = """SELECT * from property where id={} and version={};""".format(self.id, version.version);
                else:
                    select_all_query = """SELECT * from property where id={} and key='{}' and version={};""".format(self.id, key, version.version);
                
                query_res = _patricia_connection.session.execute(select_all_query);

                l = []
                if len(query_res._current_rows) <= 0:
                    return l;
                
                for row in query_res._current_rows:
                    p = patricia_object_property(self, version,
                                    row.key, row.value)
                    l.append(p)
                
                return l
