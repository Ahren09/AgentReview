import logging
import logging
import os
from pathlib import Path
from typing import List, Union

from llama_index.readers.file.docs import PDFReader

from agentreview.agent import Player
from .backends import IntelligenceBackend
from .config import BackendConfig
from .message import Message


class AreaChair(Player):

    def __init__(
            self,
            name: str,
            role_desc: str,
            env_type: str,
            backend: Union[BackendConfig, IntelligenceBackend],
            global_prompt: str = None,
            **kwargs,
    ):
        super().__init__(name, role_desc, backend, global_prompt, **kwargs)
        self.env_type = env_type
        self.role_desc = role_desc

    def act(self, observation: List[Message]) -> str:

        # The author just finished their rebuttals (so last speaker is Author 1).
        # The AC asks each reviewer to update their reviews.

        if self.env_type == "paper_review":
            if len(observation) > 0 and observation[-1].agent_name.startswith("Author"):
                return "Dear reviewers, please update your reviews based on the author's rebuttals."

            else:
                return super().act(observation)

        elif self.env_type == "paper_decision":
            return super().act(observation)

        else:
            raise ValueError(f"Unknown env_type: {self.env_type}")


class Reviewer(Player):

    def __init__(
            self,
            name: str,
            role_desc: str,
            backend: Union[BackendConfig, IntelligenceBackend],
            global_prompt: str = None,
            **kwargs,
    ):
        print("kwargs")
        print(kwargs)
        super().__init__(name, role_desc, backend, global_prompt, **kwargs)

    def act(self, observation: List[Message]) -> str:
        return super().act(observation)


class PaperExtractorPlayer(Player):
    """A player for solely extracting contents from a paper.

    No API calls are made by this player.
    """

    def __init__(
            self,
            name: str,
            role_desc: str,
            paper_id: int,
            paper_decision: str,
            conference: str,
            backend: Union[BackendConfig, IntelligenceBackend],
            paper_pdf_path: str = None,
            global_prompt: str = None,
            **kwargs,
    ):
        super().__init__(name, role_desc, backend, global_prompt, **kwargs)
        self.paper_id = paper_id
        self.paper_decision = paper_decision
        self.conference: str = conference
        
        if paper_pdf_path is not None:
            self.paper_pdf_path = paper_pdf_path

    def act(self, observation: List[Message]) -> str:
        """
        Take an action based on the observation (Generate a response), which can later be parsed to actual actions that affect the game dynamics.

        Parameters:
            observation (List[Message]): The messages that the player has observed from the environment.

        Returns:
            str: The action (response) of the player.
        """
        if self.paper_pdf_path is not None:
            logging.info(f"Loading paper from {self.paper_pdf_path} ...")
        else:
            logging.info(f"Loading {self.conference} paper {self.paper_id} ({self.paper_decision}) ...")

        loader = PDFReader()
        if self.paper_pdf_path is not None:
            document_path = Path(self.paper_pdf_path)
        else:
            document_path = Path(os.path.join(self.args.data_dir, self.conference, "paper", self.paper_decision,
                                            f"{self.paper_id}.pdf"))  #
        documents = loader.load_data(file=document_path)

        num_words = 0
        main_contents = "Contents of this paper:\n\n"
        FLAG = False

        for doc in documents:
            text = doc.text.split(' ')
            if len(text) + num_words > self.args.max_num_words:
                text = text[:self.args.max_num_words - num_words]
                FLAG = True
            num_words += len(text)
            text = " ".join(text)
            main_contents += text + ' '
            if FLAG:
                break
        
        print(main_contents)
        
        return main_contents
