import csv
import json
import logging
from typing import Union

from agentreview.arena import Arena, TooManyInvalidActions
from agentreview.role_descriptions import get_reviewer_description
from agentreview.utility.utils import format_metareviews
from .agent import Player
from .config import ArenaConfig
from .environments import TimeStep, load_environment
from .paper_review_player import PaperExtractorPlayer, AreaChair, Reviewer


logger = logging.getLogger(__name__)


class PaperReviewArena(Arena):
    """Arena for the paper review environment.

    """

    # PaperReviewArena.from_config
    @classmethod
    def from_config(cls, config: Union[str, ArenaConfig]):
        """Create an arena from a config."""
        # If config is a path, load the config
        if isinstance(config, str):
            config = ArenaConfig.load(config)

        global_prompt = config.get("global_prompt", None)

        # Create the players
        players = []
        for player_config in config.players:
            # Add public_prompt to the player config
            if global_prompt is not None:
                player_config["global_prompt"] = global_prompt

            if player_config['name'].startswith("Paper Extractor"):
                player = PaperExtractorPlayer.from_config(player_config)

            elif player_config['name'].startswith("AC"):
                player = AreaChair.from_config(player_config)

            elif player_config['name'].startswith("Reviewer"):
                player = Reviewer.from_config(player_config)

            else:
                player = Player.from_config(player_config)
            players.append(player)

        # Check that the player names are unique
        player_names = [player.name for player in players]
        assert len(player_names) == len(
            set(player_names)
        ), f"Player names must be unique, current players: {[','.join(player_names)]}"

        # Create the environment
        config.environment[
            "player_names"
        ] = player_names  # add the player names to the environment config
        env = load_environment(config.environment)

        return cls(players, env, global_prompt=global_prompt)

    # PaperReviewArena.step()
    def step(self) -> TimeStep:
        """Take a step in the game: one player takes an action and the environment updates."""

        # if self.environment.phase_index > 4 and self.args.task == "paper_review":
        #     logger.info("Finishing the simulation for Phase I - IV. Please run `python run_paper_decision_cli.py ` for "
        #           "Phase V. (AC makes decisions).")
        #     return
        #
        # elif self.environment.phase_index > 5 and self.args.task == "paper_decision":
        #     logger.info("Finishing the simulation for Phase V. (AC makes decisions).")
        #     return

        player_name = self.environment.get_next_player()

        player = self.name_to_player[player_name]  # get the player object

        observation = self.environment.get_observation(
            player_name
        )  # get the observation for the player

        timestep = None

        # try to take an action for a few times
        for i in range(self.invalid_actions_retry):


            # Update reviewer description for rebuttal
            if self.environment.phase_index == 3 and player.name.startswith("Reviewer"):
                logging.info("Update reviewers' role_desc for Phase 3 (reviewer_ac_discussion)")
                reviewer_index = int(player.name.split("Reviewer ")[1])

                # reviewer_index starts from 1, so we need to subtract 1 to get the index of the reviewer in the list

                player.role_desc = get_reviewer_description(phase="reviewer_ac_discussion",
                                                            **self.environment.experiment_setting["players"][
                                                                'Reviewer'][reviewer_index - 1])

            elif self.environment.phase_index == 5:  # Phase 5 AC Makes Decisions

                player.role_desc += format_metareviews(self.environment.metareviews, self.environment.paper_ids)

            action = player(observation)  # take an action

            if self.environment.check_action(action, player_name):  # action is valid
                timestep = self.environment.step(
                    player_name, action
                )  # update the environment
                break
            else:  # action is invalid
                logging.warning(f"{player_name} made an invalid action {action}")
                continue

        if (
                timestep is None
        ):  # if the player made invalid actions for too many times, terminate the game
            warning_msg = f"{player_name} has made invalid actions for {self.invalid_actions_retry} times. Terminating the game."
            logging.warning(warning_msg)
            raise TooManyInvalidActions(warning_msg)

        return timestep

    def save_history(self, path: str):
        """
        Save the history of the game to a file.

        Supports csv and json formats.
        """
        messages = self.environment.get_observation()
        message_rows = []

        if path.endswith(".csv"):
            header = [
                "agent_name",
                "content",
                "turn",
                "timestamp",
                "visible_to",
                "msg_type",
            ]
            for message in messages:
                message_row = [
                    message.agent_name,
                    message.content,
                    message.turn,
                    str(message.timestamp),
                    message.visible_to,
                    message.msg_type,
                ]
                message_rows.append(message_row)

            with open(path, "w") as f:
                writer = csv.writer(f)
                writer.writerow(header)
                writer.writerows(message_rows)
        elif path.endswith(".json"):
            for message in messages:
                message_row = {
                    "agent_name": message.agent_name,
                    "content": message.content,
                    "turn": message.turn,
                    "timestamp": str(message.timestamp),
                    "visible_to": message.visible_to,
                    "msg_type": message.msg_type,
                }
                message_rows.append(message_row)

            with open(path, "w") as f:


                json.dump({
                    "experiment_setting": self.environment.experiment_setting,
                    "messages": message_rows,
                }, f, indent=2)
        else:
            raise ValueError("Invalid file format")
