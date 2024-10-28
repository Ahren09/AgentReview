"""
Process and classify ICLR submissions using OpenReview API.

This script processes ICLR submissions, classifies them into subdirectories
based on decisions, extracts paper content into JSON format, and checks the
validity of the processed papers.

It includes three main functions:
- classify_ICLR_submissions_into_subdirectories: Classifies papers into
  directories based on decisions.
- process_submission: Processes each submission by extracting text and saving
  it as a JSON file.
- check_processed_paper: Verifies if all processed papers are valid JSON files.
"""

import os
import sys
import traceback
from collections import Counter

from tqdm import tqdm

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from agentreview.arguments import parse_args
from agentreview.utility.utils import print_colored

decision_map = {
    # ICLR 2023
    "Reject": "Reject",
    "Accept: poster": "Accept-poster",
    "Accept: notable-top-25%": "Accept-notable-top-25",
    "Accept: notable-top-5%": "Accept-notable-top-5",

    # ICLR 2022
    "Accept (Poster)": "Accept-poster",
    "Accept (Oral)": "Accept-oral",
    "Accept (Spotlight)": "Accept-spotlight",

    # ICLR 2021
    "Significant concerns (Do not publish)": "Significant-concerns",
    "Concerns raised (can publish with adjustment)": "Concerns-raised",

    # ICLR 2020
    "Accept (Talk)": "Accept-oral",  # We assume this signifies an oral presentation

    # ICLR 2018
    "Invite to Workshop Track": "Reject"
}


def categorize_ICLR_submissions_into_subdirectories():
    """Classifies ICLR submissions into subdirectories based on review decisions.

    This function iterates through the review notes and identifies the decision
    (recommendation or final decision) for each submission. It then moves the
    notes and their corresponding papers into directories based on the decision.

    Raises:
        AssertionError: If the line containing the decision does not have the
                        expected format.
    """
    note_dir = f"data/{args.conference}/notes"
    paper_dir = f"data/{args.conference}/paper"

    for note in os.listdir(note_dir):
        print(note)

        # Skip directories or irrelevant files
        if os.path.isdir(os.path.join(note_dir, note)) or ".DS_Store" in note:
            continue

        note_path = os.path.join(note_dir, note)
        lines = open(note_path, "r").readlines()
        decision = None

        for line in tqdm(lines):
            if "\"recommendation\"" in line:
                assert Counter(line)["\""] == 4, "Unexpected format in recommendation line."
                print(line)
                decision = line.split("\"recommendation\"")[1].split("\"")[1]
                break

            elif "\"decision\"" in line:
                assert Counter(line)["\""] == 4, "Unexpected format in decision line."
                print(line)
                try:
                    decision = line.split("\"decision\"")[1].split("\"")[1]
                    break
                except Exception:
                    traceback.print_exc()
                    print_colored(line, 'red')

        if decision is None:
            # Possibly withdrawn papers
            print_colored(f"Could not find decision for {note}", "red")
            continue

        os.makedirs(os.path.join(note_dir, decision_map[decision]), exist_ok=True)
        os.makedirs(os.path.join(paper_dir, decision_map[decision]), exist_ok=True)
        os.rename(note_path, os.path.join(note_dir, decision_map[decision], note))

        paper_id = int(note.split(".json")[0])
        paper_path = os.path.join(paper_dir, f"{paper_id}.pdf")
        os.rename(paper_path, os.path.join(paper_dir, decision_map[decision], f"{paper_id}.pdf"))


if __name__ == "__main__":
    args = parse_args()

    # Extract contents of each paper into a JSON file
    categorize_ICLR_submissions_into_subdirectories()