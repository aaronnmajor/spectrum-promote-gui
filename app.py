"""
Flask application for metadata-driven generic database editor.
Queries information_schema using SQLAlchemy to get column names and types.
Renders forms dynamically using Jinja2 templates with Tailwind CSS styling.
"""

from flask import Flask, render_template, request, jsonify
from sqlalchemy import create_engine, text, inspect, MetaData, Table
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
    # Validate table name exists to prevent SQL injection
    inspector = inspect(engine)
    if table_name not in inspector.get_table_names():
        return []
    
    # Use SQLAlchemy Table object for safe query construction
    metadata = MetaData()
    table = Table(table_name, metadata, autoload_with=engine)
    
    with engine.connect() as conn:
        from sqlalchemy import select
        result = conn.execute(select(table))
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
        
        # Get primary key column name
        inspector = inspect(engine)
        pk_columns = inspector.get_pk_constraint('users')
        primary_key = pk_columns['constrained_columns'][0] if pk_columns['constrained_columns'] else 'id'
        
        return render_template('index.html', metadata=metadata, data=data, table_name='users', primary_key=primary_key)
    except Exception:
        # Don't expose internal error details to users
        return render_template('error.html', error='An error occurred while loading the page'), 500


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
    except Exception:
        # Don't expose internal error details to users
        return jsonify({
            'error': 'Failed to retrieve metadata'
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
        
        # Validate table name exists to prevent SQL injection
        inspector = inspect(engine)
        if table_name not in inspector.get_table_names():
            return jsonify({'error': 'Table does not exist'}), 400
        
        # Get primary key column name from metadata
        columns = inspector.get_columns(table_name)
        pk_columns = inspector.get_pk_constraint(table_name)
        primary_key_name = pk_columns['constrained_columns'][0] if pk_columns['constrained_columns'] else 'id'
        
        # Validate that all field names exist in the table
        valid_columns = {col['name'] for col in columns}
        for field_name in fields.keys():
            if field_name not in valid_columns:
                return jsonify({'error': 'Invalid column name'}), 400
        
        # Use SQLAlchemy Table object for safe query construction
        metadata = MetaData()
        table = Table(table_name, metadata, autoload_with=engine)
        
        # Build UPDATE statement using SQLAlchemy
        from sqlalchemy import update
        stmt = update(table)
        
        # Set WHERE clause using primary key
        stmt = stmt.where(table.c[primary_key_name] == record_id)
        
        # Set values for columns
        stmt = stmt.values(**fields)
        
        with engine.connect() as conn:
            result = conn.execute(stmt)
            conn.commit()
            
            if result.rowcount == 0:
                return jsonify({'error': 'Record not found'}), 404
            
            return jsonify({
                'success': True,
                'message': f'Record {record_id} updated successfully',
                'rows_affected': result.rowcount
            })
    
    except SQLAlchemyError:
        # Don't expose internal database error details to users
        return jsonify({
            'error': 'Database operation failed'
        }), 500
    except Exception:
        # Don't expose internal error details to users
        return jsonify({
            'error': 'Update operation failed'
        }), 500


if __name__ == '__main__':
    # Initialize sample database
    init_sample_database()
    
    # Run the Flask app
    # Note: debug=True should only be used in development
    # In production, use a WSGI server like gunicorn and set debug=False
    debug_mode = os.environ.get('FLASK_DEBUG', 'False').lower() == 'true'
    app.run(debug=debug_mode, host='0.0.0.0', port=5000)
