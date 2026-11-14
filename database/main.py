from pathlib import Path
from database.connection import get_connection


def main():
    schema_path = Path(__file__).parent / "schema.sql"
    schema = schema_path.read_text()

    try:
        with get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(schema)

        print("Schema executed successfully!")

    except Exception as error:
        print("Database setup failed:")
        print(error)


if __name__ == "__main__":
    main()