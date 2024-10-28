import glob
import logging
import os
import sys
from argparse import Namespace


sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from agentreview import const
from agentreview.arguments import parse_args
from agentreview.experiment_config import all_settings
from agentreview.environments import PaperReview
from agentreview.paper_review_settings import get_experiment_settings
from agentreview.paper_review_arena import PaperReviewArena
from agentreview.utility.experiment_utils import initialize_players
from agentreview.utility.utils import project_setup, get_paper_decision_mapping

# Set up logging configuration
logging.basicConfig(
    level=logging.DEBUG,  # Set to DEBUG to capture all levels of logs
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)  # Output to stdout
    ]
)

logger = logging.getLogger(__name__)


# Sample Paper IDs from each category

def main(args: Namespace):
    """
    Main routine for paper review and rebuttals:

    * Phase 1: Reviewer Assessment (Reviewer writes reviews)
    * Phase 2: Author-Reviewer Discussion. (Author writes rebuttals).
    * Phase 3: Reviewer-AC Discussion.
    * Phase 4: Meta-Review Compilation. (AC writes metareviews)

    Args:
        args (Namespace): Parsed arguments for configuring the review process.
    """

    args.task = "paper_review"

    paper_id2decision, paper_decision2ids = get_paper_decision_mapping(args.data_dir, args.conference)

    # Sample paper IDs for the simulation from existing data.
    paper_paths = glob.glob(os.path.join(args.data_dir, args.conference, "paper", "**", "*.pdf"))
    sampled_paper_ids = [int(os.path.basename(p).split(".pdf")[0]) for p in paper_paths if p.endswith(".pdf")]

    for paper_id in sampled_paper_ids:
        # Ground-truth decision in the conference.
        # We use this to partition the papers into different quality.
        paper_decision = paper_id2decision[paper_id]

        experiment_setting = get_experiment_settings(paper_id=paper_id,
                                                     paper_decision=paper_decision,
                                                     setting=all_settings[args.experiment_name])

        logger.info(f"Experiment Started!")
        logger.info(f"Paper ID: {paper_id} (Decision in {args.conference}: {paper_decision})")

        players = initialize_players(experiment_setting=experiment_setting, args=args)

        player_names = [player.name for player in players]

        # for role, players_list in experiment_setting["players"].items():
        #
        #     for i, player_config in enumerate(players_list):
        #         if role == "Paper Extractor":
        #
        #             player_config = get_paper_extractor_config(global_settings=experiment_setting['global_settings'], )
        #
        #             player = PaperExtractorPlayer(data_dir=args.data_dir, paper_id=paper_id,
        #                                           paper_decision=paper_decision,
        #                                           args=args,
        #                                           conference=args.conference, **player_config)
        #
        #             player_names.append(player.name)
        #
        #
        #         elif role == "AC":
        #
        #             player_config = get_ac_config(env_type="paper_review",
        #                                           scoring_method=args.ac_scoring_method,
        #                                           num_papers_per_area_chair=args.num_papers_per_area_chair,
        #                                           global_settings=experiment_setting['global_settings'],
        #                                           acceptance_rate=args.acceptance_rate,
        #                                           **player_config)
        #
        #             player_config['model'] = args.model_name
        #
        #             player = AreaChair(data_dir=args.data_dir,
        #                                conference=args.conference,
        #                                args=args,
        #                                **player_config)
        #
        #             player_names.append(player.name)
        #
        #
        #         elif role == "Author":
        #
        #             # Author requires no behavior customization.
        #             # So we directly use the Player class
        #             player_config = get_author_config()
        #             player = Player(data_dir=args.data_dir,
        #                             conference=args.conference,
        #                             args=args,
        #                             **player_config)
        #
        #             player_names.append(player.name)
        #
        #         elif role == "Reviewer":
        #             player_config = get_reviewer_player_config(reviewer_index=i + 1,
        #                                                        global_settings=experiment_setting['global_settings'],
        #                                                        **player_config)
        #             player_config['model'] = args.model_name
        #             player = Reviewer(data_dir=args.data_dir, conference=args.conference, **player_config)
        #             player_names.append(player.name)
        #
        #         else:
        #             raise NotImplementedError(f"Unknown role: {role}")
        #
        #         players.append(player)

        env = PaperReview(player_names=player_names, paper_decision=paper_decision, paper_id=paper_id,
                          args=args, experiment_setting=experiment_setting)

        arena = PaperReviewArena(players=players, environment=env, args=args, global_prompt=const.GLOBAL_PROMPT)
        arena.launch_cli(interactive=False)

    logger.info("Done!")


if __name__ == "__main__":
    project_setup()
    main(parse_args())
