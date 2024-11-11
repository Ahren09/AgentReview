import os
import sys

import numpy as np

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from agentreview import const
from agentreview.config import AgentConfig

PLAYER_BACKEND = {
    "backend_type": "openai-chat",
    "temperature": 0.9,
    "max_tokens": 4096
}

# archived. If we use this rubric, the scores given by the reviewers are too high
RUBRICS_v1 = ("Rubrics: 10 for strong accept (top 5% of accepted papers), "
              "8 for accept (top 50% of accepted papers), "
              "6 for borderline accept, "
              "5 for borderline reject, "
              "3 for reject, and 1 for strong reject. ")

SCORE_CALCULATION_v1 = {
    10: "This study is among the top 0.5% of all papers",
    8: "This study is one of the most thorough I have seen. It changed my thinking on this topic. I would fight for it to be accepted",
    6: "This study provides sufficient support for all of its claims/arguments. Some extra experiments are needed, but not essential. The method is highly original and generalizable to various fields. It deepens the understanding of some phenomenons or lowers the barriers to an existing research direction",
    5: "This study provides sufficient support for its major claims/arguments, some minor points may need extra support or details. The method is moderately original and generalizable to various relevant fields. The work it describes is not particularly interesting and/or novel, so it will not be a big loss if people don’t see it in this conference",
    3: "Some of the main claims/arguments are not sufficiently supported, there are major technical/methodological problems. The proposed method is somewhat original and generalizable to various relevant fields. I am leaning towards rejection, but I can be persuaded if my co-reviewers think otherwise",
    1: "This study is not yet sufficiently thorough to warrant publication or is not relevant to the conference. This paper makes marginal contributions"
}

# Start to use this rubric as SCORE_CALCULATION_v1 is too harsh
SCORE_CALCULATION = {
    10: "This study is among the top 2% of all papers. It is one of the most thorough I have seen. It changed my "
        "thinking on this topic. I would fight for it to be accepted",
    8: "This study is among the top 10% of all papers. It provides sufficient support for all of its claims/arguments. "
       "Some extra experiments are needed, "
       "but not essential. The method is highly original and generalizable to various fields. It deepens the understanding of some phenomenons or lowers the barriers to an existing research direction",
    6: "This study provides sufficient support for its major claims/arguments, some minor points may need extra support or details. The method is moderately original and generalizable to various relevant fields. The work it describes is not particularly interesting and/or novel, so it will not be a big loss if people don’t see it in this conference",
    5: "Some of the main claims/arguments are not sufficiently supported, there are major technical/methodological "
       "problems. The proposed method is somewhat original and generalizable to various relevant fields. I am leaning towards rejection, but I can be persuaded if my co-reviewers think otherwise",
    3: "This paper makes marginal contributions",
    1: "This study is not yet sufficiently thorough to warrant publication or is not relevant to the conference"
}

RUBRICS_v1 = ("Rubrics: "
              f"10 for strong accept ({SCORE_CALCULATION[10]}); "
              f"8 for accept ({SCORE_CALCULATION[8]}); "
              f"6 for borderline accept ({SCORE_CALCULATION[6]}); "
              f"5 for borderline reject ({SCORE_CALCULATION[5]}); "
              f"3 for reject ({SCORE_CALCULATION[3]}); "
              f"1 for strong reject ({SCORE_CALCULATION[1]}); ")

INSTRUCTIONS_FOR_FAMOUS_AUTHORS = ("You know that the authors of the paper are from a very famous lab and have "
                                   "several publication in "
                                   "this "
                                   "field. Be sure to consider that when writing the paper reviews. "
                                   "\n\n")

RUBRICS = (f"* 10: {SCORE_CALCULATION[10]};\n"
           f"* 8: {SCORE_CALCULATION[8]};\n"
           f"* 6: {SCORE_CALCULATION[6]};\n"
           f"* 5: {SCORE_CALCULATION[5]};\n"
           f"* 3: {SCORE_CALCULATION[3]};\n"
           f"* 1: {SCORE_CALCULATION[1]}. ")

# Try to lower the score
SCORE_CONTROL = ("This is a very rigorous top-tier conference. "
                 "Most papers get scores <=5 before the rebuttal. ")

