from training_utils import build_training_parser
from meticulous import Experiment
import sys

def forced_exit():
    parser = build_training_parser()
    Experiment.add_argument_group(parser)
    experiment = Experiment.from_parser(parser)
    sys.exit()

if __name__ == '__main__':
    forced_exit()