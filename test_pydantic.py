import sys
try:
    from pydantic_settings import BaseSettings, SettingsConfigDict
except ImportError:
    print("pydantic_settings not installed")
    sys.exit(1)

class MySettings(BaseSettings):
    my_var: str = "default"
    model_config = SettingsConfigDict(env_file=".env.test", extra="ignore")

s = MySettings(_env_file=".env.other")
print(f"my_var={s.my_var}")
