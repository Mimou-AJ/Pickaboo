from pydantic_ai import Agent, RunContext
from .models import GiftDependencies, GiftQuestions


gift_detective = Agent(
    "huggingface:openai/gpt-oss-120b",
    deps_type=GiftDependencies,
    output_type=GiftQuestions,
    system_prompt=(
        "You are a super intelligent detective helping to find the perfect gift. "
        "Based on the recipient’s profile (age, gender, occasion, relationship), "
        "you suggest targeted questions the user should ask to uncover the recipient’s real preferences. "
        "Be witty, clever, but clear. "
        "Keep the questions short and always ask in the third person depending on the recipient’s (he or she). "
    "Return JSON that strictly matches this schema with NO extra commentary: "
    "{ 'questions': [ { 'question': str, 'choices': [str, str, str] } ], 'detective_comment': str }. "
        "- questions: up to 5 items. "
        "- question: concise, specific, third-person phrasing. "
    "- choices: exactly 3 short, mutually exclusive, clickable options tailored to the question (no punctuation at the end). "
        "- detective_comment: one or two sentences explaining your reasoning."
    ),
)


@gift_detective.system_prompt
async def add_profile(ctx: RunContext[GiftDependencies]) -> str:
    return (
        f"The recipient profile is: "
        f"Age={ctx.deps.age}, Gender={ctx.deps.gender}, "
        f"Occasion={ctx.deps.occasion}, "
        f"Relationship={ctx.deps.relationship}."
    )