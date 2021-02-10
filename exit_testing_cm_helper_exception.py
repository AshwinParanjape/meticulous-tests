from training_utils import build_training_parser
from meticulous import Experiment
import time
def raise_exception():
    parser = build_training_parser()
    Experiment.add_argument_group(parser)
    with Experiment.from_parser(parser) as exp:
        raise Exception
    time.sleep(2)
    Experiment.from_parser(parser)
    raise Exception

if __name__ == '__main__':
    raise_exception()