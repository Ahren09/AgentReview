import os
import random
from os import path as osp

import numpy as np


def check_cwd():
    basename = osp.basename(osp.normpath(os.getcwd()))
    assert basename.lower() in [
        "agentreview"], "Please run this file from the repository root directory (AgentReview/)"


def set_seed(seed):
    random.seed(seed)
    np.random.seed(seed)
