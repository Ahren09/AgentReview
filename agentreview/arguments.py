import argparse
import logging
import os
import sys

def parse_args():
    parser = argparse.ArgumentParser(description="Argument parser for configuring OpenAI API and experiment settings")

    # Authentication details for OpenAI API
    parser.add_argument(
        "--openai_key", type=str, default=None, help="API key to authenticate with OpenAI. Can be set via this argument or through the OPENAI_API_KEY environment variable."
    )

    parser.add_argument(
        "--deployment", type=str, default=None, help="For Azure OpenAI: the deployment name to be used when calling the API."
    )

    parser.add_argument(
        "--openai_client_type", type=str, default="openai", choices=["openai", "azure_openai"],
        help="Specify the OpenAI client type to use: 'openai' for standard OpenAI API or 'azure_openai' for Azure-hosted OpenAI services."
    )

    parser.add_argument(
        "--endpoint", type=str, default=None, help="For Azure OpenAI: custom endpoint to access the API. Should be in the format 'https://<your-endpoint>.openai.azure.com'."
    )


    parser.add_argument(
        "--api_version", type=str, default="2023-05-15", help="API version to be used for making requests. Required "
                                                              "for Azure OpenAI clients."
    )

    # Experiment configuration
    parser.add_argument(
        "--ac_scoring_method", type=str, default="ranking", choices=["recommendation", "ranking"],
        help="Specifies the scoring method used by the Area Chair (AC) to evaluate papers: 'recommendation' or 'ranking'."
    )

    parser.add_argument(
        "--conference", type=str, default="ICLR2023", help="Conference name where the papers are being evaluated, e.g., 'ICLR2023'."
    )

    parser.add_argument(
        "--num_reviewers_per_paper", type=int, default=3, help="The number of reviewers assigned to each paper."
    )

    parser.add_argument(
        "--experiment_name",
        type=str, default=None, required=False,
        choices=[
            "BASELINE", "benign_Rx1", "malicious_Rx1", "malicious_Rx2", "malicious_Rx3", "unknowledgeable_Rx1",
            "knowledgeable_Rx1", "responsible_Rx1", "irresponsible_Rx1", "irresponsible_Rx2", "irresponsible_Rx3",
            "inclusive_ACx1", "authoritarian_ACx1", "conformist_ACx1", "no_numeric_ratings"],
        help="Specifies the name of the experiment to run. Choose from predefined experiment types based on the reviewer and AC behavior or experiment configuration."
    )

    parser.add_argument(
        "--overwrite", action="store_true", help="If set, existing results or output files will be overwritten without prompting."
    )
    parser.add_argument(
        "--skip_logging", action="store_true", help="If set, we do not log the messages in the console."
    )

    parser.add_argument(
        "--num_papers_per_area_chair", type=int, default=10, help="The number of papers each area chair is assigned for evaluation."
    )

    # Model configuration
    parser.add_argument(
        "--model_name", type=str, default="gpt-4o", choices=["gpt-4", "gpt-4o", "gpt-35-turbo"],
        help="Specifies which GPT model to use: 'gpt-4' for the standard GPT-4 model, 'gpt-35-turbo' for a "
             "cost-effective alternative, or 'gpt-4o' for larger context support."
    )

    # Output directories
    parser.add_argument(
        "--output_dir", type=str, default="outputs", help="Directory where results, logs, and outputs will be stored."
    )

    # Output directories
    parser.add_argument(
        "--max_num_words", type=int, default=16384, help="Maximum number of words in the paper."
    )

    parser.add_argument(
        "--visual_dir", type=str, default="outputs/visual", help="Directory where visualization files (such as graphs and plots) will be stored."
    )

    # System configuration
    parser.add_argument(
        "--device", type=str, default='cuda', help="The device to be used for processing (e.g., 'cuda' for GPU acceleration or 'cpu' for standard processing)."
    )

    parser.add_argument(
        "--data_dir", type=str, default='data', help="Directory where input data (e.g., papers) are stored."
    )


    parser.add_argument(
        "--acceptance_rate", type=float, default=0.32,
        help="Percentage of papers to accept. We use 0.32, the average acceptance rate for ICLR 2020 - 2023"
    )

    args = parser.parse_args()

    # Ensure necessary directories exist
    os.makedirs(args.visual_dir, exist_ok=True)
    os.makedirs(args.output_dir, exist_ok=True)

    # Set 'player_to_test' based on experiment name
    if args.experiment_name is None:
        args.player_to_test = None
    elif "Rx" in args.experiment_name:
        args.player_to_test = "Reviewer"
    elif "ACx" in args.experiment_name:
        args.player_to_test = "Area Chair"
    elif "no_rebuttal" in args.experiment_name or "no_overall_score" in args.experiment_name:
        args.player_to_test = "Review Mechanism"

    # Sanity checks for authentication
    print("Running sanity checks for the arguments...")

    if args.openai_client_type == "openai":
        if os.environ.get('OPENAI_API_KEY') is None:
            assert isinstance(args.openai_key, str), ("Please specify the `--openai_key` argument OR set the "
                                                      "OPENAI_API_KEY environment variable.")
            raise ValueError("OpenAI key is missing.")

    if args.openai_client_type == "azure_openai":
        if os.environ.get('AZURE_OPENAI_KEY') is None:
            assert isinstance(args.openai_key, str), ("Please specify the `--openai_key` argument OR set the "
                                                      "AZURE_OPENAI_KEY environment variable.")
            os.environ['AZURE_OPENAI_KEY'] = args.openai_key

        if os.environ.get('AZURE_DEPLOYMENT') is None:
            assert isinstance(args.deployment, str), ("Please specify the `--deployment` argument OR set the "
                                                      "AZURE_DEPLOYMENT environment variable.")
            os.environ['AZURE_DEPLOYMENT'] = args.deployment

        if os.environ.get('AZURE_ENDPOINT') is None:
            assert isinstance(args.endpoint, str), ("Please specify the `--endpoint` argument OR set the "
                                                    "AZURE_ENDPOINT environment variable.")
            endpoint = args.endpoint
        else:
            endpoint = os.environ.get('AZURE_ENDPOINT')

        if not endpoint.startswith("https://"):
            endpoint = f"https://{endpoint}.openai.azure.com"
        os.environ['AZURE_ENDPOINT'] = endpoint

        if os.environ.get('OPENAI_API_VERSION') is None:
            assert isinstance(args.api_version, str), ("Please specify the `--api_version` argument OR set the "
                                                       "OPENAI_API_VERSION environment variable.")
            os.environ['OPENAI_API_VERSION'] = args.api_version

    return args
