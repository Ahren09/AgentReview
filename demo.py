#!/usr/bin/env python
# coding: utf-8

# # AgentReview
# 
# 
# 
# In this tutorial, you will explore customizing the AgentReview experiment.
# 
# 📑 Venue: EMNLP 2024 (Oral)
# 
# 🔗 arXiv: [https://arxiv.org/abs/2406.12708](https://arxiv.org/abs/2406.12708)
# 
# 🌐 Website: [https://agentreview.github.io/](https://agentreview.github.io/)
# 
# ```bibtex
# @inproceedings{jin2024agentreview,
#   title={AgentReview: Exploring Peer Review Dynamics with LLM Agents},
#   author={Jin, Yiqiao and Zhao, Qinlin and Wang, Yiyang and Chen, Hao and Zhu, Kaijie and Xiao, Yijia and Wang, Jindong},
#   booktitle={EMNLP},
#   year={2024}
# }
# ```
# 

# In[2]:


import os

import numpy as np

from agentreview import const

os.environ["OPENAI_API_VERSION"] = "2024-06-01-preview"


# ## Overview
# 
# AgentReview features a range of customizable variables, such as characteristics of reviewers, authors, area chairs (ACs), as well as the reviewing mechanisms 

# In[3]:



# ## Review Pipeline
# 
# The simulation adopts a structured, 5-phase pipeline (Section 2 in the [paper](https://arxiv.org/abs/2406.12708)):
# 
# * **I. Reviewer Assessment.** Each manuscript is evaluated by three reviewers independently.
# * **II. Author-Reviewer Discussion.** Authors submit rebuttals to address reviewers' concerns;
# * **III. Reviewer-AC Discussion.** The AC facilitates discussions among reviewers, prompting updates to their initial assessments.
# * **IV. Meta-Review Compilation.** The AC synthesizes the discussions into a meta-review.
# * **V. Paper Decision.** The AC makes the final decision on whether to accept or reject the paper, based on all gathered inputs.

# In[2]:



# In[4]:


import os

if os.path.basename(os.getcwd()) == "notebooks":
    os.chdir("..")
# Change the working directory to AgentReview
print(f"Changing the current working directory to {os.path.basename(os.getcwd())}")


# In[5]:


from argparse import Namespace

args = Namespace(openai_key=None, 
          deployment=None, 
          openai_client_type='azure_openai', 
          endpoint=None, 
          api_version='2023-05-15',
          ac_scoring_method='ranking', 
          conference='ICLR2024', 
          num_reviewers_per_paper=3,  
          ignore_missing_metareviews=False, 
          overwrite=False, 
          num_papers_per_area_chair=10, 
          model_name='gpt-4o', 
          output_dir='outputs', 
          max_num_words=16384, 
          visual_dir='outputs/visual', 
          device='cuda', 
          data_dir='./data', # Directory to all paper PDF
          acceptance_rate=0.32, 
          task='paper_review')

os.environ['OPENAI_API_VERSION'] = args.api_version

# In[13]:


malicious_Rx1_setting = {
    "AC": [
        "BASELINE"
    ],

    "reviewer": [
        "malicious",
        "BASELINE",
        "BASELINE"
    ],

    "author": [
        "BASELINE"
    ],
    "global_settings":{
        "provides_numeric_rating": ['reviewer', 'ac'],
        "persons_aware_of_authors_identities": []
    }
}

all_settings = {"malicious_Rx1": malicious_Rx1_setting}
args.experiment_name = "malicious_Rx1_setting"


# 
# `malicious_Rx1` means 1 reviewer is a malicious reviewer, and the other reviewers are default (i.e. `BASELINE`) reviewers.
# 
# 

# ## Reviews
# 
# Define the review pipeline

# In[10]:


from agentreview.environments import PaperReview

def review_one_paper(paper_id, setting):
    paper_decision = paper_id2decision[paper_id]

    experiment_setting = get_experiment_settings(paper_id=paper_id,
                                                 paper_decision=paper_decision,
                                                 setting=setting)
    print(f"Paper ID: {paper_id} (Decision in {args.conference}: {paper_decision})")

    players = initialize_players(experiment_setting=experiment_setting, args=args)

    player_names = [player.name for player in players]

    env = PaperReview(player_names=player_names, paper_decision=paper_decision, paper_id=paper_id,
                          args=args, experiment_setting=experiment_setting)

    arena = PaperReviewArena(players=players, environment=env, args=args)
    arena.launch_cli(interactive=False)


# In[11]:


import os
import sys

sys.path.append(os.path.abspath(os.path.join(os.getcwd(), "agentreview")))

from agentreview.paper_review_settings import get_experiment_settings
from agentreview.paper_review_arena import PaperReviewArena
from agentreview.utility.experiment_utils import initialize_players
from agentreview.utility.utils import project_setup, get_paper_decision_mapping


# In[14]:


sampled_paper_ids = [39]

paper_id2decision, paper_decision2ids = get_paper_decision_mapping(args.data_dir, args.conference)

for paper_id in sampled_paper_ids:
    review_one_paper(paper_id, malicious_Rx1_setting)



def run_paper_decision():
    args.task = "paper_decision"

    # Make sure the same set of papers always go through the same AC no matter which setting we choose
    NUM_PAPERS = len(const.year2paper_ids[args.conference])
    order = np.random.choice(range(NUM_PAPERS), size=NUM_PAPERS, replace=False)


    # Paper IDs we actually used in experiments
    experimental_paper_ids = []

    # For papers that have not been decided yet, load their metareviews
    metareviews = []
    print("Shuffling paper IDs")
    sampled_paper_ids = np.array(const.year2paper_ids[args.conference])[order]

    # Exclude papers that already have AC decisions
    existing_ac_decisions = load_llm_ac_decisions(output_dir=args.output_dir,
                                                             conference=args.conference,
                                                             model_name=args.model_name,
                                                             ac_scoring_method=args.ac_scoring_method,
                                                             experiment_name=args.experiment_name,
                                                             num_papers_per_area_chair=args.num_papers_per_area_chair)

    sampled_paper_ids = [paper_id for paper_id in sampled_paper_ids if paper_id not in existing_ac_decisions]




# In[ ]:




