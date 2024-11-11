import json
import re
from glob import glob
from argparse import Namespace

import gradio as gr


from agentreview import const
from agentreview.config import AgentConfig
from agentreview.agent import Player
from agentreview.backends import BACKEND_REGISTRY
from agentreview.environments import PaperReview
from agentreview.paper_review_arena import PaperReviewArena
from agentreview.utility.experiment_utils import initialize_players
from agentreview.paper_review_player import PaperExtractorPlayer, AreaChair, Reviewer
from agentreview.role_descriptions import (get_reviewer_description, get_ac_description, get_author_config,
                                           get_paper_extractor_config, get_author_description)

# 该文件的使命是前端交互：构建前端页面，从页面中获取用户的配置，传入后端运行，将结果实时展示到相应模块

css = """#col-container {max-width: 90%; margin-left: auto; margin-right: auto; display: flex; flex-direction: column;}
#header {text-align: center;}
#col-chatbox {flex: 1; max-height: min(900px, 100%);}
#label {font-size: 2em; padding: 0.5em; margin: 0;}
.message {font-size: 1.2em;}
.message-wrap {max-height: min(700px, 100vh);}
"""
# .wrap {min-width: min(640px, 100vh)}
# #env-desc {max-height: 100px; overflow-y: auto;}
# .textarea {height: 100px; max-height: 100px;}
# #chatbot-tab-all {height: 750px; max-height: min(750px, 100%);}
# #chatbox {height: min(750px, 100%); max-height: min(750px, 100%);}
# #chatbox.block {height: 730px}
# .wrap {max-height: 680px;}
# .scroll-hide {overflow-y: scroll; max-height: 100px;}

DEBUG = False

DEFAULT_BACKEND = "openai-chat"
MAX_NUM_PLAYERS = 5
DEFAULT_NUM_PLAYERS = 5
CURRENT_STEP_INDEX = 0

def load_examples():
    example_configs = {}
    # Load json config files from examples folder
    example_files = glob("examples/*.json")
    for example_file in example_files:
        with open(example_file, encoding="utf-8") as f:
            example = json.load(f)
            try:
                example_configs[example["name"]] = example
            except KeyError:
                print(f"Example {example_file} is missing a name field. Skipping.")
    return example_configs


EXAMPLE_REGISTRY = load_examples()

# DB = SupabaseDB() if supabase_available else None

