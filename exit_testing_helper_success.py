from training_utils import build_training_parser
from meticulous import Experiment

def successful_exit():
    parser = build_training_parser()
    Experiment.add_argument_group(parser)
    experiment = Experiment.from_parser(parser)

if __name__ == '__main__':
    successful_exit()