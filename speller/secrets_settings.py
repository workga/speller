from pydantic_settings import BaseSettings

from speller.secrets import CHAT_GPT_SECRETS_SETTINGS_AUTH


class ChatGPTSecretsSettings(BaseSettings):
    auth: str = CHAT_GPT_SECRETS_SETTINGS_AUTH