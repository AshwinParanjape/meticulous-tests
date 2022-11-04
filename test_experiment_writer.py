import unittest
from .training_utils import build_training_parser, build_training_parser_with_required_args
import subprocess
import json
from meticulous import Experiment
from meticulous.experiment import DirtyRepoException, MismatchedArgsException
import random, string
import os
import shutil
import sys
import datetime
from git import Repo
def id_generator(size=6, chars=string.ascii_uppercase + string.digits):
    return ''.join(random.choice(chars) for _ in range(size))

class RequiredArgsTestCase(unittest.TestCase):
    def setUp(self):
        self.experiments_folder_id = os.path.join('temp_files', 'experiments_'+self.id())
        self.original_args_list = ['16', '--test-batch-size', '2']
        self.meticulous_args_list = ['--experiments-directory', self.experiments_folder_id]

    def test_args(self):
        parser = build_training_parser_with_required_args()
        args = vars(parser.parse_args(self.original_args_list))
        Experiment.add_argument_group(parser)
        exp = Experiment.from_parser(parser, arg_list=self.original_args_list+self.meticulous_args_list)
        with open(os.path.join(self.experiments_folder_id, '1', 'args.json'), 'r') as f:
            stored_args = json.load(f)
            self.assertDictEqual(stored_args, args, msg="Stored args don't match actual args")
        exp.finish()


    def test_default_args(self):
        parser = build_training_parser_with_required_args()
        default_args = vars(parser.parse_args(['16']))
        del default_args['batchsize']
        Experiment.add_argument_group(parser)
        experiment = Experiment.from_parser(parser, arg_list=self.original_args_list+self.meticulous_args_list)
        with open(os.path.join(self.experiments_folder_id, '1', 'default_args.json'), 'r') as f:
            stored_args = json.load(f)
            self.assertDictEqual(stored_args, default_args, msg="Stored default args don't match actual default args")
        experiment.finish()

    def tearDown(self):
        shutil.rmtree(self.experiments_folder_id)
        pass

class DirtyRepoTestCase(unittest.TestCase):
    def setUp(self):
        self.experiments_folder_id = os.path.join('temp_files', 'experiments_'+self.id())
        self.original_args_list = ['--dry-run', '--epochs', '1']
        self.meticulous_args_list = ['--experiments-directory', self.experiments_folder_id]
        #Dirty a file in the repo
        with open(os.path.join('simulated_files', 'dirty_file.txt'), 'w') as f:
            f.write('made dirty')
        self.parser = build_training_parser()
        Experiment.add_argument_group(self.parser)

    def test_dirty_repo(self):
        with self.assertRaises(DirtyRepoException):
            exp = Experiment.from_parser(self.parser, self.original_args_list+self.meticulous_args_list)
            #with open(os.path.join(self.experiments_folder_id, '1', 'metadata.json'), 'r') as f:
            #    metadata = json.load(f)
            #    self.assertIn("git-dirty", metadata)

    def tearDown(self):
        with open(os.path.join('simulated_files','dirty_file.txt'), 'w') as f:
            pass

class EndTimeTestCase(unittest.TestCase):
    # These tests are invoked with subproccess because they test behaviour at program exit
    def setUp(self):
        self.experiments_folder_id = os.path.join('temp_files', 'experiments_' + self.id())
        self.arg_list = ['--dry-run', '--epochs', '1', '--experiments-directory', self.experiments_folder_id]

    def test_success(self):
        subprocess.run(['python', 'exit_testing_helper_success.py', ]+self.arg_list)
        with open(os.path.join(self.experiments_folder_id, '1', 'metadata.json'), 'r') as f:
            metadata = json.load(f)
            self.assertIn('end-time', metadata)

    def test_exit(self):
        subprocess.run(['python', 'exit_testing_helper_exit.py', ]+self.arg_list)
        with open(os.path.join(self.experiments_folder_id, '1', 'metadata.json'), 'r') as f:
            metadata = json.load(f)
            self.assertIn('end-time', metadata)

    def test_exception(self):
        subprocess.run(['python', 'exit_testing_helper_exception.py', ]+self.arg_list)
        with open(os.path.join(self.experiments_folder_id, '1', 'metadata.json'), 'r') as f:
            metadata = json.load(f)
            self.assertIn('end-time', metadata)

    def tearDown(self):
        shutil.rmtree(self.experiments_folder_id)
        pass

