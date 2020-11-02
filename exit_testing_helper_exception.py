from training_utils import build_training_parser
from meticulous import Experiment

def raise_exception():
    parser = build_training_parser()
    Experiment.add_argument_group(parser)
    experiment = Experiment.from_parser(parser)
    raise Exception

if __name__ == '__main__':
    raise_exception()