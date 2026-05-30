from pydantic_settings import BaseSettings, SettingsConfigDict
import os

class Settings(BaseSettings):
    my_val: str = "default"

    model_config = SettingsConfigDict(env_file=".env.test.dummy", extra="ignore")

def run():
    print(Settings(_env_file=".env.test.dummy2").my_val)

if __name__ == "__main__":
    with open(".env.test.dummy2", "w") as f:
        f.write("my_val=from_dummy2")
    run()
