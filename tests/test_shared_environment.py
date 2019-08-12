import os
import sys
import unittest
import mock # define mock os.environ so we don't mess up real env vars
import src.util as util
from src.shared_environment import EnvironmentManager

class TestEnvironmentManager(unittest.TestCase):
    test_config = {'case_list':[{}], 'pod_list':['X']}

    # ---------------------------------------------------

    def test_setUp(self):
        pass #TODO

    # ---------------------------------------------------

    def test_check_pod_driver_no_driver_1(self):
        # fill in driver from pod name
        programs = util.get_available_programs()
        test_set = {'pod_name':'A', 'pod_dir':'/B'}
        with mock.patch('os.path.exists', return_value = True):
            with mock.patch('distutils.spawn.find_executable', return_value = True):                
                env = EnvironmentManager(self.test_config)
                env._check_pod_driver(test_set)
                ext = os.path.splitext(test_set['driver'])[1][1:]
                self.assertTrue(ext in programs)
                self.assertEqual(test_set['program'], programs[ext])

    def test_check_pod_driver_no_driver_2(self):
        # assertion fails if no driver found
        test_set = {'pod_name':'A', 'pod_dir':'/B'}
        with mock.patch('os.path.exists', return_value = False):
            env = EnvironmentManager(self.test_config)
            self.assertRaises(AssertionError, env._check_pod_driver, test_set)
    
    def test_check_pod_driver_abspath(self):
        # fill in absolute path
        test_set = {'pod_name':'A', 'pod_dir':'/B', 'driver':'C.ncl'}
        with mock.patch('os.path.exists', return_value = True):
            with mock.patch('distutils.spawn.find_executable', return_value = True):
                env = EnvironmentManager(self.test_config)
                env._check_pod_driver(test_set)
                self.assertEqual(test_set['driver'], '/B/C.ncl')
                self.assertEqual(test_set['program'], 'ncl')

    def test_check_pod_driver_program(self):
        # fill in program from driver's extension
        test_set = {'pod_name':'A', 'pod_dir':'/B', 'driver':'C.ncl'}
        with mock.patch('os.path.exists', return_value = True):
            with mock.patch('distutils.spawn.find_executable', return_value = True):
                env = EnvironmentManager(self.test_config)
                env._check_pod_driver(test_set)
                self.assertEqual(test_set['program'], 'ncl')

    def test_check_pod_driver_no_program_1(self):
        # assertion fail if can't recognize driver's extension
        test_set = {'pod_name':'A', 'pod_dir':'/B', 'driver':'C.foo'}
        with mock.patch('os.path.exists', return_value = True):
            env = EnvironmentManager(self.test_config)
            self.assertRaises(AssertionError, env._check_pod_driver, test_set)

    def test_check_pod_driver_no_program_2(self):
        # assertion fail if explicitly specified program not found
        test_set = {'pod_name':'A', 'pod_dir':'/B', 'driver':'C.ncl',
            'program':'nonexistent_program'}
        with mock.patch('os.path.exists', return_value = True):
            env = EnvironmentManager(self.test_config)
            self.assertRaises(AssertionError, env._check_pod_driver, test_set)

    # ---------------------------------------------------

    os_environ_check_for_varlist_files = {
        'DATADIR':'/A', 'CASENAME': 'B', 'prc_var':'PRECC'}

    def test_check_for_varlist_files_found(self):
        # case file is found
        test_vars = [{'var_name': 'pr_var', 'name_in_model':'PRECT', 
            'freq':'mon'}]
        with mock.patch.dict('os.environ', self.os_environ_check_for_varlist_files):
            with mock.patch('os.path.isfile', return_value = True):
                env = EnvironmentManager(self.test_config)
                f = env._check_for_varlist_files(test_vars)
                self.assertEqual(f['found_files'], ['/A/mon/B.PRECT.mon.nc'])
                self.assertEqual(f['missing_files'], [])

    def test_check_for_varlist_files_not_found(self):
        # case file is required and not found
        test_vars = [{'var_name': 'pr_var', 'name_in_model':'PRECT', 
            'freq':'mon', 'required': True}]
        with mock.patch.dict('os.environ', self.os_environ_check_for_varlist_files):
            with mock.patch('os.path.isfile', return_value = False):
                env = EnvironmentManager(self.test_config)
                f = env._check_for_varlist_files(test_vars)
                self.assertEqual(f['found_files'], [])
                self.assertEqual(f['missing_files'], ['/A/mon/B.PRECT.mon.nc'])

    def test_check_for_varlist_files_optional(self):
        # case file is optional and not found
        test_vars = [{'var_name': 'pr_var', 'name_in_model':'PRECT', 
            'freq':'mon', 'required': False}]
        with mock.patch.dict('os.environ', self.os_environ_check_for_varlist_files):
            with mock.patch('os.path.isfile', side_effect = [False, True]):
                env = EnvironmentManager(self.test_config)
                f = env._check_for_varlist_files(test_vars, 2)
                self.assertEqual(f['found_files'], [])
                self.assertEqual(f['missing_files'], [])

    def test_check_for_varlist_files_alternate(self):
        # case alternate variable is specified and found
        test_vars = [{'var_name': 'pr_var', 'name_in_model':'PRECT', 
            'freq':'mon', 'required': True, 'alternates':['prc_var']}]
        with mock.patch.dict('os.environ', self.os_environ_check_for_varlist_files):
            with mock.patch('os.path.isfile', side_effect = [False, True]):
                env = EnvironmentManager(self.test_config)
                f = env._check_for_varlist_files(test_vars, 2)
                self.assertEqual(f['found_files'], ['/A/mon/B.PRECC.mon.nc'])
                self.assertEqual(f['missing_files'], [])

    # ---------------------------------------------------

    def test_run(self):
        pass #TODO

# ---------------------------------------------------

if __name__ == '__main__':
    unittest.main()