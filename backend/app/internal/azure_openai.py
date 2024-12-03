from openai import AzureOpenAI

class AzureOpenAIService:

    def __init__(self, endpoint: str, api_key: str, deployment_name: str):
        self.client = AzureOpenAI(
            azure_endpoint=endpoint,
            api_key=api_key,
            api_version="2024-06-01"
        )
        self.deployment_name = deployment_name
        self.system_prompt = "You Are helpful assistant."

    def close(self):
        self.client.close()
    
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

