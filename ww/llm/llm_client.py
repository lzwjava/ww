import os


def call_llm_with_messages(messages, model=None, **kwargs):
    """Route to the appropriate LLM backend based on MODEL_PROVIDER env var.

    MODEL_PROVIDER: 'openrouter' (default) or 'copilot'
    MODEL: the raw model string passed to the provider (e.g. 'gpt-4o', 'anthropic/claude-opus-4.6')
    """
    provider = os.getenv("MODEL_PROVIDER", "openrouter")
    if model is None:
        model = os.getenv("MODEL")

    if provider == "copilot":
        from ww.llm.copilot_client import call_copilot_api_with_messages

        return call_copilot_api_with_messages(messages, model=model, **kwargs)
    else:
        from ww.llm.openrouter_client import call_openrouter_api_with_messages

        return call_openrouter_api_with_messages(messages, model=model, **kwargs)


def call_llm(prompt, model=None, **kwargs):
    messages = [{"role": "user", "content": prompt}]
    return call_llm_with_messages(messages, model=model, **kwargs)
