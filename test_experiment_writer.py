import unittest
from .training_utils import build_training_parser
import subprocess
import json
from meticulous import Experiment
from meticulous.experiment import DirtyRepoException
import random, string
import os
import shutil
import sys
from git import Repo
def id_generator(size=6, chars=string.ascii_uppercase + string.digits):
    return ''.join(random.choice(chars) for _ in range(size))


class DirtyRepoTestCase(unittest.TestCase):
    def setUp(self):
        #Dirty a file in the repo
        with open(os.path.join('simulated_files', 'dirty_file.txt'), 'w') as f:
            f.write('made dirty')
        self.parser = build_training_parser()
        Experiment.add_argument_group(self.parser)

    def test_dirty_repo(self):
        with self.assertRaises(DirtyRepoException):
            Experiment.from_parser(self.parser)

    def tearDown(self):
        with open(os.path.join('simulated_files','dirty_file.txt'), 'w') as f:
            pass

class StatusTestCase(unittest.TestCase):
    # These tests are invoked with subproccess because they test behaviour at program exit
    def setUp(self):
        self.experiments_folder_id = os.path.join('temp_files','experiments_'+self.id())
        self.arg_list = ['--dry-run', '--epochs', '1', '--experiments-directory', self.experiments_folder_id]

    def test_success(self):
        subprocess.run(['python', 'exit_testing_helper_success.py', ]+self.arg_list)
        with open(os.path.join(self.experiments_folder_id, '1', 'STATUS'), 'r') as f:
            self.assertEqual(f.readlines()[0].strip(), 'SUCCESS')

    def test_exit(self):
        subprocess.run(['python', 'exit_testing_helper_exit.py', ]+self.arg_list)
        with open(os.path.join(self.experiments_folder_id, '1', 'STATUS'), 'r') as f:
            self.assertEqual(f.readlines()[0].strip(), 'ERROR')

    def test_exception(self):
        subprocess.run(['python', 'exit_testing_helper_exception.py', ]+self.arg_list)
        with open(os.path.join(self.experiments_folder_id, '1', 'STATUS'), 'r') as f:
            self.assertEqual(f.readlines()[0].strip(), 'Traceback (most recent call last):')

    def tearDown(self):
        shutil.rmtree(self.experiments_folder_id)
        pass

class OutputTestCase(unittest.TestCase):
    def setUp(self):
        self.experiments_folder_id = os.path.join('temp_files', 'experiments_'+self.id())
        self.original_args_list = ['--dry-run', '--epochs', '1']
        self.meticulous_args_list = ['--experiments-directory', self.experiments_folder_id]

    def test_metadata(self):
        parser = build_training_parser()
        Experiment.add_argument_group(parser)
        experiment = Experiment.from_parser(parser, self.original_args_list+self.meticulous_args_list)
        with open(os.path.join(self.experiments_folder_id, '1', 'metadata.json'), 'r') as f:
            metadata = json.load(f)
            repo = Repo('', search_parent_directories=True)
            self.assertEqual(metadata['githead-sha'], repo.commit().hexsha, msg="Stored githead-sha doesn't match actual githead-sha")

    def test_args(self):
        args_list = self.original_args_list + ['--seed', '234']
        parser = build_training_parser()
        args = vars(parser.parse_args(args_list))
        Experiment.add_argument_group(parser)
        experiment = Experiment.from_parser(parser, args_list+self.meticulous_args_list)
        with open(os.path.join(self.experiments_folder_id, '1', 'args.json'), 'r') as f:
            stored_args = json.load(f)
            self.assertDictEqual(stored_args, args, msg="Stored args don't match actual args")

    def test_default_args(self):
        args_list = self.original_args_list + ['--seed', '234']
        parser = build_training_parser()
        default_args = vars(parser.parse_args([]))
        Experiment.add_argument_group(parser)
        experiment = Experiment.from_parser(parser, args_list+self.meticulous_args_list)
        with open(os.path.join(self.experiments_folder_id, '1', 'default_args.json'), 'r') as f:
            stored_args = json.load(f)
            self.assertDictEqual(stored_args, default_args, msg="Stored default args don't match actual default args")

    def test_stdout_redirection(self):
        args_list = self.original_args_list + ['--seed', '234']
        parser = build_training_parser()
        default_args = vars(parser.parse_args([]))
        Experiment.add_argument_group(parser)
        experiment = Experiment.from_parser(parser, args_list+self.meticulous_args_list)
        stdout_text = 'stdout redirection text'
        stderr_text = 'stderr redirection text'
        print(stdout_text)
        print(stderr_text, file=sys.stderr)
        with open(os.path.join(self.experiments_folder_id, '1', 'stdout'), 'r') as f:
            first_line = f.readlines()[0]
            self.assertEqual(stdout_text, first_line.strip(), msg="Error with stdout redirection")

        with open(os.path.join(self.experiments_folder_id, '1', 'stderr'), 'r') as f:
            first_line = f.readlines()[0]
            self.assertEqual(stderr_text, first_line.strip(), msg="Error with stderr redirection")

    def tearDown(self):
        shutil.rmtree(self.experiments_folder_id)
        pass
