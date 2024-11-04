import logging
import os
import os.path as osp
from typing import Union

from colorama import Fore
from colorama import Style as CRStyle
from prompt_toolkit import prompt
from prompt_toolkit.completion import WordCompleter
from prompt_toolkit.styles import Style
from rich.console import Console

from agentreview.utility.utils import get_rebuttal_dir, load_llm_ac_decisions, \
    save_llm_ac_decisions
from ..arena import Arena, TooManyInvalidActions
from ..backends.human import HumanBackendError
from ..const import AGENTREVIEW_LOGO
from ..environments import PaperReview, PaperDecision

# Get the ASCII art from https://patorjk.com/software/taag/#p=display&f=Big&t=Chat%20Arena

color_dict = {
    "red": Fore.RED,
    "green": Fore.GREEN,

    "blue": Fore.BLUE,  # Paper Extractor
    "light_red": Fore.LIGHTRED_EX,  # AC
    "light_green": Fore.LIGHTGREEN_EX,  # Author
    "yellow": Fore.YELLOW,  # R1
    "magenta": Fore.MAGENTA,  # R2
    "cyan": Fore.CYAN,
    "white": Fore.WHITE,
    "black": Fore.BLACK,

    "light_yellow": Fore.LIGHTYELLOW_EX,
    "light_blue": Fore.LIGHTBLUE_EX,
    "light_magenta": Fore.LIGHTMAGENTA_EX,
    "light_cyan": Fore.LIGHTCYAN_EX,
    "light_white": Fore.LIGHTWHITE_EX,
    "light_black": Fore.LIGHTBLACK_EX,

}

visible_colors = [
    color
    for color in color_dict  # ANSI_COLOR_NAMES.keys()
    if color not in ["black", "white", "red", "green"] and "grey" not in color
]

try:
    import colorama
except ImportError:
    raise ImportError(
        "Please install colorama: `pip install colorama`"
    )

MAX_STEPS = 20  # We should not need this parameter for paper reviews anyway

# Set logging level to ERROR
logging.getLogger().setLevel(logging.ERROR)


