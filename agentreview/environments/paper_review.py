import json
import logging
import os.path as osp
from typing import List

from agentreview.environments import Conversation
from agentreview.utility.utils import get_rebuttal_dir
from .base import TimeStep
from ..message import Message
from ..paper_review_message import PaperReviewMessagePool


logger = logging.getLogger(__name__)

class PaperReview(Conversation):
    """
    Discussion between reviewers and area chairs.

    There are several phases in the reviewing process:
        reviewer_write_reviews: reviewers write their reviews based on the paper content.
        author_reviewer_discussion: An author respond to comments from the reviewers.
        reviewer_ac_discussion: reviewers and an area chair discuss the paper.
        ac_discussion: an area chair makes the final decision.
    """

    type_name = "paper_review"

    def __init__(self, player_names: List[str], paper_id: int, paper_decision: str, experiment_setting: dict, args,
                 parallel: bool = False,

                 **kwargs):
        """
        Args:
            paper_id (int): the id of the paper, such as 917
            paper_decision (str): the decision of the paper, such as "Accept: notable-top-25%"
        """

        # Inherit from the parent class of `class Conversation`
        super(Conversation, self).__init__(player_names=player_names, parallel=parallel, **kwargs)
        self.args = args
        self.paper_id = paper_id
        self.paper_decision = paper_decision
        self.parallel = parallel
        self.experiment_setting = experiment_setting
        self.player_to_test = experiment_setting.get('player_to_test', None)
        self.task = kwargs.get("task")
        self.experiment_name = args.experiment_name

        # The "state" of the environment is maintained by the message pool
        self.message_pool = PaperReviewMessagePool(experiment_setting)

        self.phase_index = 0
        self._phases = None

    @property
    def phases(self):

        if self._phases is not None:
            return self._phases

        reviewer_names = [name for name in self.player_names if name.startswith("Reviewer")]

        num_reviewers = len(reviewer_names)

        reviewer_names = [f"Reviewer {i}" for i in range(1, num_reviewers + 1)]

        self._phases = {
            # In phase 0, no LLM-based agents are called.
            0: {
                "name": "paper_extraction",
                'speaking_order': ["Paper Extractor"],
            },

            1: {
                "name": 'reviewer_write_reviews',
                'speaking_order': reviewer_names
            },

            # The author responds to each reviewer's review
            2: {
                'name': 'author_reviewer_discussion',
                'speaking_order': ["Author" for _ in reviewer_names],
            },

            3: {
                'name': 'reviewer_ac_discussion',
                'speaking_order': ["AC"] + reviewer_names,
            },

            4: {
                'name': 'ac_write_metareviews',
                'speaking_order': ["AC"]
            },
            5: {
                'name': 'ac_makes_decisions',
                'speaking_order': ["AC"]
            },
        }

        return self.phases

    @phases.setter
    def phases(self, value):
        self._phases = value

    def reset(self):
        self._current_phase = "review"
        self.phase_index = 0
        return super().reset()



    def load_message_history_from_cache(self):
        if self._phase_index == 0:

            print("Loading message history from BASELINE experiment")

            full_paper_discussion_path = get_rebuttal_dir(paper_id=self.paper_id,
                                                          experiment_name="BASELINE",
                                                          model_name=self.args.model_name,
                                                          conference=self.args.conference)

            messages = json.load(open(osp.join(full_paper_discussion_path, f"{self.paper_id}.json"), 'r',
                                      encoding='utf-8'))['messages']

            num_messages_from_AC = 0

            for msg in messages:

                # We have already extracted contents from the paper.
                if msg['agent_name'] == "Paper Extractor":
                    continue

                # Encountering the 2nd message from the AC. Stop loading messages.
                if msg['agent_name'] == "AC" and num_messages_from_AC == 1:
                    break

                if msg['agent_name'] == "AC":
                    num_messages_from_AC += 1

                message = Message(**msg)
                self.message_pool.append_message(message)

            num_unique_reviewers = len(
                set([msg['agent_name'] for msg in messages if msg['agent_name'].startswith("Reviewer")]))

            assert num_unique_reviewers == self.args.num_reviewers_per_paper

            self._phase_index = 4

    def step(self, player_name: str, action: str) -> TimeStep:
        """
        Step function that is called by the arena.

        Args:
            player_name: the name of the player that takes the action
            action: the action that the agents wants to take
        """

        message = Message(
            agent_name=player_name, content=action, turn=self._current_turn
        )
        self.message_pool.append_message(message)

        speaking_order = self.phases[self.phase_index]["speaking_order"]

        # Reached the end of the speaking order. Move to the next phase.
        logging.info(f"Phase {self.phase_index}: {self.phases[self._phase_index]['name']} "
                     f"| Player {self._next_player_index}: {speaking_order[self._next_player_index]}")

        terminal = self.is_terminal()

        if self._next_player_index == len(speaking_order) - 1:
            self._next_player_index = 0

            if self.phase_index == 4:
                terminal = True
                logger.info(
                    "Finishing the simulation for Phase I - IV. Please run `python run_paper_decision_cli.py ` for "
                           "Phase V. (AC makes decisions).")

            else:
                logger.info(f"Phase {self.phase_index}: end of the speaking order. Move to Phase ({self.phase_index + 1}).")
                self.phase_index += 1
                self._current_turn += 1




        else:
            self._next_player_index += 1

        timestep = TimeStep(
            observation=self.get_observation(),
            reward=self.get_zero_rewards(),
            terminal=terminal,
        )  # Return all the messages

        return timestep

    def get_next_player(self) -> str:
        """Get the next player in the current phase."""
        speaking_order = self.phases[self.phase_index]["speaking_order"]
        next_player = speaking_order[self._next_player_index]
        return next_player

    def get_observation(self, player_name=None) -> List[Message]:
        """Get observation for the player."""
        if player_name is None:
            return self.message_pool.get_all_messages()
        else:

            return self.message_pool.get_visible_messages_for_paper_review(
                player_name, phase_index=self.phase_index, next_player_idx=self._next_player_index,
                player_names=self.player_names
            )
