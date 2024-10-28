import json
import os
import os.path as osp
import random
import re
from collections import Counter
from typing import Union, List, Dict, Tuple

import numpy as np
import pandas as pd

from agentreview import const
from agentreview.utility.general_utils import check_cwd, set_seed


def generate_num_papers_to_accept(n, batch_number, shuffle=True):
    # Calculate the base value (minimum value in the array)
    base_value = int(n // batch_number)

    # Calculate how many elements need to be base_value + 1
    remainder = int(n % batch_number)

    # Initialize the array
    array = []

    # Add the elements to the array
    for i in range(batch_number):
        if i < remainder:
            array.append(base_value + 1)
        else:
            array.append(base_value)

    if shuffle:
        random.shuffle(array)

    return array


def get_papers_accepted_by_llm(llm_ac_decisions, acceptance_rate: float) -> list:
    papers_accepted_by_llm = []

    num_papers = sum([len(batch) for batch in llm_ac_decisions])

    if num_papers == 0:
        raise ValueError("No papers found in batch")

    num_papers_to_accept = generate_num_papers_to_accept(n=acceptance_rate * num_papers,
                                                         batch_number=len(llm_ac_decisions))

    for idx_batch, batch in enumerate(llm_ac_decisions):
        tups = sorted([(paper_id, rank) for paper_id, rank in batch.items()], key=lambda x: x[1], reverse=False)

        paper_ids = [int(paper_id) for paper_id, rank in tups]

        papers_accepted_by_llm += paper_ids[:num_papers_to_accept[idx_batch]]

    return papers_accepted_by_llm


def get_paper_decision_mapping(data_dir: str, conference: str, verbose: bool = False):
    paper_id2decision, paper_decision2ids = {}, {}
    path_paper_id2decision = os.path.join(data_dir, conference, "id2decision.json")
    path_paper_decision2ids = os.path.join(data_dir, conference, "decision2ids.json")

    if osp.exists(path_paper_id2decision) and osp.exists(path_paper_decision2ids):
        paper_id2decision = json.load(open(path_paper_id2decision, 'r', encoding='utf-8'))
        paper_decision2ids = json.load(open(path_paper_decision2ids, 'r', encoding='utf-8'))

        paper_id2decision = {int(k): v for k, v in paper_id2decision.items()}

        if verbose:
            print(f"Loaded {len(paper_id2decision)} paper IDs to decisions from {path_paper_id2decision}")

    else:

        PAPER_DECISIONS = get_all_paper_decisions(conference)

        for paper_decision in PAPER_DECISIONS:

            paper_ids = os.listdir(os.path.join(data_dir, conference, "notes", paper_decision))
            paper_ids = sorted(
                [int(paper_id.split(".json")[0]) for paper_id in paper_ids if paper_id.endswith(".json")])

            paper_id2decision.update({paper_id: paper_decision for paper_id in paper_ids})
            paper_decision2ids[paper_decision] = paper_ids

            if verbose:
                print(f"{paper_decision}: {len(paper_ids)} papers")

        json.dump(paper_id2decision, open(path_paper_id2decision, 'w', encoding='utf-8'), indent=2)
        json.dump(paper_decision2ids, open(path_paper_decision2ids, 'w', encoding='utf-8'), indent=2)

    return paper_id2decision, paper_decision2ids


def project_setup():
    check_cwd()
    import warnings
    import pandas as pd
    warnings.simplefilter(action='ignore', category=FutureWarning)
    pd.set_option('display.max_rows', 40)
    pd.set_option('display.max_columns', 20)
    set_seed(42)


def get_next_review_id(path: str) -> int:
    existing_review_ids = sorted([int(x.split('.json')[0].split('_')[1]) for x in os.listdir(path)])
    next_review_id = 1
    while next_review_id in existing_review_ids:
        next_review_id += 1
    print(f"Next review ID: {next_review_id}")
    return next_review_id




def filter_paper_ids_from_initial_experiments(sampled_paper_ids: List[int]):
    paper_ids_initial_experiments = json.load(open(f"outputs/paper_ids_initial_experiments.json"))
    sampled_paper_ids = set(sampled_paper_ids) - set(paper_ids_initial_experiments)
    sampled_paper_ids = sorted(list(sampled_paper_ids))
    return sampled_paper_ids


def get_paper_review_and_rebuttal_dir(reviewer_type: str, conference: str, model_name: str, paper_id: int = None):
    if reviewer_type == "NoOverallScore":
        reviewer_type = "BASELINE"

    path = f"outputs/paper_review_and_rebuttal" \
           f"/{conference}/" \
           f"{get_model_name_short(model_name)}/{reviewer_type}"

    if paper_id is not None:
        path += f"/{paper_id}"

    return path


def get_rebuttal_dir(output_dir: str,
                     paper_id: Union[str, int, None],
                     experiment_name: str,
                     model_name: str,
                     conference: str):

    path = os.path.join(output_dir, "paper_review", conference, get_model_name_short(model_name),
            experiment_name)

    if paper_id is not None:
        path += f"/{paper_id}"

    return path


def print_colored(text, color='red'):

    # Dictionary of ANSI color codes for terminal
    foreground_colors = {
        'black': 30,
        'red': 31,
        'green': 32,
        'yellow': 33,
        'blue': 34,
        'magenta': 35,
        'cyan': 36,
        'white': 37,
    }
    try:

        # get_ipython is specific to Jupyter and IPython.
        # We use this to decide whether we are running a Jupyter notebook or not.
        get_ipython
        print(text)  # Plain text in Jupyter
    except:
        # If not Jupyter, print with color codes
        color_code = foreground_colors.get(color, 31)  # Default to red if color not found
        print(f"\033[{color_code}m{text}\033[0m")


def get_ac_decision_path(output_dir: str, conference: str, model_name: str, ac_scoring_method: str, experiment_name:
str):
    ac_decision_dir = os.path.join(output_dir, "decisions", conference,
                                   get_model_name_short(model_name),
                                   f"decisions_thru_{ac_scoring_method}")
    os.makedirs(ac_decision_dir, exist_ok=True)

    if isinstance(experiment_name, str):
        ac_decision_dir += f"/decision_{experiment_name}.json"

    return ac_decision_dir


def load_metareview(paper_id: int, **kwargs):
    rebuttal_dir = get_rebuttal_dir(paper_id=paper_id, **kwargs)

    path = f"{rebuttal_dir}/{paper_id}.json"

    if not osp.exists(path):
        print(f"Not Found: {path}")
        return None

    try:
        reviews = json.load(open(path))

        metareview = reviews["messages"][-1]
        if not metareview["agent_name"].startswith("AC"):
            return None

        return metareview['content']

    except FileNotFoundError:
        return None


def get_reviewer_type_from_profile(profile: dict):
    """
    Get a short name for the reviewer's type from the reviewer's  experiment profile.
    
    
    Input:
        {
            'is_benign': True,
            'is_knowledgeable': None,
            'is_responsible': None,
            'provides_numeric_rating': True
        }

    Output:
        "benign"


    Input:
        {
            'is_benign': False,
            'is_knowledgeable': None,
            'is_responsible': None,
            'provides_numeric_rating': True
        }

    Output:
        "malicious"


    Input:
        {
            'is_benign': None,
            'is_knowledgeable': None,
            'is_responsible': None,
            'provides_numeric_rating': True
        }

    Output:
        "default"

    """

    reviewer_attributes = Counter([profile[k] for k in ["is_benign", 'is_knowledgeable', 'is_responsible']])

    assert (reviewer_attributes[True] <= 1 and reviewer_attributes[False] <= 1) and reviewer_attributes[None] >= 2, \
        ("A reviewer can only have 0 or 1 of "
         "these "
         "properties profile to True or False")

    if profile['is_benign']:
        return "benign"
    elif profile['is_benign'] == False:
        # NOTE: We cannot use `not profile['is_benign']` as we need to consider the case where `profile['is_benign']`
        # is
        # None
        return "malicious"

    elif profile['is_knowledgeable']:
        return "knowledgeable"

    elif profile['is_knowledgeable'] == False:
        # Same as above
        return "unknowledgeable"

    elif profile['is_responsible']:
        return "responsible"
    elif profile['is_responsible'] == False:
        # Same as above
        return "irresponsible"

    elif profile['provides_numeric_rating'] == False:
        return "NoOverallScore"

    elif profile.get('knows_authors') == "famous":
        return "authors_are_famous"

    elif profile.get('knows_authors') == "unfamous":
        return "authors_are_unfamous"

    else:
        return "BASELINE"


def get_ac_type_from_profile(profile: dict):
    return None


# def get_ac_type_from_profile(profile: dict):
#     """
#     Get a short name for the area chair's type from their profile in the experiment setting.
#
#     """

def format_metareviews(metareviews: List[str], paper_ids: List[int]):
    metareviews_formatted = ""

    for paper_id, metareview in zip(paper_ids, metareviews):
        metareview = re.sub('\n+', '\n', metareview)
        metareviews_formatted += (f"Paper ID: {paper_id}\nMetareview: "
                                  f"{metareview}\n{'-' * 5}\n")

    return metareviews_formatted


def get_all_paper_decisions(conference: str) -> List[str]:
    if conference in ["ICLR2019", "ICLR2018"]:
        return const.PAPER_DECISIONS_ICLR2019

    else:
        return const.PAPER_DECISIONS


def get_paper_ids_of_known_authors(conference: str, num_papers: int, decision: str = None):
    paper_id2decision, paper_decision2ids = get_paper_decision_mapping(conference)
    paper_ids_of_famous_authors = paper_decision2ids[decision][:num_papers]
    return paper_ids_of_famous_authors


def get_experiment_names(conference: str = "ICLR2023"):
    experiment_names = ["BASELINE"]

    # The following are settings for reviewer types
    # Varying reviewer commitment
    experiment_names += ["responsible_Rx1"]
    experiment_names += ["irresponsible_Rx1"]

    # Varying reviewer intention
    experiment_names += ["benign_Rx1"]
    experiment_names += ["malicious_Rx1"]

    # Varying reviewer knowledgeability
    experiment_names += ["knowledgeable_Rx1"]
    experiment_names += ["unknowledgeable_Rx1"]

    # The following are settings for AC types
    experiment_names += ["conformist_ACx1", "authoritarian_ACx1", "inclusive_ACx1"]

    # Enable these for ICLR2023
    if conference == "ICLR2023":
        experiment_names += ["no_rebuttal"]
        experiment_names += ["no_overall_score"]
        experiment_names += ["malicious_Rx2"]
        experiment_names += ["malicious_Rx3"]
        experiment_names += ["irresponsible_Rx2"]
        experiment_names += ["irresponsible_Rx3"]
        experiment_names += ["authors_are_famous_Rx1"]
        experiment_names += ["authors_are_famous_Rx2"]
        experiment_names += ["authors_are_famous_Rx3"]

    return experiment_names


def load_llm_ac_decisions_as_array(
    output_dir: str,
    experiment_name: str,
    ac_scoring_method: str,
    acceptance_rate: float,
    conference: str,
    model_name: str,
    num_papers_per_area_chair: int
) -> Tuple[np.ndarray, np.ndarray]:
    """Loads and processes GPT-4 generated area chair (AC) decisions for an experiment.

    Args:
        experiment_name (str): Name of the experiment.
        ac_scoring_method (str): Method used for AC scoring ('ranking' or 'recommendation').
        acceptance_rate (float): Acceptance rate for the conference.
        conference (str): Name of the conference.
        model_name (str): Model name used to generate AC decisions.
        num_papers_per_area_chair (int): Number of papers assigned to each area chair.

    Returns:
        Tuple[np.ndarray, np.ndarray]: An array of decisions (True for accept, False for reject)
            and an array of paper IDs in the order processed.

    Raises:
        NotImplementedError: If `ac_scoring_method` is not 'ranking' or 'recommendation'.
    """
    print("=" * 30)
    print(f"Experiment Name: {experiment_name}")

    llm_ac_decisions = load_llm_ac_decisions(
        output_dir=output_dir,
        conference=conference,
        model_name=model_name,
        ac_scoring_method=ac_scoring_method,
        experiment_name=experiment_name,
        num_papers_per_area_chair=num_papers_per_area_chair
    )

    paper_ids = sorted(
        int(paper_id) for batch in llm_ac_decisions for paper_id in batch
    )

    if ac_scoring_method == "ranking":
        if len(paper_ids) != len(set(paper_ids)):
            raise ValueError(f"Duplicate paper_ids found in the AC decisions: {Counter(paper_ids)}")

        papers_accepted_by_llm = get_papers_accepted_by_llm(llm_ac_decisions, acceptance_rate)
        decisions_llm = np.array([paper_id in papers_accepted_by_llm for paper_id in paper_ids])

    elif ac_scoring_method == "recommendation":
        llm_ac_decisions_flat = {int(k): v for batch in llm_ac_decisions for k, v in batch.items()}
        decisions_llm = np.array(
            [llm_ac_decisions_flat[paper_id].startswith("Accept") for paper_id in paper_ids]
        )
    else:
        raise NotImplementedError(f"Scoring method '{ac_scoring_method}' not implemented.")

    return decisions_llm, np.array(paper_ids)


def load_llm_ac_decisions(
    output_dir: str,
    conference: str,
    model_name: str,
    ac_scoring_method: str,
    experiment_name: str,
    num_papers_per_area_chair: int
) -> List[Dict[str, str]]:
    """Loads GPT-4 generated area chair (AC) decisions from a specified path.

    Args:
        conference (str): Name of the conference.
        model_name (str): Model name used to generate AC decisions.
        ac_scoring_method (str): Method used for AC scoring ('ranking' or 'recommendation').
        experiment_name (str): Name of the experiment.
        num_papers_per_area_chair (int): Number of papers assigned to each area chair.

    Returns:
        List[Dict[str, str]]: List of batches, where each batch contains paper ID and decision.

    Raises:
        AssertionError: If a non-final batch has a paper count different from `num_papers_per_area_chair`.
    """
    path = get_ac_decision_path(
        output_dir=output_dir,
        conference=conference,
        model_name=model_name,
        ac_scoring_method=ac_scoring_method,
        experiment_name=experiment_name
    )

    if osp.exists(path):
        with open(path, 'r', encoding='utf-8') as file:
            ac_decision = json.load(file)
        print(f"Loaded {len(ac_decision)} batches of existing AC decisions from {path}")
    else:
        ac_decision = []
        print(f"No existing AC decisions found at {path}")

    ac_decision = [batch for batch in ac_decision if batch]  # Remove empty batches

    for i, batch in enumerate(ac_decision):
        if i != len(ac_decision) - 1:
            if len(batch) != num_papers_per_area_chair:
                raise AssertionError(
                    f"Batch {i} has {len(batch)} papers, expected {num_papers_per_area_chair} for non-final batches."
                )

    return ac_decision

def write_to_excel(data, file_path, sheet_name):
    """
    Write data to an Excel file.

    Parameters:
    data (pd.DataFrame): The data to write to the Excel file.
    file_path (str): The path to the Excel file.
    sheet_name (str): The name of the sheet to write to.
    """
    # Check if the file exists
    if os.path.exists(file_path):
        # If the file exists, load it
        with pd.ExcelWriter(file_path, mode='a', engine='openpyxl', if_sheet_exists='replace') as writer:
            data.to_excel(writer, sheet_name=sheet_name, index=False)
    else:
        # If the file does not exist, create it
        with pd.ExcelWriter(file_path, engine='openpyxl') as writer:
            data.to_excel(writer, sheet_name=sheet_name, index=False)


def save_llm_ac_decisions(ac_decisions: List[dict], **kwargs):
    path = get_ac_decision_path(**kwargs)

    json.dump(ac_decisions, open(path, 'w', encoding='utf-8'), indent=2)


def get_model_name_short(name: str):
    """
    Convert long model names (e.g. `gpt-35-turbo`) to short model names (e.g. `gpt-35`)
    Args:
        name (str): long model name

    Returns:
        str: short model name
    """

    assert name.startswith('gpt-')
    return '-'.join(name.split('-')[:2])


def get_reviewer_types_from_experiment_name(experiment_name: str):
    if experiment_name in ["BASELINE", 'inclusive_ACx1', 'authoritarian_ACx1', 'conformist_ACx1',
                           "no_rebuttal"]:
        reviewer_types = ["BASELINE", "BASELINE", "BASELINE"]

    elif experiment_name == "benign_Rx1":

        reviewer_types = ["benign", "BASELINE", "BASELINE"]

    elif experiment_name == "benign_Rx2":

        reviewer_types = ["benign", "benign", "BASELINE"]

    elif experiment_name == "malicious_Rx1":

        reviewer_types = ["malicious", "BASELINE", "BASELINE"]

    elif experiment_name == "malicious_Rx2":

        reviewer_types = ["malicious", "malicious", "BASELINE"]

    elif experiment_name == "malicious_Rx3":

        reviewer_types = ["malicious", "malicious", "malicious"]

    elif experiment_name == "knowledgeable_Rx1":

        reviewer_types = ["knowledgeable", "BASELINE", "BASELINE"]

    elif experiment_name == "unknowledgeable_Rx1":

        reviewer_types = ["unknowledgeable", "BASELINE", "BASELINE"]

    elif experiment_name == "responsible_Rx1":

        reviewer_types = ["responsible", "BASELINE", "BASELINE"]

    elif experiment_name == "irresponsible_Rx1":

        reviewer_types = ["irresponsible", "BASELINE", "BASELINE"]

    elif experiment_name == "irresponsible_Rx2":

        reviewer_types = ["irresponsible", "irresponsible", "BASELINE"]

    elif experiment_name == "irresponsible_Rx3":

        reviewer_types = ["irresponsible", "irresponsible", "irresponsible"]

    elif experiment_name in ["no_overall_score"]:
        reviewer_types = ["NoOverallScore", "NoOverallScore", "NoOverallScore"]

    elif experiment_name in ["authors_are_famous_Rx1", "authors_are_famous_Rx1_no_rebuttal"]:

        reviewer_types = ["authors_are_famous", "BASELINE", "BASELINE"]

    elif experiment_name in ["authors_are_famous_Rx2", "authors_are_famous_Rx2_no_rebuttal"]:

        reviewer_types = ["authors_are_famous", "authors_are_famous", "BASELINE"]

    elif experiment_name in ["authors_are_famous_Rx3", "authors_are_famous_Rx3_no_rebuttal"]:

        reviewer_types = ["authors_are_famous", "authors_are_famous", "authors_are_famous"]

    else:
        raise NotImplementedError

    return reviewer_types
