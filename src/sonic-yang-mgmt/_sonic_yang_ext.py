# This script is used as extension of sonic_yang class. It has methods of
# class sonic_yang. A separate file is used to avoid a single large file.

import yang as ly
import re
import pprint

from json import dump, load, dumps, loads
from xmltodict import parse
from os import listdir, walk, path
from os.path import isfile, join, splitext
from glob import glob

# class sonic_yang methods

"""
load_data: load Config DB, crop, xlate and create data tree from it.
input:    data
returns:  True - success   False - failed
"""
def load_data(self, configdbJson):

   try:
      self.jIn = configdbJson
      # reset xlate
      ## self.xlateJson = dict()
      # self.jIn will be cropped
      self.cropConfigDB("cropped.json")
      # xlated result will be in self.xlateJson
      ## self.xlateConfigDB("xlateYang.json")
      #print(self.xlateJson)
      #self.root = self.ctx.parse_data_mem(dumps(self.xlateJson), \
        #            ly.LYD_JSON, ly.LYD_OPT_CONFIG|ly.LYD_OPT_STRICT)

   except Exception as e:
       self.root = None
       print("Data Loading Failed")
       raise e

   return True

"""
load all YANG models, create JSON of yang models
"""
def loadYangModel(self):

    try:
        yangDir = self.yang_dir
        self.yangFiles = glob(yangDir +"/*.yang")
        for file in self.yangFiles:
            if (self.load_schema_module(file) == False):
                return False

        # keep only modules name in self.yangFiles
        self.yangFiles = [f.split('/')[-1] for f in self.yangFiles]
        self.yangFiles = [f.split('.')[0] for f in self.yangFiles]
        print(self.yangFiles)

        # load json for each yang model
        self.loadJsonYangModel()
        # create a map from config DB table to yang container
        self.createDBTableToModuleMap()

    except Exception as e:
        print("Yang Models Load failed")
        raise e

    return True

"""
load JSON schema format from yang models
"""
def loadJsonYangModel(self):

    for f in self.yangFiles:
        m = self.ctx.get_module(f)
        if m is not None:
            xml = m.print_mem(ly.LYD_JSON, ly.LYP_FORMAT)
            self.yJson.append(parse(xml))

    return

"""
Create a map from config DB tables to container in yang model
"""
def createDBTableToModuleMap(self):

    for j in self.yJson:
        # get module name
        moduleName = j['module']['@name']
        if "sonic-head" in moduleName or "sonic-common" in moduleName:
            continue;
        # get all top level container
        topLevelContainer = j['module']['container']
        if topLevelContainer is None:
            raise Exception("topLevelContainer not found")

        assert topLevelContainer['@name'] == moduleName

        container = topLevelContainer['container']
        # container is a list
        if isinstance(container, list):
            for c in container:
                self.confDbYangMap[c['@name']] = {
                    "module" : moduleName,
                    "topLevelContainer": topLevelContainer['@name'],
                    "container": c
                    }
        # container is a dict
        else:
            self.confDbYangMap[container['@name']] = {
                "module" : moduleName,
                "topLevelContainer": topLevelContainer['@name'],
                "container": container
                }
    return

"""
Get module, topLevelContainer and json container for a config DB table
"""
def get_module_top_container(self, table):
    cmap = self.confDbYangMap
    m = cmap[table]['module']
    t = cmap[table]['topLevelContainer']
    c = cmap[table]['container']
    return m, t, c

"""
Crop config as per yang models
"""
def cropConfigDB(self, croppedFile=None):

    for table in self.jIn.keys():
        if table not in self.confDbYangMap:
            del self.jIn[table]

    if croppedFile:
        with open(croppedFile, 'w') as f:
            dump(self.jIn, f, indent=4)

    return

"""
Delete a node from data tree, if this is LEAF and KEY Delete the Parent
"""
def delete_node(self, xpath):

    # These MACROS used only here, can we get it from Libyang Header ?
    LYS_LEAF = 4
    node = self.find_data_node(xpath)
    if node is None:
        return False

    snode = node.schema()
    # check for a leaf if it is a key. If yes delete the parent
    if (snode.nodetype() == LYS_LEAF):
        leaf = ly.Schema_Node_Leaf(snode)
        if leaf.is_key():
            # try to delete parent
            nodeP = self.find_parent_node(xpath)
            xpathP = nodeP.path()
            return self._delete_node(xpath=xpathP, node=nodeP)
    else:
        return self._delete_node(xpath=xpath, node=node)

    return True

# End of class sonic_yang
