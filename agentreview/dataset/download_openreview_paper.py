"""
Download all papers from one year of ICLR conference using OpenReview API.

This script downloads all paper PDFs and their corresponding metadata
from the ICLR 2023 conference using the OpenReview API.

Alternative methods to download can be found in this
[colab notebook](https://colab.research.google.com/drive/1vXXNxn8lnO3j1dgoidjybbKIN0DW0Bt2),
though it's not used here.
"""

import glob
import json
import os
import time
import requests

from arguments import parse_args

try:
    import openreview
except ImportError:
    raise ImportError("Please install openreview package using `pip install openreview-py`")

def download_papers():
    """Downloads all papers from ICLR 2023 using OpenReview API.

    This function authenticates with the OpenReview API using environment
    variables for the username and password. It then iterates through the
    available papers, downloads the PDF, and saves the corresponding metadata
    (in JSON format) in the specified directories.

    Raises:
        AssertionError: If the OPENREVIEW_USERNAME or OPENREVIEW_PASSWORD environment
                        variables are not set.
        AssertionError: If the conference argument is not for ICLR.
    """

    args = parse_args()

    openreview_username = os.environ.get("OPENREVIEW_USERNAME")
    openreview_password = os.environ.get("OPENREVIEW_PASSWORD")

    assert openreview_username is not None, (
        "Please set your OpenReview username through the OPENREVIEW_USERNAME environment variable."
    )
    assert openreview_password is not None, (
        "Please set your OpenReview password through the OPENREVIEW_PASSWORD environment variable."
    )

    client = openreview.Client(
        baseurl='https://api.openreview.net',
        username=openreview_username,
        password=openreview_password
    )

    page_size = 1000
    offset = 0
    papers_directory = os.path.join(args.data_dir, args.conference, "paper")
    notes_directory = os.path.join(args.data_dir, args.conference, "notes")

    assert "ICLR" in args.conference, "Only works for ICLR conferences!"
    year = int(args.conference.split("ICLR")[-1])  # Only works for ICLR currently
    ids = []

    # Create directories if they don't exist
    for path in [papers_directory, notes_directory]:
        os.makedirs(path, exist_ok=True)

    while True:
        # Fetch submissions with pagination
        notes = client.get_notes(
            invitation=f'ICLR.cc/{year}/Conference/-/Blind_Submission',
            details='all',
            offset=offset,
            limit=page_size
        )

        if not notes:
            break  # Exit if no more notes are available

        # Get existing paper IDs to avoid re-downloading
        existing_papers = glob.glob(f"{papers_directory}/*.pdf")
        existing_paper_ids = {int(os.path.basename(paper).split(".pdf")[0]) for paper in existing_papers}

        for note in notes:
            paper_id = note.number
            paper_path = os.path.join(papers_directory, f"{paper_id}.pdf")
            note_path = os.path.join(notes_directory, f"{paper_id}.json")

            # Skip existing papers
            if paper_id in existing_paper_ids:
                print(f"Paper {paper_id} already downloaded.")
                continue

            print(f"Title: {note.content.get('title', 'N/A')}")
            print(f"Abstract: {note.content.get('abstract', 'N/A')}")
            print(f"TL;DR: {note.content.get('TL;DR', 'N/A')}")
            pdf_link = f"https://openreview.net/pdf?id={note.id}"
            print(f"PDF Link: {pdf_link}")

            # Attempt to download the paper PDF, retry if fails
            tries = 0
            while tries < 10:
                try:
                    response = requests.get(pdf_link)

                    if response.status_code == 200:
                        
                        with open(paper_path, "wb") as pdf_file:
                            pdf_file.write(response.content)

                        print(f"PDF downloaded successfully as {paper_path}")

                        # Save metadata as JSON, which contains the reviews, rebuttals, and decisions. 
                        with open(note_path, "w") as note_file:
                            json.dump(note.to_json(), note_file, indent=2)

                        break

                    else:
                        print(f"Attempt {tries} failed. Status code: {response.status_code}")
                        if response.status_code == 429:  # Too many requests
                            print("Too many requests. Sleeping for 10 seconds.")
                            time.sleep(10)

                except Exception as e:
                    print(f"Attempt {tries} failed with error: {e}")

                tries += 1

        offset += page_size


if __name__ == "__main__":
    download_papers()
