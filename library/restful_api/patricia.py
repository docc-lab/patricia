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
sys.path.insert(0, "/home/maniaa/core-provenance-library-1.01/bindings/python/CPL/build/release/")
sys.path.insert(0, "/home/maniaa/patricia/library/core/")

import pprint
pp = pprint.PrettyPrinter(indent=4)

# 3rd party modules
import CPL
import Patricia

import json


def ancestry(originator, name, otype, version, direction, flags):
    print("Ancestry for object: originator:" + str(originator) + ", name:" + str(name)  + ", type:" +  str(otype)) 
    c = Patricia.patricia_connection()

    obj_ls = c.lookup_all(str(originator), str(name), str(otype))
    if len(obj_ls) <= 0:
        print("object: originator:" + str(originator) + ", name:" + str(name)  + ", type:" +  str(otype) + " not found")


    objs = []
    for obj in obj_ls:
        ancestry = obj.ancestry(long(version), int(direction), int(flags));
        print("\tNumber of ancestors:" + str(len(ancestry)))
        for anc in ancestry:
            objs.append(anc.json())
        
    cpl_str = json.dumps(objs)
    print("\tancestry string: " + cpl_str);
    c.close()
    return cpl_str.replace("\"", "");

def getSpecificVersion(originator, name, otype):
    c = Patricia.patricia_connection()
    
    #get object
    obj_ls = c.lookup_all(str(originator), str(name), str(otype))

    # return version 

    #print(objs)
    cpl_str = json.dumps(objs)
    print("\tspecific version: " + cpl_str)
    c.close()
    return cpl_str.replace("\"", "")


def getAllVersions(originator, name, otype, version):
    c = Patricia.patricia_connection()
    obj = c.lookup_object(str(originator), str(name), str(otype))

    print("getAllVersions for object: originator:" + str(originator) + ", name:" + str(name)  + ", type:" +  str(otype) + " where version is:"  + str(version));
    pat_lineage = obj.get_all_versions(long(str(version)));

    lineage = []
    for pl in pat_lineage:
        lineage.append({'originator': str(originator), 'name' : str(name), 'type' : str(otype), 'id': str(obj.id), 'ct': str(obj.info().creation_time), 'version':str(pl.version)})

    cpl_str = json.dumps(lineage)
    print("getAllVersion" + cpl_str)
    c.close()
    return cpl_str.replace("\"", "")

def getVersion(originator, name, otype):
    c = Patricia.patricia_connection()
    obj = c.lookup_object(str(originator), str(name), str(otype))
    version = 0; 
    
    print (str(originator) + ", "  +  str(name) + ", " + str(otype))
    version = obj.info().version

    cpl_str = json.dumps({'version':str(version)})
    print(cpl_str)
    c.close()
    return cpl_str.replace("\"", "")


def getProperty(originator, name, otype, key, version):
    c = Patricia.patricia_connection()
    obj = c.lookup_object(str(originator), str(name), str(otype))

    prop = obj.properties(key, int(version));
    print(prop)

    prop_list = []
    for p in prop:
        prop_list.append({'originator': str(originator), 'name' : str(name), 'type' : str(otype), 'key': str(p[0]), 'value': str(p[1])})
    cpl_str = json.dumps(prop_list)
    print("property is: " + cpl_str)
    c.close()
    return cpl_str.replace("\"", "")



def lookup(originator, name, otype):
    c = Patricia.patricia_connection()

    obj_ls = c.lookup_all(str(originator), str(name), str(otype))

    objs = []
    for obj in obj_ls:
        objs.append({'originator': str(originator), 'name' : str(name), 'type' : str(otype), 'id': str(obj.id), 'ct': str(Patricia.unix_time_millis(obj.info().creation_time)), 'version':str(obj.version())})

    cpl_str = json.dumps(objs)
    print(cpl_str)
    c.close()
    return cpl_str.replace("\"", "");

def lookupbyid(id):
    c = Patricia.patricia_connection()
    obj = c.lookup_by_id(str(id))
    obj_info = obj.info();
    cpl_str = json.dumps([{'originator': obj_info.originator, 'name' : obj_info.name, 'type' : obj_info.type, 'id': str(obj.id), 'ct': str(Patricia.unix_time_millis(obj.info().creation_time)), 'version':str(obj.version())}]);
    print(cpl_str)
    c.close()
    return cpl_str.replace("\"", "");

def read(originator, name, otype):
    c = Patricia.patricia_connection()
    
    obj_ls = c.lookup_all(str(originator), str(name), str(otype))
    
    objs = []
    for obj in obj_ls:
        objs.append({'originator': str(originator), 'name' : str(name), 'type' : str(otype), 'id': str(obj.id), 'ct': str(Patricia.unix_time_millis(obj.info().creation_time)), 'version':str(obj.version())})
                
    cpl_str = json.dumps(objs)
    print(cpl_str) 
    c.close()
    return cpl_str.replace("\"", "");


def getAllObjectsJson():
    c = Patricia.patricia_connection()

    obj_ls = c.get_all_objects()
    objs = []
    for o in obj_ls:
        obj = {'info' : {},
                'versions': [],
                'properties': [],
                'ancestors': [],
                'descendant': []};

        obj['info'] = o.json();

        obj_versions = o.object.get_all_versions();
        for v in obj_versions:
            obj['versions'].append(v.jsons())
            obj_properties = o.object.properties(version=v);
            for p in obj_properties:
                obj['properties'].append(p.json())

        obj_ancestors = o.object.ancestry(direction = Patricia.D_ANCESTORS);
        for a in obj_ancestors:
            obj['ancestors'].append(a.jsons())

        obj_decendant = o.object.ancestry(direction = Patricia.D_DESCENDANTS);
        for d in obj_decendant:
            obj['descendant'].append(d.jsons())

        objs.append(obj)


    cpl_str = json.dumps(objs, indent=4)
    print(cpl_str)
    c.close()
    return cpl_str.replace("\"", "");
