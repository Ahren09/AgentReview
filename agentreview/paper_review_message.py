import logging
from typing import List

from agentreview.message import MessagePool, Message


class PaperReviewMessagePool(MessagePool):
    """
    A pool to manage the messages in the paper review environment.

    """

    def __init__(self, experiment_setting: dict):
        super().__init__()
        self.experiment_setting = experiment_setting


    def get_visible_messages_for_paper_review(self, agent_name, phase_index: int,
                                              next_player_idx: int, player_names: List[str]) \
            -> (List)[Message]:
        """
        Get all the messages that are visible to a given agent before a specified turn.

        Parameters:
            agent_name (str): The name of the agent.
            turn (int): The specified turn.
            phase_index (int): The specified phase in paper reviewing process.

        Returns:
            List[Message]: A list of visible messages.
        """

        reviewer_names = sorted([name for name in player_names if name.startswith("Reviewer")])

        # Get the messages before the current turn
        # prev_messages = [message for message in self._messages if message.turn < turn]
        prev_messages = self._messages

        if phase_index in [0, 1]:
            visible_messages = [message for message in prev_messages if message.agent_name == "Paper Extractor"]

        elif phase_index == 2:
            visible_messages = []

            for message in prev_messages:

                # The author can see the paper content and each reviewer's review
                if message.agent_name == "Paper Extractor" or message.agent_name == reviewer_names[next_player_idx]:
                    visible_messages.append(message)

            # raise NotImplementedError(f"In Phase {phase_index}, only authors can respond to reviewers' "
            #                           f"reviews, but the current agent is {agent_name}.")

        elif phase_index == 3:
            if [agent_name.startswith(prefix) for prefix in ["AC", "Reviewer", "Paper Extractor"]]:
                # Both area chairs and reviewers can see all the reviews and rebuttals
                visible_messages = prev_messages

            elif agent_name.startswith("Author"):
                visible_messages = []

        elif phase_index == 4:
            if agent_name.startswith("AC"):
                area_chair_type = self.experiment_setting['players']['AC'][0]["area_chair_type"]

                # 'BASELINE' means we do not specify the area chair's characteristics in the config file
                if area_chair_type in ["inclusive", "BASELINE"]:
                    # An inclusive area chair can see all the reviews and rebuttals
                    visible_messages = prev_messages

                elif area_chair_type == "conformist":
                    visible_messages = []

                    for message in prev_messages:
                        if message.agent_name.startswith("Author") or message.agent_name.startswith("Reviewer"):
                            visible_messages.append(message)


                elif area_chair_type == "authoritarian":
                    visible_messages = []

                    for message in prev_messages:
                        if not (message.agent_name.startswith("Author") or message.agent_name.startswith("Reviewer")):
                            visible_messages.append(message)

                else:
                    raise ValueError(f"Unknown Area chair type: {area_chair_type}.")


        else:

            visible_messages = []
            for message in prev_messages:
                if (
                        message.visible_to == "all"
                        or agent_name in message.visible_to
                        or agent_name == "Moderator"
                ):
                    visible_messages.append(message)

        logging.info(f"Phase {phase_index}： {agent_name} sees {len(visible_messages)} messages from "
                     f"{','.join([agent.agent_name for agent in visible_messages]) if visible_messages else 'None'}")

        return visible_messages
