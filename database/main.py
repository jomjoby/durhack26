from database.connection import get_connection


def main():

    try:
        with get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT version();")
                result = cur.fetchone()

                print("Successfully connected to Tiger Cloud!")
                print(result[0])

    except Exception as error:
        print("Database connection failed:")
        print(error)


if __name__ == "__main__":
    main()