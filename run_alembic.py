import os
import sys

# Set DATABASE_URL to localhost so we can run alembic locally without docker network
os.environ["DATABASE_URL"] = "postgresql+psycopg://marketintel:marketintel_password@localhost:5432/marketintel"

# Run alembic
from alembic.config import CommandLine
CommandLine().main(argv=["revision", "--autogenerate", "-m", "create fundamentals and dcf tables"])
