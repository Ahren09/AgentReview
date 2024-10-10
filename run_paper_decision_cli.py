import logging
import os
import sys

import numpy as np

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import const
from agentreview.experiment_config import all_settings
from agentreview.paper_review_settings import get_experiment_settings
from agentreview.config import AgentConfig
from agentreview.environments import PaperDecision
from agentreview.paper_review_arena import PaperReviewArena
from agentreview.paper_review_player import AreaChair
from arguments import parse_args
from agentreview.role_descriptions import get_ac_config
from utility.utils import project_setup, get_paper_decision_mapping, \
    load_metareview, load_gpt4_generated_ac_decisions

# Set up logging configuration
logging.basicConfig(
    level=logging.DEBUG,  # Set to DEBUG to capture all levels of logs
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)  # Output to stdout
    ]
)


def main(args):
    """
    Main routine for paper decisions:

    * Phase 5: Paper Decision.

    Args:
        args (Namespace): Parsed arguments for configuring the review process.
    """
    args.task = "paper_decision"

    # Sample Paper IDs from each category
    paper_id2decision, paper_decision2ids = get_paper_decision_mapping(args.data_dir, args.conference)

    # Make sure the same set of papers always go through the same ACs in the same batch
    NUM_PAPERS = len(const.year2paper_ids[args.conference])
    order = np.random.choice(range(NUM_PAPERS), size=NUM_PAPERS, replace=False)

    metareviews = []

    # Paper IDs we actually used in experiments
    experimental_paper_ids = []

    # For papers that have not been decided yet, load their metareviews

    print("Shuffling paper IDs")
    sampled_paper_ids = np.array(const.year2paper_ids[args.conference])[order]

    # Exclude papers that already have AC decisions
    existing_ac_decisions = load_gpt4_generated_ac_decisions(output_dir=args.output_dir,
                                                             conference=args.conference,
                                                             model_name=args.model_name,
                                                             ac_scoring_method=args.ac_scoring_method,
                                                             experiment_name=args.experiment_name,
                                                             num_papers_per_area_chair=args.num_papers_per_area_chair)

    existing_ac_decisions = [int(paper_id) for batch in existing_ac_decisions for paper_id in batch]

    sampled_paper_ids = [paper_id for paper_id in sampled_paper_ids if paper_id not in existing_ac_decisions]

    print("TODO: set paper_ids to existing values")

    sampled_paper_ids = [396, 729, 816]

    for paper_id in sampled_paper_ids:

        experiment_setting = get_experiment_settings(all_settings[args.experiment_name])

        # Load meta-reviews
        metareview = load_metareview(output_dir=args.output_dir, paper_id=paper_id,
                                     experiment_name=args.experiment_name,
                                     model_name=args.model_name, conference=args.conference)

        if metareview is None:

            if args.ignore_missing_metareviews:

                print(f"Metareview for {paper_id} does not exist. This may happen because the conversation is "
                      f"completely filtered out due to content policy. "
                      f"Loading the BASELINE metareview...")

                metareview = load_metareview(paper_id=paper_id, experiment_name="BASELINE",
                                             model_name=args.model_name, conference=args.conference)

            else:
                raise ValueError(f"Metareview for {paper_id} does not exist")

        metareviews += [metareview]
        experimental_paper_ids += [paper_id]

    num_batches = len(experimental_paper_ids) // args.num_papers_per_area_chair

    for batch_index in range(num_batches):
        experiment_setting["players"] = {k: v for k, v in experiment_setting["players"].items() if k.startswith("AC")}

        players = []

        for role, players_li in experiment_setting["players"].items():

            for i, player_config in enumerate(players_li):

                # This phase should only contain the Area Chair
                if role == "AC":

                    player_config = get_ac_config(env_type="paper_decision",
                                                  scoring_method=args.ac_scoring_method,
                                                  num_papers_per_area_chair=args.num_papers_per_area_chair,
                                                  global_settings=experiment_setting['global_settings'],
                                                  acceptance_rate=args.acceptance_rate
                                                  **player_config)

                    player_config = AgentConfig(**player_config)
                    player_config['model'] = args.model_name
                    player = AreaChair(**player_config)

                else:
                    raise NotImplementedError(f"Unknown role: {role}")

                players.append(player)

        player_names = [player.name for player in players]

        if batch_index >= num_batches - 1:  # Last batch. Include all remaining papers
            batch_paper_ids = experimental_paper_ids[batch_index * args.num_papers_per_area_chair:]

        else:
            batch_paper_ids = experimental_paper_ids[batch_index * args.num_papers_per_area_chair: (batch_index + 1) *
                                                                                                   args.num_papers_per_area_chair]

        env = PaperDecision(player_names=player_names, paper_ids=batch_paper_ids,
                            metareviews=metareviews,
                            experiment_setting=experiment_setting, ac_scoring_method=args.ac_scoring_method)

        arena = PaperReviewArena(players=players, environment=env, args=args)
        arena.launch_cli(interactive=False)


if __name__ == "__main__":
    project_setup()
    main(parse_args())
