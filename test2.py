import sqlite3

def create_table(conn):
    # Create the table 'test' with three columns of boolean data type
    table_name = 'test'
    column_names = ['column1', 'column2', 'column3']

    # Build the CREATE TABLE SQL query
    create_table_query = f"CREATE TABLE IF NOT EXISTS {table_name} (id INTEGER PRIMARY KEY, {', '.join([f'{column} BOOLEAN' for column in column_names])});"

    # Execute the query to create the table
    conn.execute(create_table_query)

def get_boolean_input(prompt):
    while True:
        user_input = input(prompt)
        if user_input.lower() in ['true', 'false']:
            return user_input.lower() == 'true'
        elif user_input.lower() == 'quit':
            return None
        else:
            print("Invalid input. Please enter 'true', 'false', or 'quit'.")

def main():
    db_name = 'test.sqlite'
    conn = sqlite3.connect(db_name)
    cursor = conn.cursor()

    create_table(conn)

    try:
        while True:
            data = []
            for column_name in ['column1', 'column2', 'column3']:
                user_input = get_boolean_input(f"Enter a boolean value for {column_name} (true/false) or type 'quit' to exit: ")
                if user_input is None:
                    print("Exiting data entry.")
                    break
                data.append(user_input)

            if user_input is None:
                break

            # Insert data into the 'test' table
            insert_query = f"INSERT INTO test (column1, column2, column3) VALUES (?, ?, ?);"
            cursor.execute(insert_query, data)
            conn.commit()

            print("Data inserted successfully!")

    finally:
        conn.close()

if __name__ == "__main__":
    main()
