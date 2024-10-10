import logging
import traceback
from typing import List

from agentreview.environments import Conversation
from .base import TimeStep
from ..message import Message, MessagePool


logger = logging.getLogger(__name__)


class PaperDecision(Conversation):
    """
    Area chairs make decision based on the meta reviews
    """

    type_name = "paper_decision"

    def __init__(self,
                 player_names: List[str],
                 experiment_setting: dict,
                 paper_ids: List[int] = None,
                 metareviews: List[str] = None,
                 parallel: bool = False,

                 **kwargs):
        """

        Args:
            paper_id (int): the id of the paper, such as 917
            paper_decision (str): the decision of the paper, such as "Accept: notable-top-25%"

        """

        # Inherit from the parent class of `class Conversation`
        super(Conversation, self).__init__(player_names=player_names, parallel=parallel, **kwargs)

        self.paper_ids = paper_ids
        self.metareviews = metareviews
        self.parallel = parallel
        self.experiment_setting = experiment_setting
        self.ac_scoring_method = kwargs.get("ac_scoring_method")
        # The "state" of the environment is maintained by the message pool
        self.message_pool = MessagePool()

        self.ac_decisions = None

        self._current_turn = 0
        self._next_player_index = 0
        self.phase_index = 5  # "ACs make decision based on meta review" is the last phase (Phase 5)

        self._phases = None

    @property
    def phases(self):

        if self._phases is None:
            self._phases = {
                5: {
                    "name": "ac_make_decisions",
                    'speaking_order': ["AC"]
                },
            }
        return self._phases

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

        logging.info(f"Phase {self.phase_index}: {self.phases[self.phase_index]['name']} "
                     f"| Player {self._next_player_index}: {speaking_order[self._next_player_index]}")
        if self._next_player_index == len(speaking_order) - 1:
            self._next_player_index = 0
            logger.info(f"Phase {self.phase_index}: end of the speaking order. Move to Phase {self.phase_index + 1}.")
            self.phase_index += 1
            self._current_turn += 1
        else:
            self._next_player_index += 1

        timestep = TimeStep(
            observation=self.get_observation(),
            reward=self.get_zero_rewards(),
            terminal=self.is_terminal(),
        )  # Return all the messages

        return timestep


    def check_action(self, action: str, player_name: str) -> bool:
        """Check if the action is valid."""

        if player_name.startswith("AC"):

            try:
                self.ac_decisions = self.parse_ac_decisions(action)

            except:
                traceback.print_exc()
                return False

            if not isinstance(self.ac_decisions, dict):
                return False

        return True

    @property
    def ac_decisions(self):
        return self._ac_decisions

    @ac_decisions.setter
    def ac_decisions(self, value):
        self._ac_decisions = value

    def parse_ac_decisions(self, action: str):
        """
        Parse the decisions made by the ACs
        """

        lines = action.split("\n")

        paper2rating = {}

        paper_id, rank = None, None

        for line in lines:

            if line.lower().startswith("paper id:"):
                paper_id = int(line.split(":")[1].split('(')[0].strip())
            elif self.ac_scoring_method == "ranking" and line.lower().startswith("willingness to accept:"):
                rank = int(line.split(":")[1].strip())

            elif self.ac_scoring_method == "recommendation" and line.lower().startswith("decision"):
                rank = line.split(":")[1].strip()



            if paper_id in paper2rating:
                raise ValueError(f"Paper {paper_id} is assigned a rank twice.")

            if paper_id is not None and rank is not None:
                paper2rating[paper_id] = rank
                paper_id, rank = None, None

        return paper2rating