def get_player_components(name, visible):
    with gr.Row():
        with gr.Column():
            role_name = gr.Textbox(
                lines=1,
                show_label=False,
                interactive=True,
                visible=False,
                value=name,
            )
            
            # is benign, is_knowledgeable, is_responsible, 
            # player_config = gr.CheckboxGroup(
            #     choices=["Benign", "Knowledgeable", "Responsible"],
            #     label="Reviewer Type",
            #     visible=visible,
            # )
            
            with gr.Row():
                # Converting the three attributes into dropdowns
                Intention_config = gr.Dropdown(
                    choices=["Benign", "Malicious", "Neutral"],
                    interactive=True,
                    label = "Intention",
                    show_label=True,
                    value="Neutral",
                )
                
                Knowledge_config = gr.Dropdown(
                    choices=["Knowledgeable", "Unknownledgeable", "Normal"],
                    interactive=True,
                    label = "Knowledgeability",
                    show_label=True,
                    value="Normal",
                )
                
                Responsibility_config = gr.Dropdown(
                    choices=["Responsible", "Irresponsible", "Normal"],
                    interactive=True,
                    label = "Responsibility",
                    show_label=True,
                    value="Normal",
                )
                
            
            role_desc = gr.Textbox(
                lines=8,
                max_lines=8,
                show_label=False,
                interactive=True,
                visible=visible,
                autoscroll=False,
                value=get_reviewer_description()
            )

            def update_role_desc(Intention_config, Knowledge_config, Responsibility_config):
                
                is_benign = True if Intention_config == "Benign" else (False if Intention_config == "Malicious" else None)
                is_knowledgeable = True if Knowledge_config == "Knowledgeable" else (False if Knowledge_config == "Unknownledgeable" else None)
                is_responsible = True if Responsibility_config == "Responsible" else (False if Responsibility_config == "Lazy" else None)
                
                phase = 'reviewer_write_reviews' if CURRENT_STEP_INDEX < 2 else 'reviewer_ac_discussion'
                return get_reviewer_description(is_benign, is_knowledgeable, is_responsible, phase=phase)  # FIXME:依据阶段变化
                
            Intention_config.select(fn=update_role_desc, inputs=[Intention_config, Knowledge_config, Responsibility_config], outputs=[role_desc])
            Knowledge_config.select(fn=update_role_desc, inputs=[Intention_config, Knowledge_config, Responsibility_config], outputs=[role_desc])
            Responsibility_config.select(fn=update_role_desc, inputs=[Intention_config, Knowledge_config, Responsibility_config], outputs=[role_desc])
            
        with gr.Column():
            backend_type = gr.Dropdown(
                show_label=False,
                choices=list(BACKEND_REGISTRY.keys()),
                interactive=True,
                visible=visible,
                value=DEFAULT_BACKEND,
            )
            with gr.Accordion(
                f"{name} Parameters", open=False, visible=visible
            ) as accordion:
                temperature = gr.Slider(
                    minimum=0.,
                    maximum=2.0,
                    step=0.1,
                    interactive=True,
                    visible=visible,
                    label="temperature",
                    value=0.7,
                )
                max_tokens = gr.Slider(
                    minimum=10,
                    maximum=500,
                    step=10,
                    interactive=True,
                    visible=visible,
                    label="max tokens",
                    value=200,
                )

    return [role_name, Intention_config, Knowledge_config, Responsibility_config, backend_type, accordion, temperature, max_tokens]


def get_author_components(name, visible):
    with gr.Row():
        with gr.Column():
            role_desc = gr.Textbox(
                lines=8,
                max_lines=8,
                show_label=False,
                interactive=True,
                visible=visible,
                value=get_author_description(),
            )
        with gr.Column():
            backend_type = gr.Dropdown(
                show_label=False,
                choices=list(BACKEND_REGISTRY.keys()),
                interactive=True,
                visible=visible,
                value=DEFAULT_BACKEND,
            )
            with gr.Accordion(
                f"{name} Parameters", open=False, visible=visible
            ) as accordion:
                temperature = gr.Slider(
                    minimum=0.,
                    maximum=2.0,
                    step=0.1,
                    interactive=True,
                    visible=visible,
                    label="temperature",
                    value=0.7,
                )
                max_tokens = gr.Slider(
                    minimum=10,
                    maximum=500,
                    step=10,
                    interactive=True,
                    visible=visible,
                    label="max tokens",
                    value=200,
                )

    return [role_desc, backend_type, accordion, temperature, max_tokens]


def get_area_chair_components(name, visible):
    with gr.Row():
        with gr.Column():
            
            role_name = gr.Textbox(
                lines=1,
                show_label=False,
                interactive=True,
                visible=False,
                value=name,
            )
             
            AC_type = gr.Dropdown(
                label = "AC Type",
                show_label=True,
                choices=["Inclusive", "Conformist", "Authoritarian", "Normal"],
                interactive=True,
                visible=visible,
                value="Normal",
            )
                          
            role_desc = gr.Textbox(
                lines=8,
                max_lines=8,
                show_label=False,
                interactive=True,
                visible=visible,
                value=get_ac_description("BASELINE", "ac_write_metareviews", 'None', 1),
            )

            def update_role_desc(AC_type):
                ac_type = 'BASELINE' if AC_type == "Normal" else AC_type.lower()
                return get_ac_description(ac_type, "ac_write_metareviews", "None", 1) # FIXME:依据阶段变化

            AC_type.select(fn=update_role_desc, inputs=[AC_type], outputs=[role_desc])

        with gr.Column():
            backend_type = gr.Dropdown(
                show_label=False,
                choices=list(BACKEND_REGISTRY.keys()),
                interactive=True,
                visible=visible,
                value=DEFAULT_BACKEND,
            )
            with gr.Accordion(
                f"{name} Parameters", open=False, visible=visible
            ) as accordion:
                temperature = gr.Slider(
                    minimum=0,
                    maximum=2.0,
                    step=0.1,
                    interactive=True,
                    visible=visible,
                    label="temperature",
                    value=0.7,
                )
                max_tokens = gr.Slider(
                    minimum=10,
                    maximum=500,
                    step=10,
                    interactive=True,
                    visible=visible,
                    label="max tokens",
                    value=200,
                )

    return [role_name, AC_type, backend_type, accordion, temperature, max_tokens]


