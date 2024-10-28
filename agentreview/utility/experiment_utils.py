import os
import sys

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from agentreview.agent import Player
from agentreview.paper_review_player import PaperExtractorPlayer, AreaChair, Reviewer
from agentreview.role_descriptions import get_ac_config, get_reviewer_player_config, get_author_config, \
    get_paper_extractor_config


def initialize_players(experiment_setting: dict, args):
    paper_id = experiment_setting['paper_id']
    paper_decision = experiment_setting['paper_decision']

    if args.task == "paper_decision":
        experiment_setting["players"] = {k: v for k, v in experiment_setting["players"].items() if k.startswith("AC")}

    players = []

    for role, players_list in experiment_setting["players"].items():

        for i, player_config in enumerate(players_list):
            if role == "AC":

                # For AC, `env_type` is either "paper_decision" or "paper_review"
                player_config = get_ac_config(env_type=args.task,
                                              scoring_method=args.ac_scoring_method,
                                              num_papers_per_area_chair=args.num_papers_per_area_chair,
                                              global_settings=experiment_setting['global_settings'],
                                              acceptance_rate=args.acceptance_rate,
                                              **player_config)

                player_config['model'] = args.model_name

                player = AreaChair(data_dir=args.data_dir,
                                   conference=args.conference,
                                   args=args,
                                   **player_config)


            elif args.task == "paper_review":


                if role == "Paper Extractor":

                    player_config = get_paper_extractor_config(global_settings=experiment_setting['global_settings'])

                    player = PaperExtractorPlayer(data_dir=args.data_dir, paper_id=paper_id,
                                                  paper_decision=paper_decision,
                                                  args=args,
                                                  conference=args.conference, **player_config)



                elif role == "Author":

                    # Author requires no behavior customization.
                    # So we directly use the Player class
                    player_config = get_author_config()
                    player = Player(data_dir=args.data_dir,
                                    conference=args.conference,
                                    args=args,
                                    **player_config)



                elif role == "Reviewer":
                    player_config = get_reviewer_player_config(reviewer_index=i + 1,
                                                               global_settings=experiment_setting['global_settings'],
                                                               **player_config)
                    player_config['model'] = args.model_name
                    player = Reviewer(data_dir=args.data_dir, conference=args.conference, args=args, **player_config)


                else:
                    raise NotImplementedError(f"Unknown role for paper review (stage 1-4): {role}")

            else:
                raise NotImplementedError(f"Unknown role for paper decision (stage 5): {role}")

            players.append(player)

    return players
