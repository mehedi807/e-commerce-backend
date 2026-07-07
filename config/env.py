import environ
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent

env = environ.Env(interpolate=True)
environ.Env.read_env(BASE_DIR / '.env')
