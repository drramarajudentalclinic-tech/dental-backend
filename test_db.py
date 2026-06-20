import os
from dotenv import load_dotenv

load_dotenv()

print("DATABASE_URL:")
print(os.getenv("DATABASE_URL"))