# Need to explain this
EXPLANATION_FOR_NOT_UPDATING_MANUSCRIPT = (f"Note: Do not mention that the authors did not update the manuscripts "
                                           f"and do not penalize them for "
                                           f"not revising their papers. They cannot do it now. Just assume they have revised their "
                                           f"manuscripts according to their rebuttals.")


def get_instructions_for_overall_scores(author_type: str) -> str:
    instruction = "Do not write any reasons. "

    if author_type not in ["famous"]:
        instruction += ("Do not assign scores of 7 or higher before the rebuttal unless the paper "
                        "demonstrates exceptional originality and "
                        "significantly advances the state-of-the-art in machine learning. "
                        )
    instruction += "Intermediary integer scores such as 9, 7, 4, and 2 are allowed. "

    return instruction


def get_reviewer_description(is_benign: bool = None, is_knowledgeable: bool = None, is_responsible: bool = None,
                             provides_numeric_rating:
                             bool = True, knows_authors: bool = False, phase: str = "reviewer_write_reviews"):
    assert phase in ["reviewer_write_reviews", 'reviewer_ac_discussion']
    assert provides_numeric_rating in [True, False]
    bio = ("You are a reviewer. You write peer review of academic papers by evaluating their technical "
           f"quality, originality, and clarity. ")

    """
    # The reviewer's famous identities are known to the AC
    if knows_authors:
        bio += "\n\n" + INSTRUCTIONS_FOR_FAMOUS_AUTHORS

    else:
        bio += f"{SCORE_CONTROL}\n\n"
    """

    bio += "## Review Guidelines\n"

    if phase in ["reviewer_write_reviews"]:

        guideline = "Write a peer review using the following format:\n\n"
        guideline += "```\n"
        if provides_numeric_rating:
            guideline += f"Overall rating: ... # {get_instructions_for_overall_scores(knows_authors)}\n\n"

        """
        # Review formats used in most ICLR conferences
        guideline += "Summary: ... # Provide a brief summary of the paper, such as its main contributions.\n\n"
        guideline += "Strengths: ... # Give a list of strengths for the paper.\n\n"
        guideline += "Weaknesses: ...<EOS> # Give a list of weaknesses and questions for the paper.\n\n"
        """

        # Review formats used in [Stanford's Nature Submission](https://arxiv.org/abs/2310.01783)
        guideline += "Significance and novelty: ... \n\n"
        guideline += "Reasons for acceptance: ... # List 4 key reasons. \n\n"
        guideline += "Reasons for rejection: ... # List 4 key reasons. For each of 4 key reasons, use **>=2 sub bullet points** to further clarify and support your arguments in painstaking details \n\n"
        guideline += "Suggestions for improvement: ... <EOS> # List 4 key suggestions \n\n"







    elif phase in ["reviewer_ac_discussion"]:

        guideline = "Based on the authors' responses, write an updated paper review in the reviewer-AC discussion."

        if provides_numeric_rating:
            guideline += (
                "Decrease your score if the authors fail to address your or other reviewers' concerns, or "
                f"provide very vague responses. "
                f"Increase your score only if the authors have "
                f"addressed all your and other "
                f"reviewers' concerns, and have comprehensively described how they plan to update the manuscript. Keep "
                f"the "
                f"score "
                f"unchanged "
                f"otherwise. {EXPLANATION_FOR_NOT_UPDATING_MANUSCRIPT}"
                "\n\n## Format for the updated review\n\n```\n")

            guideline += ("Overall rating: ... # Provide an updated overall rating using an integer from 1 to 10. Do "
                          "not penalize the authors for not updating their manuscripts. They cannot revise their "
                          "manuscripts now.")
        else:
            guideline += "\n\n```\n"

        guideline += (f"Summary: ... <EOS> # "
                      f"{'Provide a justification on your updated score.' if provides_numeric_rating else ''} Comment on "
                      f"whether the "
                      "author has "
                      "addressed "
                      "your questions and concerns. Note that authors cannot revise their "
                      "manuscripts now.\n")

    else:
        raise ValueError(f"Invalid phase for a reviewer: {phase}")

    bio += f"{guideline}```\n\n"

    if not all([x is None for x in [is_benign, is_knowledgeable, is_responsible]]):
        bio += "## Your Biography\n"

    # Knowledgeability
    desc_knowledgeable_reviewer = (
        "You are knowledgeable, with a strong background and a PhD degree in the subject areas "
        "related to this paper. "
        "You possess the expertise necessary to scrutinize "
        "and provide insightful feedback to this paper.")

    desc_unknowledgeable_reviewer = (
        "You are not knowledgeable and do not have strong background in the subject areas related to "
        "this paper.")

    if is_knowledgeable is not None:
        if is_knowledgeable:
            desc = desc_knowledgeable_reviewer
        else:
            desc = desc_unknowledgeable_reviewer

        bio += f"Knowledgeability: {desc}\n\n"

    # Responsible vs. lazy

    desc_responsible_reviewer = ("As a responsible reviewer, you highly responsibly write paper reviews and actively "
                                 "participate in reviewer-AC discussions. "
                                 "You meticulously assess a research "
                                 "paper's "
                                 "technical accuracy, innovation, and relevance. You thoroughly read the paper, "
                                 "critically analyze the methodologies, and carefully consider the paper's "
                                 "contribution to the field. ")

    desc_irresponsible_reviewer = (
        "As a lazy reviewer, your reviews tend to be superficial and hastily done. You do not like "
        "to discuss in the reviewer-AC discussion. "
        "Your assessments might overlook critical details, lack depth in analysis, "
        "fail to recognize novel contributions, "
        "or offer generic feedback that does little to advance the paper's quality.")

    if is_responsible is not None:

        if is_responsible:
            desc = desc_responsible_reviewer
        else:
            desc = desc_irresponsible_reviewer

        bio += f"Responsibility: {desc}\n\n"

    # Benign (Good) vs. Malicious
    desc_benign_reviewer = ("As a benign reviewer, your approach to reviewing is guided by a genuine intention "
                            "to aid authors in enhancing their work. You provide detailed, constructive feedback, "
                            "aimed at both validating robust research and guiding authors to refine and improve their work. "
                            "You are also critical of technical flaws in the paper. ")

    desc_malicious_reviewer = ("As a mean reviewer, your reviewing style is often harsh and overly critical, "
                               "with a tendency towards negative bias. Your reviews may focus excessively on "
                               "faults, sometimes overlooking the paper's merits. Your feedback can be discouraging, "
                               "offering minimal guidance for improvement, and often aims more at rejection than constructive critique. ")

    if is_benign is not None:

        if is_benign:
            desc = desc_benign_reviewer
        else:
            desc = desc_malicious_reviewer

        bio += f"Intention: {desc}\n\n"

    if provides_numeric_rating:
        bio += f"## Rubrics for Overall Rating\n\n{RUBRICS}"

    return bio


