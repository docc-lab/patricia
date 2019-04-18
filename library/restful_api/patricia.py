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
    print(cpl_str)
    c.close()
    return cpl_str.replace("\"", "");

def getSpecificVersion(originator, name, otype, version):
    print("\tget specific version: for object: originator:" + str(originator) + ", name:" + str(name)  + ", type:" +  str(otype)  + ", version:" +  str(version) )
    c = Patricia.patricia_connection()
    
    #get object
    obj = c.lookup_object(str(originator), str(name), str(otype))
    if obj is None:
        print("\t\tobject: originator:" + str(originator) + ", name:" + str(name)  + ", type:" +  str(otype) + " not found")

    version = obj.specific_version(version)
    cpl_str = json.dumps({'timestamp':str(version)})
    c.close()
    return cpl_str.replace("\"", "")


def getAllVersions(originator, name, otype, version):
    print("\tgetAllVersions for object: originator:" + str(originator) + ", name:" + str(name)  + ", type:" +  str(otype) + " where version is:"  + str(version));
    c = Patricia.patricia_connection()
    obj = c.lookup_object(str(originator), str(name), str(otype))
    if obj is None:
        print("\t\tobject: originator:" + str(originator) + ", name:" + str(name)  + ", type:" +  str(otype) + " not found")

    pat_lineage = obj.get_all_versions(long(str(version)));

    lineage = []
    for pl in pat_lineage:
        lineage.append({'originator': str(originator), 'name' : str(name), 'type' : str(otype), 'id': str(obj.id), 'ct': str(obj.info().creation_time), 'timestamp':str(pl.version)})

    cpl_str = json.dumps(lineage)
    print(cpl_str)
    c.close()
    return cpl_str.replace("\"", "")

def getVersion(originator, name, otype):
    print("\tget version: for object: originator:" + str(originator) + ", name:" + str(name)  + ", type:" +  str(otype) )
    c = Patricia.patricia_connection()
    obj = c.lookup_object(str(originator), str(name), str(otype))
    if obj is None:
        print("\t\tobject: originator:" + str(originator) + ", name:" + str(name)  + ", type:" +  str(otype) + " not found")
    version = 0; 
    
    version = obj.info().version

    cpl_str = json.dumps({'timestamp':str(version)})
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
    print(cpl_str)
    c.close()
    return cpl_str.replace("\"", "")



def lookup(originator, name, otype):
    c = Patricia.patricia_connection()

    obj_ls = c.lookup_all(str(originator), str(name), str(otype))

    objs = []
    for obj in obj_ls:
        objs.append({'originator': str(originator), 'name' : str(name), 'type' : str(otype), 'id': str(obj.id), 'ct': str(Patricia.unix_time_millis(obj.info().creation_time)), 'timestamp':str(obj.version())})

    cpl_str = json.dumps(objs)
    print(cpl_str)
    c.close()
    return cpl_str.replace("\"", "");

def lookupbyid(id):
    c = Patricia.patricia_connection()
    obj = c.lookup_by_id(str(id))
    obj_info = obj.info();
    cpl_str = json.dumps([{'originator': obj_info.originator, 'name' : obj_info.name, 'type' : obj_info.type, 'id': str(obj.id), 'ct': str(obj.info().creation_time), 'timestamp':str(obj.version())}]);
    print(cpl_str)
    c.close()
    return cpl_str.replace("\"", "");

def read(originator, name, otype):
    c = Patricia.patricia_connection()
    
    obj_ls = c.lookup_all(str(originator), str(name), str(otype))
    
    objs = []
    for obj in obj_ls:
        objs.append({'originator': str(originator), 'name' : str(name), 'type' : str(otype), 'id': str(obj.id), 'ct': str(obj.info().creation_time), 'timestamp':str(obj.version())})
                
    cpl_str = json.dumps(objs)
    print(cpl_str) 
    c.close()
    return cpl_str.replace("\"", "");


def getAllObjectsJson(dump_file_path):
    c = Patricia.patricia_connection()

    obj_ls = c.get_all_objects()
    objs = []
    for o in obj_ls:
        obj = {'info' : {},
                'timestamps': [],
                'properties': [],
                'ancestors': [],
                'descendant': []};

        obj['info'] = o.json();
        
        obj_versions = o.object.get_all_versions();
        print(obj['info'])
        for v in obj_versions:
            print(v.jsons())
            obj['timestamps'].append(v.jsons())
            obj_properties = o.object.properties(version=v);
            for p in obj_properties:
                obj['properties'].append(p.json())

        print('\n')
        obj_ancestors = o.object.ancestry(direction = Patricia.D_ANCESTORS);
        for a in obj_ancestors:
            obj['ancestors'].append(a.jsons())

        obj_decendant = o.object.ancestry(direction = Patricia.D_DESCENDANTS);
        for d in obj_decendant:
            obj['descendant'].append(d.jsons())
        
        objs.append(obj)
    
    with open(dump_file_path, 'w') as outfile:
        json.dump(objs, outfile, indent=4)

    c.close()
    return
