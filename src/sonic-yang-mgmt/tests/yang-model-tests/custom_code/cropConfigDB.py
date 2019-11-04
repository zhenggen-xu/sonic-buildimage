# This script is used to

import yang as ly

from json import dump, load, dumps, loads
from xmltodict import parse
from os import listdir, walk, path
from os.path import isfile, join, splitext

# Read given JSON file
def readJsonFile(fileName):
    #print(fileName)
    try:
        with open(fileName) as f:
            result = load(f)
    except Exception as e:
        raise Exception(e)

    return result

class sonic_yang:

    def __init__(self, yangDir):
        self.yangDir = yangDir
        self.ctx = None;
        self.yangFiles = list()
        self.confDbYangMap = dict()
        self.yJson = list()

        return

    """
        load all YANG models before test run
    """
    def loadYangModel(self):

        yangDir = self.yangDir
        # get all files
        yangFiles = [f for f in listdir(yangDir) if isfile(join(yangDir, f))]
        # get all yang files
        yangFiles = [f for f in yangFiles if splitext(f)[-1].lower()==".yang"]
        yangFiles = [f.split('.')[0] for f in yangFiles]
        # load yang mdoules
        self.ctx = ly.Context(yangDir)
        self.yangFiles = yangFiles
        print(yangFiles)
        for f in yangFiles:
            # load a module
            m = self.ctx.get_module(f)
            if m is not None:
                print("module already exist: {}".format(m.name()))
            else:
                m = self.ctx.load_module(f)
                if m is not None:
                    print("module: {} is loaded successfully".format(m.name()))
                else:
                    print("module not loaded correctly: {}".format(m.name()))
                    return

        return

    """
        load JSON schema format from yang models
    """
    def loadJsonYangModels(self):

        for f in self.yangFiles:
            m = self.ctx.get_module(f)
            if m is not None:
                xml = m.print_mem(ly.LYD_JSON, ly.LYP_FORMAT)
                self.yJson.append(parse(xml))

        return

    """
        Create a map from config DB tables to
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
                    self.confDbYangMap[c['@name']] = \
                        "/"+moduleName+":"+topLevelContainer['@name']+"/"+c['@name']
            # container is a dict
            else:
                self.confDbYangMap[container['@name']] = \
                    "/"+moduleName+":"+topLevelContainer['@name']+"/"+container['@name']

        return

    """
        Read config file and crop it as per yang models
    """
    def cropConfigDB(self, configFile, croppedFile):

        jIn = readJsonFile(configFile)
        for table in jIn.keys():
            if table not in self.confDbYangMap:
                del jIn[table]

        with open(croppedFile, 'w') as f:
            dump(jIn, f, indent=2)

        return

# end of class

def main():
    configFile = "sample_config_db.json"
    croppedFile = "cropped_" + configFile

    sy = sonic_yang("../../../yang-models")
    sy.loadYangModel()
    sy.loadJsonYangModels()
    sy.createDBTableToModuleMap()
    sy.cropConfigDB(configFile, croppedFile)

if __name__ == "__main__":
    main()