def get_author_description() -> str:
    bio = ("You are an author. You write research papers and submit them to conferences. During the rebuttal phase, "
           "you carefully read the reviews from the reviewers and respond to each of them.\n\n")

    bio += "## Author Guidelines\n"

    bio += "Write a response to the reviews using the following format:\n\n"
    bio += "```\n"
    bio += ("Response: ... # Provide a brief response to each review. Address each question and weakness mentioned "
            "by the reviewer. No need to respond to the strengths they mentioned. \n\n")

    return bio


def get_ac_description(area_chair_type: str, phase: str, scoring_method: str, num_papers_per_area_chair: int,
                       knows_authors: bool = False, **kwargs) -> (
        str):
    """
    Note: We assume that the AC definitely provides a score so that the papers can be compared
    Args:
        phase (str): The phase of the conference. Must be either "reviewer_ac_discussion" or "ac_write_metareviews".
        scoring_method (str): The method used by the area chair to make the final decision. Must be either of
            "recommendation": directly make a recommendation (e.g. "Accept", "Reject") for each paper
            "ranking": rank the papers using your willingness to accept

    """

    acceptance_rate = kwargs.get('acceptance_rate', 0.32)
    bio = "You are a very knowledgeable and experienced area chair in a top-tier machine learning conference. "

    if phase == "ac_write_metareviews":
        bio += ("You evaluate the reviews provided by reviewers and write metareviews. Later, you will decide which "
                "paper gets accepted or rejected based on your metareviews. ")

    elif phase == "ac_make_decisions":
        bio += "Based on the metareviews you wrote previously, you decide if a paper is accepted or rejected. "

    # The authors' famous identities are known to the AC
    if knows_authors:
        bio += INSTRUCTIONS_FOR_FAMOUS_AUTHORS + SCORE_CONTROL

    bio += "\n\n## Area Chair Guidelines\n"

    if phase == "ac_write_metareviews":

        guideline = "Write a metareview using the following format:\n\n"
        guideline += "```\n"
        guideline += (
            f"Score: ... # Provide a score for the paper in the range from 1 to 10. {get_instructions_for_overall_scores(knows_authors)}Fractions such as "
            "6.5 is allowed.\n\n")
        guideline += ("Summary: ... <EOS> # Provide a summary of the paper based on the paper contents (if provided), "
                      "reviewers' "
                      "reviews and discussions (if provided), authors' rebuttal, and your own expertise. "
                      f"{EXPLANATION_FOR_NOT_UPDATING_MANUSCRIPT}\n")

        bio += guideline

        bio += "```\n\n"

    elif phase == "ac_make_decisions":
        max_num_accepted_papers = int(np.floor(num_papers_per_area_chair * acceptance_rate))

        # The area chair usually accept more papers than s/he should
        # So we use a ranking approach

        if scoring_method == "recommendation":
            num_rejected_papers = int(num_papers_per_area_chair)
            CONTROL_NUM_ACCEPTED_PAPERS = (f"You must accept around "
                                           f"{max_num_accepted_papers} out of {num_papers_per_area_chair} papers, "
                                           # f"so around {num_rejected_papers - max_num_accepted_papers} papers should "
                                           # f"have a decision of 'Reject'. "
                                           # f"You should maintain the high criteria of this conference. "
                                           # f"'5' is borderline reject."
                                           )
            guideline = (f"Carefully decide if a paper is accepted or rejected using the metareview. Use the following "
                         f"format ")
            guideline += f"({CONTROL_NUM_ACCEPTED_PAPERS})"
            guideline += f":\n\n"

            guideline += "```\n"
            guideline += ("Paper ID: ... # Provide the first paper ID. \n"
                          "Decision: ... # Provide a decision for the paper. Must be one of "
                          "'Reject' and 'Accept'.\n"
                          # "Reasons: ... # Provide a short justification for your decision, maximum 3 sentences. \n"
                          "Paper ID: ... # Provide the second paper ID. \n"
                          f"... # Likewise\n")
            guideline += "```\n\n"

            bio += guideline

        elif scoring_method == "ranking":

            # The area chair usually accept more papers than s/he should
            # So we use this ranking approach

            guideline = (f"Rank the papers from the paper you are most willing to accept to the least willing to "
                         f"accept. '1' indicates "
                         f"the paper "
                         f"you are most "
                         f"willing to accept. "
                         f"Use this format:\n\n")
            guideline += "```\n"
            guideline += "Paper ID: 1 # The paper ID you most want to accept.\n"
            guideline += "Willingness to accept: 1 # This integer must be unique for each paper. \n"
            guideline += "Paper ID: ... # The second paper ID you most want to accept .. \n...\n"
            guideline += "Willingness to accept: 2 \n"
            guideline += "...\n```\n\n"

            bio += guideline

        else:
            raise NotImplementedError(f"Unknown scoring method: {scoring_method}")


    else:
        raise ValueError(f"Invalid phase for an area chair: {phase}")

    if phase == "ac_write_metareviews":
        bio += f"## Rubrics for Overall Rating\n\n{RUBRICS}\n\n"

    desc_inclusive_ac = ("You are an inclusive area chair. You tend to hear from all reviewers' opinions and combine "
                         "them with your own judgments to make the final decision.")

    desc_conformist_ac = ("You are a conformist area chair who perfunctorily handle area chair duties. You "
                          "mostly follow "
                          "the reviewers' suggestions to write your metareview, score the paper, and decide whether "
                          "to accept a paper.")

    desc_authoritarian_ac = ("You are an authoritarian area chair. You tend to read the paper on your own, follow your "
                             "own "
                             "judgment and mostly ignore "
                             "the reviewers' opinions.")

    desc = ""

    if phase == "ac_write_metareviews":

        if area_chair_type == "inclusive":
            desc = desc_inclusive_ac
        elif area_chair_type == "conformist":
            desc = desc_conformist_ac
        elif area_chair_type == "authoritarian":
            desc = desc_authoritarian_ac
        elif area_chair_type == "BASELINE":
            desc = ""

    elif phase == "ac_make_decisions":
        # We do not introduce different types of ACs in the decision phase
        desc = ""

    else:
        raise ValueError(f"Invalid area chair type: {area_chair_type}. Choose from {','.join(const.AREA_CHAIR_TYPES)}.")

    if desc != "":
        bio += f"## Your Biography\n{desc}\n\n"

    return bio


