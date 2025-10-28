from pydantic_ai import Agent, RunContext
from .models import GiftDependencies, GiftQuestions


gift_detective = Agent(
    "huggingface:deepseek-ai/DeepSeek-V3.1",
    deps_type=GiftDependencies,
    output_type=GiftQuestions,
)


def get_initial_system_prompt(deps: GiftDependencies) -> str:
    """
    Build the initial system prompt for the first interaction.
    This is only used when there's no message history.
    """
    return (
        "You are a Senior Gift Psychology Consultant and a super intelligent detective helping to find the perfect gift. "
        f"The recipient profile is: Age={deps.age}, Gender={deps.gender}, "
        f"Occasion={deps.occasion}, Budget={deps.budget}, Relationship={deps.relationship}. "
        "Ask 5 GENERAL questions to understand the recipient's profile and preferences better. "
        "The questions should be broad but still tailored to the recipient's age, gender, occasion, and relationship. "
        "Be witty, clever, but clear. "
        "Keep the questions short and always ask in the third person depending on the recipient's gender (he or she). "
        "Return JSON that strictly matches this schema with NO extra commentary: "
        "{ 'questions': [ { 'question': str, 'choices': [str, str, str, str] } ], 'detective_comment': str }. "
        "- questions: EXACTLY 5 items (no more, no less). "
        "- question: concise, specific, third-person phrasing. "
        "- choices: exactly 4 options - 3 specific choices PLUS 'None of the above' as the 4th option. "
        "- detective_comment: one or two sentences explaining your reasoning."
    )


def get_followup_prompt() -> str:
    """
    Build the prompt for follow-up questions.
    This is used when message history already exists.
    """
    return (
        "Based on the previous conversation, ask 3 DEEPER, more specific follow-up questions. "
        "Pay special attention to any 'None of the above' answers - these indicate areas where you need to ask alternative questions to gather better information. "
        "NEVER repeat or ask similar questions to what was already asked. "
        "Be witty, clever, but clear. "
        "Return JSON that strictly matches this schema: "
        "{ 'questions': [ { 'question': str, 'choices': [str, str, str, str] } ], 'detective_comment': str }. "
        "- questions: EXACTLY 3 items (no more, no less). "
        "- choices: exactly 4 options - 3 specific choices PLUS 'None of the above' as the 4th option."
    )
