from typing import Union

default_reviewer_setting = {
    "is_benign": None,
    "is_knowledgeable": None,
    "is_responsible": None,
    "provides_numeric_rating": True,
}


def get_experiment_settings(paper_id: Union[int, None] = None, paper_decision: Union[str, None] = None, setting: dict = None):
    """
    Generate experiment settings based on provided configurations for area chairs (AC) and reviewers.

    Args:
        setting (dict): A dictionary containing configuration for AC, reviewers, authors, and global settings.

    Returns:
        dict: Experiment settings including players (Paper Extractor, AC, Author, Reviewer)
              and global settings.
    """

    experiment_setting = {
        "paper_id": paper_id,
        "paper_decision": paper_decision,
        "players": {

            # Paper Extractor is a special player that extracts a paper from the dataset.
            # Its constructor does not take any arguments.
            "Paper Extractor": [{}],

            # Assume there is only one area chair (AC) in the experiment.
            "AC": [get_ac_setting_from_ac_type(ac_type) for ac_type in setting['AC']],

            # Author role with default configuration.
            "Author": [{}],

            # Reviewer settings are generated based on reviewer types provided in the settings.
            "Reviewer": [get_reviewer_setting_from_reviewer_type(reviewer_type) for reviewer_type in setting[
                'reviewer']],
        },
        "global_settings": setting['global_settings']
    }

    return experiment_setting


def get_reviewer_setting_from_reviewer_type(reviewer_type: str):
    """
    Map a reviewer type (e.g., 'benign', 'malicious') to a reviewer setting dictionary.

    Args:
        reviewer_type (str): The type of reviewer (e.g., 'benign', 'malicious', 'knowledgeable').

    Returns:
        dict: A dictionary representing the reviewer's attributes like is_benign, is_knowledgeable,
              is_responsible, or if they know the authors (e.g., 'famous', 'unfamous').

    Raises:
        ValueError: If an unknown reviewer type is provided.
    """
    reviewer_setting = {
        "is_benign": None,
        "is_knowledgeable": None,
        "is_responsible": None
    }

    # Intention
    if "benign" in reviewer_type:
        reviewer_setting["is_benign"] = True
    if "malicious" in reviewer_type:
        reviewer_setting["is_benign"] = False

    # Knowledgeability
    if "knowledgeable" in reviewer_type:
        reviewer_setting["is_knowledgeable"] = True
    if "unknowledgeable" in reviewer_type:
        reviewer_setting["is_knowledgeable"] = False

    # Commitment
    if "responsible" in reviewer_type:
        reviewer_setting["is_responsible"] = True
    if "irresponsible" in reviewer_type:
        reviewer_setting["is_responsible"] = False

    if reviewer_type in ["authors_are_famous"]:
        reviewer_setting["knows_authors"] = "famous"

    elif reviewer_type in ["authors_are_unfamous"]:
        reviewer_setting["knows_authors"] = "unfamous"

    return reviewer_setting


def get_ac_setting_from_ac_type(ac_type: str):
    """
    Generate the area chair (AC) settings based on the type of AC.

    Args:
        ac_type (str): The type of area chair (e.g., 'senior', 'junior').

    Returns:
        dict: A dictionary containing the area chair type.
    """

    ac_setting = {
        "area_chair_type": ac_type
    }

    return ac_setting
