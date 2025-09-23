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
        "Always explain briefly why you chose these questions."
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