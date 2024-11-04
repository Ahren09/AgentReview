import logging
import os
import sys

import numpy as np

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from agentreview import const
from agentreview.utility.experiment_utils import initialize_players
from agentreview.experiment_config import all_settings
from agentreview.paper_review_settings import get_experiment_settings
from agentreview.environments import PaperDecision
from agentreview.paper_review_arena import PaperReviewArena
from agentreview.arguments import parse_args
from agentreview.utility.utils import project_setup, get_paper_decision_mapping, \
    load_metareview, load_llm_ac_decisions

# Set up logging configuration
logging.basicConfig(
    level=logging.DEBUG,  # Set to DEBUG to capture all levels of logs
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)  # Output to stdout
    ]
)

logger = logging.getLogger(__name__)


def main(args):
    """
    Main routine for paper decisions:

    * Phase 5: Paper Decision.

    Args:
        args (Namespace): Parsed arguments for configuring the review process.
    """
    args.task = "paper_decision"

    print(const.AGENTREVIEW_LOGO)

    # Sample Paper IDs from each category
    paper_id2decision, paper_decision2ids = get_paper_decision_mapping(args.data_dir, args.conference)

    # Make sure the same set of papers always go through the same ACs in the same batch
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

    existing_ac_decisions = [int(paper_id) for batch in existing_ac_decisions for paper_id in batch]

    sampled_paper_ids = [paper_id for paper_id in sampled_paper_ids if paper_id not in existing_ac_decisions]

    experiment_setting = get_experiment_settings(paper_id=None, paper_decision=None, setting=all_settings[
        args.experiment_name])

    logger.info(f"Loading metareview!")

    for paper_id in sampled_paper_ids:

        # Load meta-reviews
        metareview = load_metareview(output_dir=args.output_dir, paper_id=paper_id,
                                     experiment_name=args.experiment_name,
                                     model_name=args.model_name, conference=args.conference)

        if metareview is None:
            print(f"Metareview for {paper_id} does not exist. This may happen because the conversation is "
                  f"completely filtered out due to content policy. "
                  f"Loading the BASELINE metareview...")

            metareview = load_metareview(output_dir=args.output_dir, paper_id=paper_id,
                                         experiment_name="BASELINE",
                                         model_name=args.model_name, conference=args.conference)

        if metareview is not None:

            metareviews += [metareview]
            experimental_paper_ids += [paper_id]

    num_batches = len(experimental_paper_ids) // args.num_papers_per_area_chair

    for batch_index in range(num_batches):

        players = initialize_players(experiment_setting=experiment_setting, args=args)

        player_names = [player.name for player in players]

        if batch_index >= num_batches - 1:  # Last batch. Include all remaining papers
            batch_paper_ids = experimental_paper_ids[batch_index * args.num_papers_per_area_chair:]

        else:
            batch_paper_ids = experimental_paper_ids[batch_index * args.num_papers_per_area_chair: (batch_index + 1) *
                                                                                                   args.num_papers_per_area_chair]

        env = PaperDecision(player_names=player_names, paper_ids=batch_paper_ids,
                            metareviews=metareviews,
                            experiment_setting=experiment_setting, ac_scoring_method=args.ac_scoring_method)

        arena = PaperReviewArena(players=players, environment=env, args=args, global_prompt=const.GLOBAL_PROMPT)
        arena.launch_cli(interactive=False)

if __name__ == "__main__":
    project_setup()
    main(parse_args())
