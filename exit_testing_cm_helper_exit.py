from training_utils import build_training_parser
from meticulous import Experiment
import sys

def forced_exit():
    parser = build_training_parser()
    Experiment.add_argument_group(parser)
    with Experiment.from_parser(parser) as exp:
        sys.exit()

if __name__ == '__main__':
    forced_exit()