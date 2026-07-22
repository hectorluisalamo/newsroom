# ABOUTME: In-memory LLMProvider double used by tests and the $0 e2e fake-LLM seam.
# ABOUTME: Makes no network calls; generates canned text with [src:N] citation markers.
"""Fake LLM provider — the canonical no-network, no-spend LLMProvider double.

Lives in the production package (not tests/) so both the test suite and the
CLI's ``NEWSROOM_FAKE_LLM`` seam (see ``newsroom.cli``) can import the same
class. The class is inert unless instantiated, so importing it here carries
no runtime cost or risk in production code paths that don't opt into it.
"""

from newsroom.draft.provider import LLMProvider, LLMResponse


class FakeLLMProvider(LLMProvider):
    """In-memory LLMProvider double for draft/writer tests — makes no network calls.

    Generates canned text embedding real ``[src:N]`` citation markers so the
    writer's post-generation citation check has something to find. Two knobs
    control shape:

    - ``word_count``: number of space-joined filler tokens in each generated
      body (default 700). Every call after the first (or every call, if
      ``responses`` is not exhausted) reuses this word count.
    - ``responses``: an optional queue of explicit word counts, consumed one
      per call, to simulate a provider whose output length drifts across
      retries (e.g. ``[500, 500, 700]`` misses twice then lands on target).
      Once the queue is exhausted, calls fall back to ``word_count``.

    ``call_count`` tracks how many times ``generate`` has been invoked, so
    tests can assert on the writer's retry behavior and retry cap.
    """

    model_id_value = "fake-model-v1"

    def __init__(
        self,
        word_count: int = 700,
        responses: list[int] | None = None,
    ) -> None:
        """Initialize the fake provider's word count and optional retry queue."""
        self.word_count = word_count
        self._response_queue = list(responses) if responses else []
        self.call_count = 0

    def generate(
        self,
        system_prompt: str,
        user_prompt: str,
        max_tokens: int,
    ) -> LLMResponse:
        """Return canned text of a configured length, embedding [src:N] markers."""
        self.call_count += 1
        if self._response_queue:
            target_words = self._response_queue.pop(0)
        else:
            target_words = self.word_count
        text = _build_fake_body(target_words)
        return LLMResponse(
            text=text,
            token_usage={"input_tokens": 100, "output_tokens": target_words},
        )

    @property
    def model_id(self) -> str:
        """Return the fake provider's fixed model identifier."""
        return self.model_id_value


def _build_fake_body(word_count: int) -> str:
    """Build a space-joined filler body of `word_count` tokens with [src:N] markers.

    Both [src:1] and [src:2] are placed as early as the word count allows so
    they survive even short bodies; longer bodies get additional alternating
    markers sprinkled every 40 words for realism.
    """
    if word_count <= 0:
        return ""
    words = [f"word{i}" for i in range(word_count)]
    words[0] = "Reporting"
    if word_count > 1:
        words[1] = "[src:1]"
    if word_count > 2:
        words[2] = "[src:2]"
    for i in range(40, word_count, 40):
        words[i] = "[src:1]" if (i // 40) % 2 else "[src:2]"
    return " ".join(words)
