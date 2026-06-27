from django.conf import settings
from django.utils.module_loading import import_string


def get_llm_client():
    return import_string(settings.REGWATCH_LLM_CLIENT).from_env()


def get_email_sender():
    return import_string(settings.REGWATCH_EMAIL_SENDER).from_env()
