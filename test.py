import sqlite3

# Connect to the SQLite database
db_name = 'test.sqlite'
conn = sqlite3.connect(db_name)
cursor = conn.cursor()

# Create the table 'test' with three columns of boolean data type
table_name = 'test'
column_names = ['column1', 'column2', 'column3']

# Build the CREATE TABLE SQL query
create_table_query = f"CREATE TABLE IF NOT EXISTS {table_name} (id INTEGER PRIMARY KEY, {', '.join([f'{column} BOOLEAN' for column in column_names])});"

# Execute the query to create the table
cursor.execute(create_table_query)

# Commit the changes and close the connection
conn.commit()
conn.close()

print(f"Table '{table_name}' with boolean columns {', '.join(column_names)} created in '{db_name}' successfully!")
