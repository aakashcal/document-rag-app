import openai
from app.config import settings

print("Testing OpenAI API connection...")
try:
    client = openai.OpenAI(api_key=settings.OPENAI_API_KEY)
    models = client.models.list()
    print(f"OpenAI API connection successful. Found {len(models.data)} models.")
except Exception as e:
    print(f"OpenAI API error: {str(e)}") 