import google.generativeai as genai
from dotenv import load_dotenv
import os


load_dotenv()


async def gemini_request(prompt):
    genai.configure(api_key=os.getenv("GEMINI_API_KEY"))

    model = genai.GenerativeModel(
        model_name="gemini-2.5-flash",
        generation_config={
            "temperature": 0.3,
            "top_p": 0.8,
            "top_k": 40,
            "max_output_tokens": 600000
        },
    )
    try:
        response = model.generate_content(prompt)
        return response.text
    except Exception as e:
        print(f"Помилка аналізу: {e}")
        return "Помилка аналізу"