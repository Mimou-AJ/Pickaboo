import enum

class AnswerChoice(str, enum.Enum):
    yes = "yes"
    probably = "probably"
    probably_not = "probably_not"
    no = "no"
