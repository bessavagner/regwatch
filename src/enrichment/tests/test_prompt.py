import json

import httpx

from enrichment.anthropic_client import AnthropicLLMClient
from enrichment.categories import CATEGORIES
from enrichment.openai_client import OpenAILLMClient
from enrichment.prompt import SYSTEM_PROMPT


def test_every_category_is_defined_with_an_example():
    # The D3 defect in one assertion: six labels were named and none defined,
    # so the model had no criteria to be consistent against.
    for value in CATEGORIES:
        assert f"- {value}:" in SYSTEM_PROMPT, f"{value} has no definition line"
    # One worked example per label except `other`, which is defined by exclusion.
    assert SYSTEM_PROMPT.count("Ex.:") == len(CATEGORIES) - 1


def test_the_rubric_defines_every_category_and_no_others():
    # Moved here from test_categories.py, which parsed the old flat
    # "um de: grant, penalty, ..." list the rubric replaced. The rubric must
    # stay in step with the stored vocabulary in both directions: a label
    # defined here but absent from CATEGORIES would be coerced to `other` on
    # arrival, silently.
    defined = {
        line.split(":", 1)[0].removeprefix("- ")
        for line in SYSTEM_PROMPT.splitlines()
        if line.startswith("- ")
    }
    assert defined == set(CATEGORIES)


def test_the_two_measured_clusters_are_routed_explicitly():
    # These are the exact phrases the 2026-08-20 review measured splitting
    # 12/5 and 10/2 between regulation and other. The rubric names them.
    regulation_line = next(
        line for line in SYSTEM_PROMPT.splitlines() if line.startswith("- regulation:")
    )
    assert "anuiu previamente" in regulation_line.lower()
    assert "utilidade pública" in regulation_line.lower()


def test_other_is_defined_as_a_last_resort_not_a_shrug():
    other_line = next(
        line for line in SYSTEM_PROMPT.splitlines() if line.startswith("- other:")
    )
    assert "SOMENTE" in other_line


def test_anthropic_sends_the_rubric_as_its_system_prompt():
    captured = {}

    def handler(request):
        captured["body"] = json.loads(request.content)
        return httpx.Response(200, json={"content": [{"type": "text", "text": json.dumps(
            {"summary": "s", "category": "other", "confidence": 0.5})}]})

    AnthropicLLMClient("sk-test", transport=httpx.MockTransport(handler)).summarize("a", [])
    assert captured["body"]["system"] == SYSTEM_PROMPT


def test_openai_sends_the_rubric_as_its_system_message():
    captured = {}

    def handler(request):
        captured["body"] = json.loads(request.content)
        return httpx.Response(200, json={"choices": [{"message": {"content": json.dumps(
            {"summary": "s", "category": "other", "confidence": 0.5})}}]})

    OpenAILLMClient("sk-test", transport=httpx.MockTransport(handler)).summarize("a", [])
    assert captured["body"]["messages"][0] == {"role": "system", "content": SYSTEM_PROMPT}


def test_each_signal_is_asked_for_as_something_checkable():
    for key in ("names_party", "has_amount", "has_deadline"):
        assert f'"{key}"' in SYSTEM_PROMPT
    # The point of D5: the model is asked what the text says, not how sure it is.
    assert "valor em reais" in SYSTEM_PROMPT
    assert "prazo" in SYSTEM_PROMPT
