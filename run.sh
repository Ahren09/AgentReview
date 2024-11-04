# If you use OpenAI API, you need to set OPENAI_API_KEY.
export OPENAI_API_KEY=...

# If you use AzureOpenAI API, you need to set the following
export AZURE_ENDPOINT=...  # Format: https://<your-endpoint>.openai.azure.com/
export AZURE_DEPLOYMENT=...  # Your Azure OpenAI deployment here
export AZURE_OPENAI_KEY=... # Your Azure OpenAI key here

python run_paper_review_cli.py --conference ICLR2024 \
    --openai_client_type azure_openai \
    --data_dir data \
    --experiment_name malicious_Rx1