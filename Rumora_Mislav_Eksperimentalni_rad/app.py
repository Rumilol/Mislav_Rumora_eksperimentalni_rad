from flask import Flask, jsonify
import sqlite3
import timeit
from faker import Faker
import datetime

app = Flask(__name__)

# Function to create a SQLite connection and cursor
def create_connection():
    conn = sqlite3.connect(":memory:")
    cursor = conn.cursor()
    return conn, cursor

# Function to create a table and populate it with random data using Faker
def create_and_populate_table(cursor, table_name, num_rows):
    cursor.execute(f"CREATE TABLE {table_name} (id INTEGER PRIMARY KEY AUTOINCREMENT, key TEXT, value INTEGER, timestamp TEXT)")
    fake = Faker()
    data = [(fake.word(), fake.random_int(1, 100), fake.date_time_this_decade()) for _ in range(num_rows)]
    cursor.executemany(f"INSERT INTO {table_name} (key, value, timestamp) VALUES (?,?,?)", data)

# Function to create a materialized view (data cube)
def create_materialized_view(cursor, materialized_view_name, facts_table_name):
    cursor.execute(f"CREATE TABLE {materialized_view_name} AS "
                   f"SELECT key, SUM(value) AS total_value, MAX(timestamp) AS last_timestamp FROM {facts_table_name} GROUP BY key")

# Function to simulate OLAP query from materialized view
def olap_query_materialized_view(cursor, materialized_view_name, key):
    start_time = timeit.default_timer()
    cursor.execute(f"SELECT key, total_value, last_timestamp "
                   f"FROM {materialized_view_name} "
                   f"WHERE key = ? ", (key,))
    result = cursor.fetchall()
    end_time = timeit.default_timer()
    return result, end_time - start_time

# Function to simulate OLAP query from facts table
def olap_query_facts_table(cursor, facts_table_name, key):
    start_time = timeit.default_timer()
    cursor.execute(f"SELECT key, SUM(value) AS total_value, MAX(timestamp) AS last_timestamp "
                   f"FROM {facts_table_name} "
                   f"WHERE key = ? GROUP BY key", (key,))
    result = cursor.fetchall()
    end_time = timeit.default_timer()
    return result, end_time - start_time

# Function to run the benchmark with configurable parameters
def run_benchmark(num_runs, num_rows, key):
    total_time_mv = 0
    total_time_ft = 0
    total_requests = 0

    for _ in range(num_runs):
        conn, cursor = create_connection()

        # Create and populate facts table
        create_and_populate_table(cursor, "facts_table", num_rows)

        # Create materialized view (data cube)
        create_materialized_view(cursor, "materialized_view", "facts_table")

        # Query from materialized view
        _, time_mv = olap_query_materialized_view(cursor, "materialized_view", key)
        total_time_mv += time_mv

        # Query from facts table
        _, time_ft = olap_query_facts_table(cursor, "facts_table", key)
        total_time_ft += time_ft

        conn.close()
        total_requests += 1

    avg_time_mv = total_time_mv / num_runs
    avg_time_ft = total_time_ft / num_runs
    throughput = total_requests / (total_time_mv + total_time_ft)

    return avg_time_mv, avg_time_ft, throughput

# Create Flask route outside of the run_benchmark function
@app.route('/query')
def query():
    num_runs = 5  # Number of benchmark runs
    num_rows = 10000
    key = Faker().word()

    avg_time_mv, avg_time_ft, throughput = run_benchmark(num_runs, num_rows, key)

    return jsonify({
        'Key': key,
        'Materialized View Avg. Time': avg_time_mv,
        'Facts Table Avg. Time': avg_time_ft,
        'Throughput (RPS)': throughput
    })


if __name__ == "__main__":
    app.run(debug=False)