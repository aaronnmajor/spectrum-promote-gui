"""
Flask application for metadata-driven generic database editor.
Queries information_schema using SQLAlchemy to get column names and types.
Renders forms dynamically using Jinja2 templates with Tailwind CSS styling.
"""

from flask import Flask, render_template, request, jsonify
from sqlalchemy import create_engine, text, inspect
from sqlalchemy.exc import SQLAlchemyError
import os
from crypto_utils import encrypt, decrypt

app = Flask(__name__)

# Database configuration
# Using SQLite for simplicity - can be changed to any database
DATABASE_URL = os.environ.get('DATABASE_URL', 'sqlite:///sample_database.db')
engine = create_engine(DATABASE_URL)


def init_sample_database():
    """Initialize a sample database with a users table for demonstration."""
    with engine.connect() as conn:
        # Create sample table if it doesn't exist
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT NOT NULL,
                email TEXT NOT NULL,
                age INTEGER,
                active BOOLEAN DEFAULT 1
            )
        """))
        conn.commit()
        
        # Insert sample data if table is empty
        result = conn.execute(text("SELECT COUNT(*) FROM users"))
        count = result.scalar()
        if count == 0:
            conn.execute(text("""
                INSERT INTO users (username, email, age, active)
                VALUES 
                    ('john_doe', 'john@example.com', 30, 1),
                    ('jane_smith', 'jane@example.com', 25, 1),
                    ('bob_wilson', 'bob@example.com', 35, 0)
            """))
            conn.commit()


def get_table_metadata(table_name='users'):
    """
    Query information_schema to get column names and types for a table.
    
    Args:
        table_name: Name of the table to get metadata for
        
    Returns:
        List of dictionaries containing column information
    """
    inspector = inspect(engine)
    
    if table_name not in inspector.get_table_names():
        return []
    
    columns = inspector.get_columns(table_name)
    metadata = []
    
    for column in columns:
        column_info = {
            'name': column['name'],
            'type': str(column['type']),
            'nullable': column['nullable'],
            'default': column['default'],
            'primary_key': column.get('primary_key', False)
        }
        metadata.append(column_info)
    
    return metadata


def get_table_data(table_name='users'):
    """
    Retrieve all data from the specified table.
    
    Args:
        table_name: Name of the table to retrieve data from
        
    Returns:
        List of dictionaries containing row data
    """
    with engine.connect() as conn:
        result = conn.execute(text(f"SELECT * FROM {table_name}"))
        columns = result.keys()
        rows = []
        for row in result:
            row_dict = {}
            for i, col in enumerate(columns):
                row_dict[col] = row[i]
            rows.append(row_dict)
        return rows


@app.route('/')
def index():
    """Render the main page with the database editor."""
    try:
        metadata = get_table_metadata('users')
        data = get_table_data('users')
        return render_template('index.html', metadata=metadata, data=data, table_name='users')
    except Exception as e:
        return render_template('error.html', error=str(e)), 500


@app.route('/metadata')
def metadata_endpoint():
    """
    Return JSON metadata of database fields.
    Endpoint: /metadata?table=<table_name>
    """
    table_name = request.args.get('table', 'users')
    
    try:
        metadata = get_table_metadata(table_name)
        return jsonify({
            'table': table_name,
            'fields': metadata
        })
    except Exception as e:
        return jsonify({
            'error': str(e)
        }), 500


@app.route('/update', methods=['POST'])
def update_endpoint():
    """
    Generic POST endpoint to update database records.
    Expects JSON payload with table, id, and fields to update.
    """
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({'error': 'No data provided'}), 400
        
        table_name = data.get('table', 'users')
        record_id = data.get('id')
        fields = data.get('fields', {})
        
        if not record_id:
            return jsonify({'error': 'No record ID provided'}), 400
        
        if not fields:
            return jsonify({'error': 'No fields to update'}), 400
        
        # Build UPDATE query dynamically
        set_clause = ', '.join([f"{key} = :{key}" for key in fields.keys()])
        query = text(f"UPDATE {table_name} SET {set_clause} WHERE id = :id")
        
        # Add id to parameters
        params = {**fields, 'id': record_id}
        
        with engine.connect() as conn:
            result = conn.execute(query, params)
            conn.commit()
            
            if result.rowcount == 0:
                return jsonify({'error': 'Record not found'}), 404
            
            return jsonify({
                'success': True,
                'message': f'Record {record_id} updated successfully',
                'rows_affected': result.rowcount
            })
    
    except SQLAlchemyError as e:
        return jsonify({
            'error': f'Database error: {str(e)}'
        }), 500
    except Exception as e:
        return jsonify({
            'error': str(e)
        }), 500


if __name__ == '__main__':
    # Initialize sample database
    init_sample_database()
    
    # Run the Flask app
    app.run(debug=True, host='0.0.0.0', port=5000)