def get_empty_state():
    return gr.State({"arena": None})


with (gr.Blocks(css=css) as demo):
    state = get_empty_state()
    all_components = []

    with gr.Column(elem_id="col-container"):
        gr.Markdown(
            """
# [AgentReview](https://arxiv.org/abs/2406.12708) 🎓
Simulate conference reviews on your own papers using LLM agents.

**[🌐Homepage](https://github.com/Ahren09/AgentReview)** | **[💻Code](https://github.com/Ahren09/AgentReview)** | **[
📄Paper](https://aclanthology.org/2024.emnlp-main.70/)** | **[🔗arXiv](https://arxiv.org/abs/2406.12708)**
""",
            elem_id="header",
        )
        
        # Environment configuration
        env_desc_textbox = gr.Textbox(
            show_label=True,
            lines=2,
            visible=True,
            label="Environment Description",
            interactive=True,
            # placeholder="Enter a description of a scenario or the game rules.",
            value=const.GLOBAL_PROMPT,
        )
        
        all_components += [env_desc_textbox]
        
        with gr.Row():
            with gr.Column(elem_id="col-chatbox"):
                with gr.Tab("All", visible=True):
                    chatbot = gr.Chatbot(
                        elem_id="chatbox", visible=True, show_label=False, height=600
                    )

                player_chatbots = []
                for i in range(MAX_NUM_PLAYERS):
                    if i in [0, 1, 2]:
                        player_name = f"Reviewer {i + 1}"

                    elif i == 3:
                        player_name = "AC"

                    elif i == 4:
                        player_name = "Author"

                    with gr.Tab(player_name, visible=(i < DEFAULT_NUM_PLAYERS)):
                        player_chatbot = gr.Chatbot(
                            elem_id=f"chatbox-{i}",
                            visible=i < DEFAULT_NUM_PLAYERS,
                            label=player_name,
                            show_label=False,
                            height=600,  # FIXME: this parameter is not working
                        )
                        player_chatbots.append(player_chatbot)

            all_components += [chatbot, *player_chatbots]

            with gr.Column(elem_id="col-config"):  # Player Configuration
                # gr.Markdown("Player Configuration")
                
                # parallel_checkbox = gr.Checkbox(
                #     label="Parallel Actions", value=False, visible=True
                # )
                
                all_players_components, players_idx2comp = [], {}
                with gr.Blocks():
                    for i in range(MAX_NUM_PLAYERS):
                        if i in [0, 1, 2]:
                            player_name = f"Reviewer {i + 1}"

                        elif i == 3:
                            player_name = "AC"

                        elif i == 4:
                            player_name = "Author"

                        else:
                            raise ValueError(f"Invalid player index: {i}")
                        with gr.Tab(
                            player_name, visible=(i < DEFAULT_NUM_PLAYERS)
                        ) as tab:
                            if "Reviewer" in player_name:
                                player_comps = get_player_components(
                                    player_name, visible=(i < DEFAULT_NUM_PLAYERS)
                                )
                            elif player_name == "AC":
                                player_comps = get_area_chair_components(
                                    player_name, visible=(i < DEFAULT_NUM_PLAYERS)
                                )
                            elif player_name == "Author":
                                player_comps = get_author_components(
                                    player_name, visible=(i < DEFAULT_NUM_PLAYERS)
                                )

                        players_idx2comp[i] = player_comps + [tab]
                        all_players_components += player_comps + [tab]

                all_components += all_players_components
                
                # human_input_textbox = gr.Textbox(
                #     show_label=True,
                #     label="Human Input",
                #     lines=1,
                #     visible=True,
                #     interactive=True,
                #     placeholder="Upload your paper here",
                # )
                
                upload_file_box = gr.File(
                    visible=True,
                    height = 100,
                )
                
                with gr.Row():
                    btn_step = gr.Button("Submit")
                    btn_restart = gr.Button("Clear")

                all_components += [upload_file_box, btn_step, btn_restart]
    
    
    def _convert_to_chatbot_output(all_messages, display_recv=False):
        chatbot_output = []
        for i, message in enumerate(all_messages):
            agent_name, msg, recv = (
                message.agent_name,
                message.content,
                str(message.visible_to),
            )
            new_msg = re.sub(
                r"\n+", "<br>", msg.strip()
            )  # Preprocess message for chatbot output
            if display_recv:
                new_msg = f"**{agent_name} (-> {recv})**: {new_msg}"  # Add role to the message
            else:
                new_msg = f"**{agent_name}**: {new_msg}"

            if agent_name == "Moderator":
                chatbot_output.append((new_msg, None))
            else:
                chatbot_output.append((None, new_msg))
        return chatbot_output
    
    def _create_arena_config_from_components(all_comps: dict):
        
        env_desc = all_comps[env_desc_textbox]
        paper_pdf_path = all_comps[upload_file_box]
        
        # Step 1: Initialize the players
        num_players = MAX_NUM_PLAYERS
        
        # You can ignore these fields for the demo
        conference = "EMNLP2024"
        paper_decision = "Accept"
        data_dir = ''
        paper_id = "12345"

        args = Namespace(openai_client_type="azure_openai",
                         experiment_name="test",
                         max_num_words=16384)
        
        # 在paper_decision 阶段 中只启用 AC
        players = []
        
        # 不能直接获取role_desc，需要根据Intention_config, Knowledge_config, Responsibility_config生成一个配置
        # self.environment.experiment_setting["players"]['Reviewer'][reviewer_index - 1]
        
        experiment_setting = {
        "paper_id": paper_id,
        "paper_decision": paper_decision,
        "players": {

            # Paper Extractor is a special player that extracts a paper from the dataset.
            # Its constructor does not take any arguments.
            "Paper Extractor": [{}],

            # Assume there is only one area chair (AC) in the experiment.
            "AC": [],

            # Author role with default configuration.
            "Author": [{}],

            # Reviewer settings are generated based on reviewer types provided in the settings.
            "Reviewer": [],
        },
            # "global_settings": setting['global_settings']
        }
        
        
        for i in range(num_players):

            role_name = role_desc = backend_type = temperature = max_tokens = None

            if i in [0, 1, 2]: # reviewer
                role_name, intention_config, knowledge_config, responsibility_config, backend_type, temperature, max_tokens = (
                    all_comps[c]
                    for c in players_idx2comp[i]
                    if not isinstance(c, (gr.Accordion, gr.Tab))
                )
                
                is_benign = True if intention_config == "Benign" else (False if intention_config == "Malicious" else None)
                is_knowledgeable = True if knowledge_config == "Knowledgeable" else (False if knowledge_config == "Unknownledgeable" else None)
                is_responsible = True if responsibility_config == "Responsible" else (False if responsibility_config == "Lazy" else None)
                
                experiment_setting["players"]['Reviewer'].append({"is_benign": is_benign, 
                                                                    "is_knowledgeable": is_knowledgeable, 
                                                                    "is_responsible": is_responsible,
                                                                    "knows_authors": 'unfamous'})
                    
                role_desc = get_reviewer_description(is_benign, is_knowledgeable, is_responsible)
            
            elif i == 3: # AC
                role_name, ac_type, backend_type, temperature, max_tokens = (
                    all_comps[c]
                    for c in players_idx2comp[i]
                    if not isinstance(c, (gr.Accordion, gr.Tab))
                )
                
                ac_type = 'BASELINE' if ac_type == "Normal" else ac_type.lower()
                
                experiment_setting["players"]['AC'].append({"area_chair_type": ac_type})
                
                role_desc = get_ac_description(ac_type, "ac_write_metareviews", "None", 1)

            elif i == 4: # Author
                role_name, backend_type, temperature, max_tokens = (
                    all_comps[c]
                    for c in players_idx2comp[i]
                    if not isinstance(c, (gr.Accordion, gr.Tab))
                )

                role_desc = get_author_description()

            else:
                raise ValueError(f"Invalid player index: {i}")



            # common config for all players
            player_config = {
                "name": role_name,
                "role_desc": role_desc,
                "global_prompt": env_desc,
                "backend": {
                    "backend_type": backend_type,
                    "temperature": temperature,
                    "max_tokens": max_tokens,
                },
            }
            
            player_config = AgentConfig(**player_config)
            
            if i < num_players-1:
                player = Reviewer(data_dir=data_dir, conference=conference, args=args, **player_config)
            else:
                player_config["env_type"] = "paper_review"
                player = AreaChair(data_dir=data_dir, conference=conference, args=args, **player_config)
            
            players.append(player)
            
        # 根据上面的player_config和人造生成该阶段的players
        # if CURRENT_STEP == "paper_review":
            
        # 人为加入paper extractor
        paper_extractor_config = get_paper_extractor_config(max_tokens=2048)

        paper_extractor = PaperExtractorPlayer(paper_pdf_path=paper_pdf_path,
                                            data_dir=data_dir, paper_id=paper_id,
                                            paper_decision=paper_decision, args=args,
                                            conference=conference, **paper_extractor_config)
        players.append(paper_extractor)
        
        # 人为加入author
        author_config = get_author_config()
        author = Player(data_dir=data_dir, conference=conference, args=args,
                        **author_config)
        
        players.append(author)
            
        
        player_names = [player.name for player in players]
        
        # Step 2: Initialize the environment
        env = PaperReview(player_names=player_names, paper_decision=paper_decision, paper_id=paper_id,
                          args=args, experiment_setting=experiment_setting)
        
        # Step 3: Initialize the Arena
        arena = PaperReviewArena(players=players, environment=env, args=args, global_prompt=env_desc)
        
        return arena
        
    def step_game(all_comps: dict):
        global CURRENT_STEP_INDEX
        
        yield {
            btn_step: gr.update(value="Running...", interactive=False),
            btn_restart: gr.update(interactive=False),
        }
        
        cur_state = all_comps[state]
        
        # If arena is not yet created, create it
        if cur_state["arena"] is None:
            # Create the Arena
            arena = _create_arena_config_from_components(all_comps)
            cur_state["arena"] = arena
        else:
            arena = cur_state["arena"]
        
        # TODO: 连续运行
        
        timestep = arena.step()
        
        CURRENT_STEP_INDEX = int(arena.environment.phase_index)
        
        # 更新前端信息
        if timestep:
            all_messages = timestep.observation
            all_messages[0].content = 'Paper content has been extracted.'
            chatbot_output = _convert_to_chatbot_output(all_messages, display_recv=True)

            # Initialize update dictionary
            update_dict = {
                chatbot: chatbot_output,
                btn_step: gr.update(
                    value="Next Step", interactive=not timestep.terminal
                ),
                btn_restart: gr.update(interactive=True),
                state: cur_state,
            }

            # Define a mapping of player names to their respective chatbots
            player_name_to_chatbot = {
                "Reviewer 1": player_chatbots[0],
                "Reviewer 2": player_chatbots[1],
                "Reviewer 3": player_chatbots[2],
                "AC": player_chatbots[3],
                "Author": player_chatbots[4],
            }

            # Update each player's chatbot output
            for player in arena.players:
                player_name = player.name
                if player_name in player_name_to_chatbot:
                    player_messages = arena.environment.get_messages_from_player(player_name)
                    # player_messages[0].content = 'Paper content has been extracted.'
                    player_output = _convert_to_chatbot_output(player_messages)
                    update_dict[player_name_to_chatbot[player_name]] = player_output

            # # Reviewer 1, 2, 3 Area Chair, Paper Extractor, Author
            # for i, player in enumerate(arena.players):
            #     player_name = player.name
            #     # Get the messages for the current player
            #     player_messages = arena.environment.get_observation(player_name)
            #     player_messages[0].content = 'Paper content has been extracted.'
            #
            #     # Convert messages to chatbot output
            #     player_output = _convert_to_chatbot_output(player_messages)


                """
                if 'Reviewer' in player.name and arena.environment.phase_index < 4: # FIXME: 临时逻辑
                    player_messages = arena.environment.get_observation(player.name)
                    # 不要显示第一条长段的信息，只显示 文章内容已被抽取
                    player_messages[0].content = 'Paper content has been extracted.'
                    player_output = _convert_to_chatbot_output(player_messages)
                    # Update the player's chatbot output
                    update_dict[player_chatbots[i]] = player_output
                elif arena.environment.phase_index in [4, 5]: # FIXME: 临时逻辑
                    player_messages = arena.environment.get_observation('AC')
                    player_messages[0].content = 'Paper content has been extracted.'
                    player_output = _convert_to_chatbot_output(player_messages)
                    # Update the player's chatbot output
                    update_dict[player_chatbots[3]] = player_output
                """
            # Ahren: Auto run
            # if not timestep.terminal:
            #     yield from step_game(all_comps)

            yield update_dict
        
            
    def restart_game(all_comps: dict):
        global CURRENT_STEP_INDEX
        CURRENT_STEP_INDEX = 0
        
        cur_state = all_comps[state]
        cur_state["arena"] = None
        yield {
            chatbot: [],
            btn_restart: gr.update(interactive=False),
            btn_step: gr.update(interactive=False),
            state: cur_state,
        }

        # arena_config = _create_arena_config_from_components(all_comps)
        # arena = Arena.from_config(arena_config)
        # log_arena(arena, database=DB)
        # cur_state["arena"] = arena

        yield {
            btn_step: gr.update(value="Start", interactive=True),
            btn_restart: gr.update(interactive=True),
            upload_file_box: gr.update(value=None),
            state: cur_state,
        }
    
    # Remove Accordion and Tab from the list of components
    all_components = [
        comp for comp in all_components if not isinstance(comp, (gr.Accordion, gr.Tab))
    ]
    
    # update component
    # env_desc_textbox.change()

    # If any of the Textbox, Slider, Checkbox, Dropdown, RadioButtons is changed, the Step button is disabled
    for comp in all_components:

        def _disable_step_button(state):
            if state["arena"] is not None:
                return gr.update(interactive=False)
            else:
                return gr.update()

        if (
            isinstance(
                comp, (gr.Textbox, gr.Slider, gr.Checkbox, gr.Dropdown, gr.Radio)
            )
            and comp is not upload_file_box
        ):
            comp.change(_disable_step_button, state, btn_step)

    # Ahren: Auto run
    btn_step.click(
        step_game,
        set(all_components + [state]),
        [chatbot, *player_chatbots, btn_step, btn_restart, state, upload_file_box],
    )
    
    btn_restart.click(
        restart_game,
        set(all_components + [state]),
        [chatbot, *player_chatbots, btn_step, btn_restart, state, upload_file_box],
    )

    
demo.queue()
demo.launch() 