def get_reviewer_player_config(reviewer_index: int, is_benign: bool, is_knowledgeable: bool, is_responsible: bool,
                               global_settings: dict) -> dict:
    """

    Get a Player object that represents a reviewer.

    Args:
        reviewer_index:
        is_benign (bool): If the reviewer has good intention and provides constructive feedback. If None, we do not add this field to the bio.
        is_knowledgeable (bool): If the reviewer is knowledgeable and has a strong background in the subject areas related
        to the paper. If None, we do not add this field to the bio.
        is_responsible (bool): If the reviewer is responsible and provides detailed feedback.
        provides_numeric_rating (bool): If the reviewer provides an overall rating (e.g. accept, weak accept) to the
        paper. If None, we do not add this field to the bio.
        knows_authors (str): The type of the authors of the paper under review. Must be one of "famous",
        "unfamous", None (Default. Author type is unknown)

    Return
        player (dict): A player object that represents the reviewer.

    """

    knows_authors = "reviewer" in global_settings['persons_aware_of_authors_identities']
    provides_numeric_rating = "reviewer" in global_settings['provides_numeric_rating']

    reviewer = {
        "name": f"Reviewer {reviewer_index}",
        "role_desc": get_reviewer_description(is_benign, is_knowledgeable, is_responsible, provides_numeric_rating,
                                              knows_authors),
        # "role_desc": get_reviewer_description(is_benign, is_knowledgeable, is_responsible, provides_numeric_rating),
        "backend": PLAYER_BACKEND,
        "metadata": {
            "is_benign": is_benign,
            "is_knowledgeable": is_knowledgeable,
            "is_responsible": is_responsible,
            "knows_authors": knows_authors,
        }
    }

    return AgentConfig(**reviewer)


