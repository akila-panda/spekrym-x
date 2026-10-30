"""Phase 9C-1: Groq and Gemini adapters against mocked HTTP (never the real services)."""

import json

import httpx
import pytest
from pydantic import SecretStr

from sx_assistant.analyst.config import ApprovalError, build_providers
from sx_assistant.analyst.errors import AuthError, BadRequest, RateLimited, Transient
from sx_assistant.analyst.provider import ModelSpec
from sx_assistant.analyst.providers.gemini import GeminiProvider
from sx_assistant.analyst.providers.groq import GroqProvider
from sx_core.config import Settings

KEY = "sk-test-SECRET-123"


def client(handler):
    return httpx.Client(transport=httpx.MockTransport(handler))


def groq(handler):
    return GroqProvider(ModelSpec("groq", "m1"), SecretStr(KEY), client(handler))


def gemini(handler):
    return GeminiProvider(ModelSpec("gemini", "g1"), SecretStr(KEY), client(handler))


def test_groq_request_shape_and_parse():
    seen = {}

    def h(req):
        seen.update(url=str(req.url), auth=req.headers["authorization"],
                    body=json.loads(req.content))
        return httpx.Response(200, json={"choices": [{"message": {"content": "hi"}}],
                                         "usage": {"prompt_tokens": 7, "completion_tokens": 3}})

    c = groq(h).complete("sys", "usr")
    assert seen["url"] == "https://api.groq.com/openai/v1/chat/completions"
    assert seen["auth"] == f"Bearer {KEY}" and KEY not in json.dumps(seen["body"])
    assert seen["body"]["model"] == "m1" and seen["body"]["temperature"] == 0
    assert seen["body"]["messages"][0] == {"role": "system", "content": "sys"}
    assert (c.text, c.prompt_tokens, c.completion_tokens) == ("hi", 7, 3)


def test_gemini_key_is_a_header_never_in_the_url():
    seen = {}

    def h(req):
        seen.update(url=str(req.url), key=req.headers["x-goog-api-key"],
                    body=json.loads(req.content))
        return httpx.Response(200, json={
            "candidates": [{"content": {"parts": [{"text": "a"}, {"text": "b"}]}}],
            "usageMetadata": {"promptTokenCount": 5, "candidatesTokenCount": 2}})

    c = gemini(h).complete("sys", "usr")
    assert seen["url"] == ("https://generativelanguage.googleapis.com/v1beta/models/"
                           "g1:generateContent")
    assert KEY not in seen["url"] and seen["key"] == KEY
    assert seen["body"]["systemInstruction"]["parts"][0]["text"] == "sys"
    assert (c.text, c.prompt_tokens, c.completion_tokens) == ("ab", 5, 2)


@pytest.mark.parametrize("make", [groq, gemini])
@pytest.mark.parametrize("status,exc", [(429, RateLimited), (401, AuthError), (403, AuthError),
                                        (500, Transient), (503, Transient), (400, BadRequest)])
def test_status_codes_map_to_errors(make, status, exc):
    p = make(lambda r: httpx.Response(status, json={"error": {"message": f"bad {KEY}"}},
                                      headers={"retry-after": "12"}))
    with pytest.raises(exc) as e:
        p.complete("s", "u")
    assert KEY not in str(e.value)
    if status == 429:
        assert e.value.retry_after == 12.0


@pytest.mark.parametrize("make", [groq, gemini])
def test_timeout_and_garbage_are_transient_and_not_retried(make):
    calls = []

    def h(req):
        calls.append(1)
        raise httpx.ReadTimeout("slow")

    with pytest.raises(Transient, match="may still have used quota"):
        make(h).complete("s", "u")
    assert len(calls) == 1
    with pytest.raises(Transient):
        make(lambda r: httpx.Response(200, text="<html>")).complete("s", "u")
    with pytest.raises(Transient):
        make(lambda r: httpx.Response(200, json={})).complete("s", "u")


@pytest.mark.parametrize("make", [groq, gemini])
def test_oversize_input_is_refused_before_any_request(make):
    def boom(req):
        raise AssertionError("request must not be sent")

    with pytest.raises(BadRequest):
        make(boom).complete("s", "x" * 30_000)


def test_list_models():
    g = groq(lambda r: httpx.Response(200, json={"data": [{"id": "b"}, {"id": "a"}]}))
    assert g.list_models() == ["a", "b"]
    m = gemini(lambda r: httpx.Response(200, json={"models": [
        {"name": "models/x", "supportedGenerationMethods": ["generateContent"]},
        {"name": "models/e", "supportedGenerationMethods": ["embedContent"]}]}))
    assert m.list_models() == ["x"]


def _approved(tmp_path, confirmed):
    p = tmp_path / "approved.json"
    p.write_text(json.dumps({"models": [
        {"provider": "groq", "model": "openai/gpt-oss-20b", "owner_confirmed_free": confirmed},
        {"provider": "gemini", "model": "gemini-3.8-flash", "owner_confirmed_free": confirmed}]}))
    return p


def test_unconfirmed_or_unlisted_models_are_refused(tmp_path):
    s = Settings(groq_api_key=SecretStr(KEY), gemini_api_key=SecretStr(KEY))
    with pytest.raises(ApprovalError, match="not confirmed free"):
        build_providers(s, {}, approved_path=_approved(tmp_path, False))
    with pytest.raises(ApprovalError, match="not in approved_models.json"):
        build_providers(s, {"SX_GROQ_MODEL": "some/paid-model"},
                        approved_path=_approved(tmp_path, True))
    ok = build_providers(s, {}, approved_path=_approved(tmp_path, True))
    assert [p.spec.provider_id for p in ok.providers] == ["groq", "gemini"]


def test_missing_key_skips_the_provider_and_keys_stay_out_of_repr(tmp_path):
    s = Settings(groq_api_key=SecretStr(KEY))
    r = build_providers(s, {}, approved_path=_approved(tmp_path, True))
    assert [p.spec.provider_id for p in r.providers] == ["groq"] and "gemini" in r.skipped
    assert KEY not in repr(s) and KEY not in repr(r)


def test_shipped_approved_file_is_unconfirmed_by_default():
    from sx_assistant.analyst.config import load_approved
    assert not any(m["owner_confirmed_free"] for m in load_approved().values())


def test_unconfirmed_provider_is_skipped_when_another_is_confirmed(tmp_path):
    s = Settings(groq_api_key=SecretStr(KEY), gemini_api_key=SecretStr(KEY))
    p = tmp_path / "approved.json"
    p.write_text(json.dumps({"models": [
        {"provider": "groq", "model": "openai/gpt-oss-20b", "owner_confirmed_free": False},
        {"provider": "gemini", "model": "gemini-3.8-flash", "owner_confirmed_free": True}]}))
    out = build_providers(s, {}, approved_path=p)
    assert [q.spec.provider_id for q in out.providers] == ["gemini"]
    assert "groq" in out.skipped and "never called" in out.skipped["groq"]