class ArenaCLI:
    """The CLI user interface for ChatArena."""

    def __init__(self, arena: Arena):
        self.arena = arena
        self.args = arena.args


    def launch(self, max_steps: int = None, interactive: bool = True):
        """Run the CLI."""

        if not interactive and max_steps is None:
            max_steps = MAX_STEPS

        args = self.args

        console = Console()
        # Print ascii art
        timestep = self.arena.reset()
        console.print("🎓AgentReview Initialized!", style="bold green")

        env: Union[PaperReview, PaperDecision] = self.arena.environment
        players = self.arena.players

        env_desc = self.arena.global_prompt
        num_players = env.num_players
        player_colors = visible_colors[:num_players]  # sample different colors for players
        name_to_color = dict(zip(env.player_names, player_colors))

        print("name_to_color: ", name_to_color)
        # System and Moderator messages are printed in red
        name_to_color["System"] = "red"
        name_to_color["Moderator"] = "red"

        console.print(
            f"[bold green underline]Environment ({env.type_name}) description:[/]\n{env_desc}"
        )

        # Print the player name, role_desc and backend_type
        for i, player in enumerate(players):
            player_name_str = f"[{player.name} ({player.backend.type_name})] Role Description:"
            # player_name = Text(player_name_str)
            # player_name.stylize(f"bold {name_to_color[player.name]} underline")
            # console.print(player_name)
            # console.print(player.role_desc)

            logging.info(color_dict[name_to_color[player.name]] + player_name_str + CRStyle.RESET_ALL)
            logging.info(color_dict[name_to_color[player.name]] + player.role_desc + CRStyle.RESET_ALL)

        console.print(Fore.GREEN + "\n========= Arena Start! ==========\n" + CRStyle.RESET_ALL)

        step = 0
        while not timestep.terminal:
            if env.type_name == "paper_review":
                if env.phase_index > 4:
                    break

            elif env.type_name == "paper_decision":
                # Phase 5: AC makes decisions
                if env.phase_index > 5:
                    break

            else:
                raise NotImplementedError(f"Unknown environment type: {env.type_name}")

            if interactive:
                command = prompt(
                    [("class:command", "command (n/r/q/s/h) > ")],
                    style=Style.from_dict({"command": "blue"}),
                    completer=WordCompleter(
                        [
                            "next",
                            "n",
                            "reset",
                            "r",
                            "exit",
                            "quit",
                            "q",
                            "help",
                            "h",
                            "save",
                            "s",
                        ]
                    ),
                )
                command = command.strip()

                if command == "help" or command == "h":
                    console.print("Available commands:")
                    console.print("    [bold]next or n or <Enter>[/]: next step")
                    console.print("    [bold]exit or quit or q[/]: exit the game")
                    console.print("    [bold]help or h[/]: print this message")
                    console.print("    [bold]reset or r[/]: reset the game")
                    console.print("    [bold]save or s[/]: save the history to file")
                    continue
                elif command == "exit" or command == "quit" or command == "q":
                    break
                elif command == "reset" or command == "r":
                    timestep = self.arena.reset()
                    console.print(
                        "\n========= Arena Reset! ==========\n", style="bold green"
                    )
                    continue
                elif command == "next" or command == "n" or command == "":
                    pass
                elif command == "save" or command == "s":
                    # Prompt to get the file path
                    file_path = prompt(
                        [("class:command", "save file path > ")],
                        style=Style.from_dict({"command": "blue"}),
                    )
                    file_path = file_path.strip()
                    # Save the history to file
                    self.arena.save_history(file_path)
                    # Print the save success message
                    console.print(f"History saved to {file_path}", style="bold green")
                else:
                    console.print(f"Invalid command: {command}", style="bold red")
                    continue

            try:
                timestep = self.arena.step()
            except HumanBackendError as e:
                # Handle human input and recover with the game update
                human_player_name = env.get_next_player()
                if interactive:
                    human_input = prompt(
                        [
                            (
                                "class:user_prompt",
                                f"Type your input for {human_player_name}: ",
                            )
                        ],
                        style=Style.from_dict({"user_prompt": "ansicyan underline"}),
                    )
                    # If not, the conversation does not stop
                    timestep = env.step(human_player_name, human_input)
                else:
                    raise e  # cannot recover from this error in non-interactive mode
            except TooManyInvalidActions as e:
                # Print the error message
                # console.print(f"Too many invalid actions: {e}", style="bold red")
                print(Fore.RED + "This will be red text" + CRStyle.RESET_ALL)
                break

            # The messages that are not yet logged
            messages = [msg for msg in env.get_observation() if not msg.logged]

            # Print the new messages
            for msg in messages:
                message_str = f"[{msg.agent_name}->{msg.visible_to}]: {msg.content}"
                if self.args.skip_logging:
                    console.print(color_dict[name_to_color[msg.agent_name]] + message_str + CRStyle.RESET_ALL)
                msg.logged = True

            step += 1
            if max_steps is not None and step >= max_steps:
                break

        console.print("\n========= Arena Ended! ==========\n", style="bold red")

        if env.type_name == "paper_review":

            paper_id = self.arena.environment.paper_id
            rebuttal_dir = get_rebuttal_dir(output_dir=self.args.output_dir,
                                            paper_id=paper_id,
                                            experiment_name=self.args.experiment_name,
                                            model_name=self.args.model_name,
                                            conference=self.args.conference)

            os.makedirs(rebuttal_dir, exist_ok=True)

            path_review_history = f"{rebuttal_dir}/{paper_id}.json"

            if osp.exists(path_review_history):
                raise Exception(f"History already exists!! ({path_review_history}). There must be something wrong with "
                                f"the path to save the history ")

            self.arena.save_history(path_review_history)

        elif env.type_name == "paper_decision":
            ac_decisions = load_llm_ac_decisions(output_dir=args.output_dir,
                                                            conference=args.conference,
                                                            model_name=args.model_name,
                                                            ac_scoring_method=args.ac_scoring_method,
                                                            experiment_name=args.experiment_name,
                                                            num_papers_per_area_chair=args.num_papers_per_area_chair)


            ac_decisions += [env.ac_decisions]

            save_llm_ac_decisions(ac_decisions,
                                 output_dir=args.output_dir,
                                 conference=args.conference,
                                 model_name=args.model_name,
                                 ac_scoring_method=args.ac_scoring_method,
                                 experiment_name=args.experiment_name)
