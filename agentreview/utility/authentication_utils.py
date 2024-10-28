import logging
import os

import openai

logging.basicConfig(level=logging.INFO)


def get_openai_client(client_type: str):
    """

    Refer to [this page](https://platform.openai.com/docs/models) for authentication using OpenAI.
    Refer to [this page](https://learn.microsoft.com/en-us/azure/ai-services/openai/how-to/switching-endpoints) for
    authentication using Azure OpenAI.
    """

    assert client_type in ["azure_openai", "openai"]

    endpoint: str = os.environ['AZURE_ENDPOINT']

    if not endpoint.startswith("https://"):
        endpoint = f"https://{endpoint}.openai.azure.com"

    os.environ['AZURE_ENDPOINT'] = endpoint

    if not os.environ.get('OPENAI_API_VERSION'):
        os.environ['OPENAI_API_VERSION'] = "2023-05-15"

    if client_type == "openai":
        client = openai.OpenAI(
            api_key=os.environ['OPENAI_API_KEY']
        )

    elif client_type == "azure_openai":
        client = openai.AzureOpenAI(
            api_key=os.environ['AZURE_OPENAI_KEY'],
            azure_endpoint=os.environ['AZURE_ENDPOINT'],  # f"https://YOUR_END_POINT.openai.azure.com"
            azure_deployment=os.environ['AZURE_DEPLOYMENT']
        )

    else:
        raise NotImplementedError

    return client