class ContextManagerEndTimeTestCase(unittest.TestCase):
    # These tests are invoked with subproccess because they test behaviour at program exit
    def setUp(self):
        self.experiments_folder_id = os.path.join('temp_files', 'experiments_' + self.id())
        self.arg_list = ['--dry-run', '--epochs', '1', '--experiments-directory', self.experiments_folder_id]

    def test_success(self):
        subprocess.run(['python', 'exit_testing_cm_helper_success.py', ]+self.arg_list)
        with open(os.path.join(self.experiments_folder_id, '1', 'metadata.json'), 'r') as f:
            metadata1 = json.load(f)
            self.assertIn('end-time', metadata1)
        with open(os.path.join(self.experiments_folder_id, '2', 'metadata.json'), 'r') as f:
            metadata2 = json.load(f)
            self.assertIn('end-time', metadata2)
        with open(os.path.join(self.experiments_folder_id, '3', 'metadata.json'), 'r') as f:
            metadata3 = json.load(f)
            self.assertIn('end-time', metadata3)
        end_time1 = datetime.datetime.strptime(metadata1["end-time"], "%Y-%m-%dT%H:%M:%S.%f")
        end_time2 = datetime.datetime.strptime(metadata2["end-time"], "%Y-%m-%dT%H:%M:%S.%f")
        end_time3 = datetime.datetime.strptime(metadata3["end-time"], "%Y-%m-%dT%H:%M:%S.%f")
        self.assertTrue(end_time2 - end_time1 < datetime.timedelta(seconds=1))
        self.assertTrue(end_time3 - end_time2 > datetime.timedelta(seconds=1))

    def test_exception(self):
        subprocess.run(['python', 'exit_testing_cm_helper_exception.py', ]+self.arg_list)
        with open(os.path.join(self.experiments_folder_id, '1', 'metadata.json'), 'r') as f:
            metadata1 = json.load(f)
            self.assertIn('end-time', metadata1)
        with open(os.path.join(self.experiments_folder_id, '2', 'metadata.json'), 'r') as f:
            metadata2 = json.load(f)
            self.assertIn('end-time', metadata2)
        end_time1 = datetime.datetime.strptime(metadata1["end-time"], "%Y-%m-%dT%H:%M:%S.%f")
        end_time2 = datetime.datetime.strptime(metadata2["end-time"], "%Y-%m-%dT%H:%M:%S.%f")
        self.assertTrue(end_time2 - end_time1 > datetime.timedelta(seconds=1))

    def tearDown(self):
        shutil.rmtree(self.experiments_folder_id)
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
            lines = f.readlines()
            self.assertEqual(lines[0].strip(), 'ERROR')
            self.assertEqual(lines[1].strip(), 'Traceback (most recent call last):')

    def tearDown(self):
        shutil.rmtree(self.experiments_folder_id)
        pass

