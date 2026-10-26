# Probe: verify the configured CLAUDE_MODEL is accepted by the Emergent LLM proxy (and a bogus id is rejected)
import asyncio
import sys
import uuid

sys.path.insert(0, "/app/backend")
from config import CLAUDE_MODEL, EMERGENT_LLM_KEY  # noqa: E402
from emergentintegrations.llm.chat import LlmChat, UserMessage  # noqa: E402


async def probe(model: str):
    chat = LlmChat(api_key=EMERGENT_LLM_KEY, session_id=f"probe-{uuid.uuid4().hex[:6]}",
                   system_message="Reply briefly.").with_model("anthropic", model)
    try:
        r = await chat.send_message(UserMessage(text="Which exact Claude model are you? One line."))
        print(f"[{model}] OK -> {str(r)[:200]}")
    except Exception as e:
        print(f"[{model}] FAIL -> {type(e).__name__}: {str(e)[:300]}")


async def main():
    print("CLAUDE_MODEL =", CLAUDE_MODEL)
    await probe(CLAUDE_MODEL)
    await probe("claude-sonnet-9-9-bogus")


asyncio.run(main())
