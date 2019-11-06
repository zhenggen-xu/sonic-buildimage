import sys
import os
import pytest
from unittest import TestCase
import yang as ly
import sonic_yang as sy
import json
import getopt
import subprocess

test_path = os.path.dirname(os.path.abspath(__file__))
modules_path = os.path.dirname(test_path)
sys.path.insert(0, modules_path)

class Test_SonicYang(object):
    @pytest.fixture(autouse=True, scope='class')
    def data(self):
        test_file = "/sonic/src/sonic-yang-mgmt/tests/libyang-python-tests/test_SonicYang.json"
        data = self.jsonTestParser(test_file)
        return data

    @pytest.fixture(autouse=True, scope='class')
    def yang_s(self, data):
        yang_dir = str(data['yang_dir'])
        data_file = str(data['data_file'])
        yang_s = sy.sonic_yang(yang_dir)
        yang_s.load_schema_modules(yang_dir)

        root = yang_s.load_data_file(data_file)
        return yang_s

    def jsonTestParser(self, file):
        """
        Open the json test file
        """
        with open(file) as data_file:
            data = json.load(data_file)
        return data

    def setup_class(cls):
        pass

    def load_yang_model_file(self, yang_s, yang_dir, yang_file, module_name):
        yfile=yang_dir+yang_file
        module = yang_s.load_schema_module(yfile)

        if (module is None):
            print("Module is None")
            return False

        if (yang_s.get_module(module_name) is None):
            print("get Module is None")
            return False
        else:
            return True

    #test load and get yang module
    def test_load_yang_model_files(self, data, yang_s):
        yang_dir = data['yang_dir']
        for module in data['modules']:
            file = str(module['file'])
            status = self.load_yang_model_file(yang_s, yang_dir, file, str(module['module']))
            assert status == True

    #test load yang modules in directory
    def test_load_yang_model_dir(self, data, yang_s):
        yang_dir = data['yang_dir']
        yang_s.load_schema_modules(str(yang_dir))

        for module_name in data['modules']:
            print(module_name['module'])
            assert yang_s.get_module(str(module_name['module'])) is not None

    #test_validate_data_tree():
    def test_validate_data_tree(self, data, yang_s):
        assert yang_s.validate_data_tree() == True

    #test find node
    def test_find_node(self, data, yang_s):
        for node in data['data_nodes']:
            expected = node['valid']
            xpath = str(node['xpath'])
            dnode = yang_s.find_data_node(xpath)

            if(expected == "True"):
                 assert dnode is not None
                 assert dnode.path() == xpath
            else:
                 assert dnode == None

    #test add node
    def test_add_node(self, data, yang_s):
        for node in data['new_nodes']:
            xpath = str(node['xpath'])
            value = node['value']
            status = yang_s.add_node(xpath, str(value))

            node = yang_s.find_data_node(xpath)
            assert node is not None

    #test find node value
    def test_find_node_value(self, data, yang_s):
       for node in data['node_values']:
            xpath = str(node['xpath'])
            value = str(node['value'])
            print(xpath)
            print(value)
            val = yang_s.find_node_value(xpath)
            assert str(val) == str(value)

    #test delete data node
    def test_delete_node(self, data, yang_s):
        for node in data['delete_nodes']:
            expected = node['valid']
            xpath = str(node['xpath'])
            status = yang_s.delete_node(xpath)
            assert str(status) == expected

    #test set node's value
    def test_set_datanode_value(self, data, yang_s):
        for node in data['set_nodes']:
            xpath = str(node['xpath'])
            value = node['value']
            status = yang_s.set_dnode_value(xpath, value)
            assert status == True

            val = yang_s.find_node_value(xpath)
            assert str(val) == str(value)

    #test list of members
    def test_find_members(self, yang_s, data):
        for node in data['members']:
            members = node['members']
            xpath = str(node['xpath'])
            list = yang_s.find_data_nodes(xpath)
            assert list.sort() == members.sort()

    #get parent xpath
    def test_get_parent_xpath(self, yang_s, data):
        for node in data['parents']:
            xpath = str(node['xpath'])
            expected_xpath = str(node['parent'])
            path = yang_s.get_parent_xpath(xpath)
            assert path == expected_xpath

    #test find_node_schema_xpath
    def test_find_node_schema_xpath(self, yang_s, data):
        for node in data['schema_nodes']:
            xpath = str(node['xpath'])
            schema_xpath = str(node['value'])
            path = yang_s.find_node_schema_xpath(xpath)
            assert path == schema_xpath

    #test data dependencies
    def test_find_data_dependencies(self, yang_s, data):
        for node in data['dependencies']:
            xpath = str(node['xpath'])
            list = node['dependencies']
            depend = yang_s.find_data_dependencies(xpath)
            print(depend)
            assert set(depend) == set(list)

    #test merge data tree
    def test_merge_data_tree(self, data, yang_s):
        data_merge_file = data['data_merge_file']
        yang_dir = data['yang_dir']
        rc = yang_s.merge_data(yang_dir, data_merge_file)
        yang_s.root.print_mem(ly.LYD_JSON, ly.LYP_FORMAT)
        assert rc == 0

    def teardown_class(cls):
        pass
