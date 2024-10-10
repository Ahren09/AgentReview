import re

from colorama import Fore

problem_pattern = r"(problem|issue|challenge)"
importance_pattern = r"\b(important|challenging|crucial|critical|vital|significant)\b"
interesting_pattern = r"\b(interesting|fascinating|intriguing|exciting)\b"

novel_pattern = r"\b(novel|new|original|innovative|creative)\b"
model_pattern = r"(model|architecture|method|approach|framework)"

experiment_pattern =r"\b(evaluate|evaluation|comparison|result|experiment[s])\b|\b(analysis|analyses)\b"
result_pattern = r"\b(result|performance|metric|score)\b"

insight_pattern = r"\b(insight|observation|finding|trend)\b"


limitation_pattern = r"(limitation|drawback|weakness|challenge)"

scalability_pattern = r"\b(complexity|scalability|scalable)\b"

real_world_pattern = r"realistic|real\-world|practical"


theoretical_pattern = r"\b(math|theoretical|justification|justify|foundation|theory)\b"



def text_match_problem(text):
    """Regex patterns to search for problem-related and importance-related keywords"""

    # Check if both patterns are found in the text
    return re.search(problem_pattern, text, re.IGNORECASE) and (re.search(importance_pattern, text, re.IGNORECASE)
                                                                or re.search(interesting_pattern, text, re.IGNORECASE))


def text_match_dataset(text):
    """
    Check if the strengths mentioned by reviewers contains the word "dataset" or "data set".

    """
    return re.search(r"\b(dataset|data set)\b", text, re.IGNORECASE)


def text_match_model(text):
    """
    Check if the strengths mentioned by reviewers contains the word "model".
    """
    return re.search(model_pattern, text, re.IGNORECASE)

def text_match_experiment(text):
    """
    Check if the strengths mentioned by reviewers contains the word "experiment".
    """
    return re.search(experiment_pattern, text, re.IGNORECASE) or re.search(result_pattern, text, re.IGNORECASE)

def text_match_real_world(text):
    """
    Check if the strengths mentioned by reviewers contains the word "model".
    """
    return re.search(real_world_pattern, text, re.IGNORECASE)

def text_match_theoretical(text):
    """
    Check if the strengths mentioned by reviewers are related to theoretical analysis / foundation.
    """
    return re.search(theoretical_pattern, text, re.IGNORECASE)

def text_match_scalability(text):
    """
    Check if the strengths mentioned by reviewers are related to scalability or time/space complexity.
    """
    return re.search(scalability_pattern, text, re.IGNORECASE)

def match_strengths(text):
    """
    Check if the strengths mentioned by reviewers contains the word "model".
    """
    for category, f in {"problem": text_match_problem,
                        "dataset": text_match_dataset,
                        "model": text_match_model,
                        "limitation": text_match_limitation,
                        "experiment": text_match_experiment,
                        "theoretical-analysis": text_match_theoretical,
                        "scalability": text_match_scalability,
                        }.items():
        if f(text):
            return category

    print(
        Fore.RED
        + f"No category found for weaknesses: {text}"
        + Fore.BLACK
    )

def match_weaknesses(text):
    for category, f in {"problem": text_match_problem,
                        "dataset": text_match_dataset,
                        "model": text_match_model,
                        "limitation": text_match_limitation,
                        "experiment": text_match_experiment,
                        "real-world": text_match_real_world,
                        "theoretical-analysis": text_match_theoretical,
                        "scalability": text_match_scalability,
                        }:
        if f(text):
            return category

    print(
        Fore.RED
        + f"No category found for weaknesses: {text}"
        + Fore.BLACK
    )
    return None

    raise ValueError(f"No category found for weaknesses: {text}")




def text_match_limitation(text):
    """
    Check if the strengths mentioned by reviewers contains the word "model".
    """
    return re.search(limitation_pattern, text, re.IGNORECASE)