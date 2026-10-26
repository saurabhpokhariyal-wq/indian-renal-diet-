# Probe: compare grounding (no SAFE/CAUTION/AVOID for invented dish) between old and new Claude model ids
import asyncio
import re
import sys
import uuid

sys.path.insert(0, "/app/backend")
from config import EMERGENT_LLM_KEY  # noqa: E402
from db import db  # noqa: E402
from ai_service import AI_SYSTEM_PROMPT_BASE, _build_ai_context, _build_grounded_food_block  # noqa: E402
from emergentintegrations.llm.chat import LlmChat, UserMessage  # noqa: E402

TIER = re.compile(r"\b(SAFE|CAUTION|AVOID)\b", re.IGNORECASE)
Q = "is zorplok curry safe for me?"


async def run(model, user, sysmsg, n=4):
    fails = 0
    for _ in range(n):
        chat = LlmChat(api_key=EMERGENT_LLM_KEY, session_id=f"probe-{uuid.uuid4().hex[:6]}",
                       system_message=sysmsg).with_model("anthropic", model)
        ans = str(await chat.send_message(UserMessage(text=Q)))
        t = TIER.findall(ans)
        if t:
            fails += 1
            print(f"  [{model}] tier words {t}: ...{ans[-250:]!r}")
    print(f"{model}: {fails}/{n} runs emitted tier words")


async def main():
    user = await db.users.find_one({"email": "demo@renal.app"}, {"_id": 0})
    sysmsg = AI_SYSTEM_PROMPT_BASE + await _build_ai_context(user, "en") + await _build_grounded_food_block(Q, user)
    await asyncio.gather(run("claude-sonnet-5-5", user, sysmsg), run("claude-sonnet-4-5-20250929", user, sysmsg))


asyncio.run(main())
