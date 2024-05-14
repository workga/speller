from pydantic_settings import BaseSettings


class ChatGPTSecretsSettings(BaseSettings):
    auth: str = ''