class ContextManagerStatusTestCase(unittest.TestCase):
    """Test whether experiments in context manager produce the same output as 'global' experiments"""
    # These tests are invoked with subproccess because they test behaviour at program exit
    def setUp(self):
        self.experiments_folder_id = os.path.join('temp_files','experiments_'+self.id())
        self.arg_list = ['--dry-run', '--epochs', '1', '--experiments-directory', self.experiments_folder_id]

    def test_success(self):
        subprocess.run(['python', 'exit_testing_cm_helper_success.py', ]+self.arg_list)
        # Context Manager
        with open(os.path.join(self.experiments_folder_id, '1', 'STATUS'), 'r') as f:
            exp1 = f.readlines()[0].strip()
        # Experiment where we call 'finish' manually
        with open(os.path.join(self.experiments_folder_id, '2', 'STATUS'), 'r') as f:
            exp2 = f.readlines()[0].strip()
        # Experiment that is terminated on exit
        with open(os.path.join(self.experiments_folder_id, '3', 'STATUS'), 'r') as f:
            exp3 = f.readlines()[0].strip()
        self.assertEqual(exp1, 'SUCCESS')
        self.assertEqual(exp1, exp2)
        self.assertEqual(exp2, exp3)
        # All experiments returned SUCCESS successfully

    def test_exit(self):
        subprocess.run(['python', 'exit_testing_cm_helper_exit.py', ]+self.arg_list)
        with open(os.path.join(self.experiments_folder_id, '1', 'STATUS'), 'r') as f:
            self.assertEqual(f.readlines()[0].strip(),'ERROR')

    def test_exception(self):
        subprocess.run(['python', 'exit_testing_cm_helper_exception.py', ]+self.arg_list)
        with open(os.path.join(self.experiments_folder_id, '1', 'STATUS'), 'r') as f:
            lines1 = f.readlines()
        with open(os.path.join(self.experiments_folder_id, '2', 'STATUS'), 'r') as f:
            lines2 = f.readlines()
        self.assertEqual(lines1[0].strip(), 'ERROR')
        self.assertEqual(lines1[1].strip(), 'Traceback (most recent call last):')
        # Test that the context manager (id 2) produces the same output as the global experiment (id 1)
        self.assertEqual(lines1[0].strip(), lines2[0].strip())
        self.assertEqual(lines1[1].strip(), lines2[1].strip())

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
            commit = repo.commit()
            self.assertEqual(metadata['githead-sha'], commit.hexsha, msg="Stored githead-sha doesn't match actual githead-sha")
            self.assertEqual(metadata['githead-message'], commit.message,
                             msg="Stored commit message doesn't match actual commit message")
            self.assertIn('start-time', metadata)
            self.assertIn('description', metadata)
            self.assertIn('command', metadata)
        experiment.finish()


    def test_args(self):
        args_list = self.original_args_list + ['--seed', '234']
        parser = build_training_parser()
        args = vars(parser.parse_args(args_list))
        Experiment.add_argument_group(parser)
        experiment = Experiment.from_parser(parser, args_list+self.meticulous_args_list)
        with open(os.path.join(self.experiments_folder_id, '1', 'args.json'), 'r') as f:
            stored_args = json.load(f)
            self.assertDictEqual(stored_args, args, msg="Stored args don't match actual args")
        experiment.finish()


    def test_default_args(self):
        args_list = self.original_args_list + ['--seed', '234']
        parser = build_training_parser()
        default_args = vars(parser.parse_args([]))
        Experiment.add_argument_group(parser)
        experiment = Experiment.from_parser(parser, args_list+self.meticulous_args_list)
        with open(os.path.join(self.experiments_folder_id, '1', 'default_args.json'), 'r') as f:
            stored_args = json.load(f)
            self.assertDictEqual(stored_args, default_args, msg="Stored default args don't match actual default args")
        experiment.finish()

    def test_nested_stdout_redirection(self):
        args_list = self.original_args_list + ['--seed', '234']
        parser = build_training_parser()
        Experiment.add_argument_group(parser)
        stdout_text1, stderr_text1 = "stdout redirection text 1", "stderr redirection text 1"
        stdout_text2, stderr_text2 = "stdout redirection text 2", "stderr redirection text 2"
        stdout_text3, stderr_text3 = "stdout redirection text 3", "stderr redirection text 3"
        outer_experiment = Experiment.from_parser(parser, args_list + self.meticulous_args_list)
        print(stdout_text1)
        print(stderr_text1, file=sys.stderr)
        with Experiment.from_parser(parser, args_list + self.meticulous_args_list) as inner_experiment:
            print(stdout_text2)
            print(stderr_text2, file=sys.stderr)
        print(stdout_text3)
        print(stderr_text3, file=sys.stderr)
        outer_experiment.finish()

        with open(os.path.join(self.experiments_folder_id, '1', 'stdout'), 'r') as f:
            lines = f.readlines()
            self.assertEqual(stdout_text1, lines[0].strip(), msg="Error with stdout redirection")
            self.assertEqual(stdout_text2, lines[1].strip(), msg="Error with stdout redirection")
            self.assertEqual(stdout_text3, lines[2].strip(), msg="Error with stdout redirection")

        with open(os.path.join(self.experiments_folder_id, '1', 'stderr'), 'r') as f:
            lines = f.readlines()
            self.assertEqual(stderr_text1, lines[0].strip(), msg="Error with stderr redirection")
            self.assertEqual(stderr_text2, lines[1].strip(), msg="Error with stderr redirection")
            self.assertEqual(stderr_text3, lines[2].strip(), msg="Error with stderr redirection")

        with open(os.path.join(self.experiments_folder_id, '2', 'stdout'), 'r') as f:
            first_line = f.readlines()[0]
            self.assertEqual(stdout_text2, first_line.strip(), msg="Error with stdout redirection")

        with open(os.path.join(self.experiments_folder_id, '2', 'stderr'), 'r') as f:
            first_line = f.readlines()[0]
            self.assertEqual(stderr_text2, first_line.strip(), msg="Error with stderr redirection")

    def test_stdout_redirection(self):
        args_list = self.original_args_list + ['--seed', '234']
        parser = build_training_parser()
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
        experiment.finish()
    def test_sequential_stdout_redirection(self):
        args_list = self.original_args_list + ['--seed', '234']
        parser = build_training_parser()
        Experiment.add_argument_group(parser)
        stdout_text1 = "stdout redirection text 1"
        stderr_text1 = "stderr redirection text 1"
        stdout_text2 = "stdout redirection text 2"
        stderr_text2 = "stderr redirection text 2"
        with Experiment.from_parser(parser, args_list+self.meticulous_args_list) as exp:
            print(stdout_text1)
            print(stderr_text1, file=sys.stderr)
        exp2 = Experiment.from_parser(parser, args_list+self.meticulous_args_list)
        print(stdout_text2)
        print(stderr_text2, file=sys.stderr)
        exp2.finish()
        with open(os.path.join(self.experiments_folder_id, '1', 'stdout'), 'r') as f:
            first_line = f.readlines()[0]
            self.assertEqual(stdout_text1, first_line.strip(), msg="Error with stdout redirection")

        with open(os.path.join(self.experiments_folder_id, '1', 'stderr'), 'r') as f:
            first_line = f.readlines()[0]
            self.assertEqual(stderr_text1, first_line.strip(), msg="Error with stderr redirection")

        with open(os.path.join(self.experiments_folder_id, '2', 'stdout'), 'r') as f:
            first_line = f.readlines()[0]
            self.assertEqual(stdout_text2, first_line.strip(), msg="Error with stdout redirection")

        with open(os.path.join(self.experiments_folder_id, '2', 'stderr'), 'r') as f:
            first_line = f.readlines()[0]
            self.assertEqual(stderr_text2, first_line.strip(), msg="Error with stderr redirection")
    
    def test_given_experiment_id(self):
        args_list = self.original_args_list + ['--seed', '234']
        parser = build_training_parser()
        Experiment.add_argument_group(parser)
        experiment1 = Experiment.from_parser(parser, args_list+self.meticulous_args_list + ['--experiment-id', '2'])
        experiment2 = Experiment.from_parser(parser, args_list+self.meticulous_args_list)
        self.assertTrue(os.path.exists(os.path.join(self.experiments_folder_id, '2')))
        self.assertTrue(os.path.exists(os.path.join(self.experiments_folder_id, '3')))
        experiment1.finish()
        experiment2.finish()

    def test_resuming_experiment(self):
        args_list = self.original_args_list + ['--seed', '234']
        parser = build_training_parser()
        Experiment.add_argument_group(parser)
        experiment = Experiment.from_parser(parser, args_list + self.meticulous_args_list + ['--experiment-id', '2'])
        experiment.finish()
        del experiment
        experiment = Experiment.from_parser(parser, args_list + self.meticulous_args_list + ['--experiment-id', '2'])
        # We should make it to here without an MismatchedArgsException or a MismatchedCommitException.
        # The experiment dir should be the 2/ located in the right tempfile
        self.assertTrue(experiment.curexpdir.endswith("2"))
        experiment.finish()

    def test_failure_on_arg_change_for_resumed_experiment(self):
        args_list1 = self.original_args_list + ['--seed', '234']
        args_list2 = self.original_args_list + ['--seed', '235']
        parser = build_training_parser()
        Experiment.add_argument_group(parser)
        experiment = Experiment.from_parser(parser, args_list1+self.meticulous_args_list + ['--experiment-id', '2'])
        experiment.finish()
        del experiment
        with self.assertRaises(MismatchedArgsException):
            experiment = Experiment.from_parser(parser, args_list2 + self.meticulous_args_list + ['--experiment-id', '2'])
            experiment.finish()

    def test_noninteger_experiment_id(self):
        args_list = self.original_args_list + ['--seed', '234']
        parser = build_training_parser()
        Experiment.add_argument_group(parser)
        experiment1 = Experiment.from_parser(parser, args_list+self.meticulous_args_list + ['--experiment-id', 'a'])
        experiment2 = Experiment.from_parser(parser, args_list+self.meticulous_args_list)
        self.assertTrue(os.path.exists(os.path.join(self.experiments_folder_id, 'a')))
        self.assertTrue(os.path.exists(os.path.join(self.experiments_folder_id, '1')))
        experiment1.finish()
        experiment2.finish()

    def test_noninteger_experiments(self):
        args_list = self.original_args_list + ['--seed', '234']
        parser = build_training_parser()
        Experiment.add_argument_group(parser)
        experiment1 = Experiment.from_parser(parser, args_list+self.meticulous_args_list)
        experiment2 = Experiment.from_parser(parser, args_list+self.meticulous_args_list)
        self.assertTrue(os.path.exists(os.path.join(self.experiments_folder_id, '1')))
        self.assertTrue(os.path.exists(os.path.join(self.experiments_folder_id, '2')))
        experiment1.finish()
        experiment2.finish()

    def test_override_default_meticulous_args(self):
        args_list = self.original_args_list + ['--seed', '234']
        parser = build_training_parser()
        args = vars(parser.parse_args(args_list))
        Experiment.add_argument_group(parser, description='Test override')
        experiment = Experiment.from_parser(parser, args_list+self.meticulous_args_list)
        with open(os.path.join(self.experiments_folder_id, '1', 'metadata.json'), 'r') as f:
            metadata = json.load(f)
            self.assertEqual(metadata['description'], 'Test override')
        experiment.finish()


    def tearDown(self):
        shutil.rmtree(self.experiments_folder_id)
        pass