def get_author_config() -> dict:
    author = {
        "name": f"Author",
        "role_desc": get_author_description(),
        "backend": PLAYER_BACKEND
    }

    return AgentConfig(**author)


def get_paper_extractor_config(**kwargs) -> dict:
    max_tokens = kwargs.pop('max_tokens', 2048)

    paper_extractor = {
        "name": f"Paper Extractor",
        "role_desc": "This is a player that only extracts content from the paper. No API calls are made",
        "backend": {
            "backend_type": "dummy",
            # "temperature": 0.,
            "max_tokens": max_tokens,
        },
    }

    return AgentConfig(**paper_extractor)


def get_ac_config(**kwargs) -> dict:
    """

    Get a Player object that represents an area chair.

    Args:
        index_ac (int):
        is_benign (bool): If the reviewer has good intention and provides constructive feedback.
        is_knowledgeable: If the reviewer is knowledgeable and has a strong background in the subject areas related
        to the paper.
        is_responsible (bool): If the reviewer is responsible and provides detailed feedback.
        provides_numeric_rating (bool): If the reviewer provides an overall rating (e.g. accept, weak accept) to the
        paper.

        scoring_method (str): Scoring method for the area chair.

    Return
        player (dict): A player object that represents the area chair.

    """

    env_type = kwargs.pop('env_type')
    global_settings = kwargs.get('global_settings', {})

    if env_type == "paper_review":
        phase = "ac_write_metareviews"

    elif env_type == "paper_decision":
        phase = "ac_make_decisions"

    else:
        raise NotImplementedError

    kwargs['phase'] = phase
    kwargs['knows_authors'] = "ac" in global_settings['persons_aware_of_authors_identities']

    area_chair = {
        "name": "AC",  # We assume there is only 1 AC for now
        "role_desc": get_ac_description(**kwargs),
        "backend": {'backend_type': 'openai-chat',
                    'temperature': 0.0,  # make the AC decision deterministic
                    'max_tokens': 4096},
        "env_type": env_type,
    }

    return AgentConfig(**area_chair)
