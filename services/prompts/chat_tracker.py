from services.context import get_context
from services.instructions import get_instructions_questions

QUESTIONS = get_instructions_questions()
QUESTIONS_COUNT = len(QUESTIONS)

async def get_chat_tracker(user_id: int):
    context = await get_context(user_id)
    if not context:
        return None
    prompt = f"""  
    Твоє завдання - проаналізувати діалог людини з ШІ ріелтором та проаналізувати чи були дані відповіді
    на основні {QUESTIONS_COUNT} запитань 
    мені потрібно проаналізувати чи діалог вдалося завершити 

    Питання які має задати ШІ ріелтор:
    {QUESTIONS}

    контекст чату:
    {context}

    ти маєш проаналізувати чи були дані відповіді на основні {QUESTIONS_COUNT} запитань
    якщо користувач відповідав що йому байдуже чи неважливо це значить що користувач відповів на це питання і воно зараховується

    ти маєш повернути лише True або False
    True - якщо були дані відповіді на основні {QUESTIONS_COUNT} запитань
    False - якщо не були дані відповіді на основні {QUESTIONS_COUNT} запитань
    """
    return prompt