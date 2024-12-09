from openai import AzureOpenAI, AsyncAzureOpenAI
import time

class AzureOpenAIService:

    def __init__(self, endpoint: str, api_key: str, deployment_name: str):
        # TODO: may need to set up AsyncAzureOpenAI client only and convert all the calls under this class to async
        self.client = AzureOpenAI(
            azure_endpoint=endpoint,
            api_key=api_key,
            api_version="2024-06-01"
        )
        self.stream_client = AsyncAzureOpenAI(
            azure_endpoint=endpoint,
            api_key=api_key,
            api_version="2024-06-01"
        )
        self.deployment_name = deployment_name
        self.system_prompt = "You Are helpful assistant."

    def close(self):
        self.client.close()
        self.stream_client.close()
    
    def aoai_completion_simple(self, user_prompt: str) -> str:
        # checking if the user prompt is empty string, if it is throw an error
        if user_prompt == "":
            raise ValueError("User prompt cannot be empty")

        messages = [
            {
                "role": "system",
                "content": self.system_prompt
            },
            {
                "role": "user",
                "content": user_prompt
            }
        ]

        response = self.client.chat.completions.create(
            model=self.deployment_name,
            messages=messages,
            temperature=0,
        )

        return response.choices[0].message.content

    async def aoai_completion_simple_stream(self, user_prompt: str):
        # checking if the user prompt is empty string, if it is throw an error
        if user_prompt == "":
            raise ValueError("User prompt cannot be empty")

        messages = [
            {
                "role": "system",
                "content": self.system_prompt
            },
            {
                "role": "user",
                "content": user_prompt
            }
        ]

        response = await self.stream_client.chat.completions.create(
            model=self.deployment_name,
            messages=messages,
            temperature=0,
            stream=True
        )

        async for chunk in response:
            if len(chunk.choices) > 0:
                delta = chunk.choices[0].delta
                if delta.content:
                    yield delta.content
         