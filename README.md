# Spectrum Promote GUI

A metadata-driven generic database editor built with Python/Flask. This application queries the information_schema using SQLAlchemy to dynamically generate forms for database editing.

## Features

- **Metadata-Driven**: Automatically discovers database schema using SQLAlchemy
- **Dynamic Forms**: Forms are generated dynamically based on table structure using Jinja2 templates
- **Modern UI**: Styled with Tailwind CSS (CDN) for a sleek, responsive interface
- **RESTful API**: 
  - `/metadata` - Returns JSON metadata of database fields
  - `/update` - Generic POST endpoint for updating records
- **Encryption Support**: Includes placeholder functions for data encryption/decryption

## Installation

1. Clone the repository:
```bash
git clone https://github.com/aaronnmajor/spectrum-promote-gui.git
cd spectrum-promote-gui
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

## Usage

1. Run the application:
```bash
python app.py
```

2. Open your browser and navigate to:
```
http://localhost:5000
```

## API Endpoints

### GET /metadata
Returns JSON metadata for a database table.

**Query Parameters:**
- `table` (optional): Table name (default: "users")

**Example:**
```bash
curl http://localhost:5000/metadata?table=users
```

**Response:**
```json
{
  "table": "users",
  "fields": [
    {
      "name": "id",
      "type": "INTEGER",
      "nullable": false,
      "default": null,
      "primary_key": true
    },
    ...
  ]
}
```

### POST /update
Generic endpoint to update database records.

**Request Body:**
```json
{
  "table": "users",
  "id": 1,
  "fields": {
    "username": "new_username",
    "email": "new@example.com"
  }
}
```

**Response:**
```json
{
  "success": true,
  "message": "Record 1 updated successfully",
  "rows_affected": 1
}
```

## Database Configuration

By default, the application uses SQLite with a sample database. To use a different database, set the `DATABASE_URL` environment variable:

```bash
export DATABASE_URL="postgresql://user:password@localhost/dbname"
# or
export DATABASE_URL="mysql://user:password@localhost/dbname"
```

## Encryption Functions

The application includes placeholder encryption functions in `crypto_utils.py`:

- `encrypt(data)` - Placeholder for encrypting data
- `decrypt(data)` - Placeholder for decrypting data

These should be implemented with actual encryption logic (e.g., using the `cryptography` library) for production use.

## Project Structure

```
spectrum-promote-gui/
├── app.py                 # Main Flask application
├── crypto_utils.py        # Encryption/decryption utilities
├── requirements.txt       # Python dependencies
├── templates/
│   ├── index.html        # Main editor interface
│   └── error.html        # Error page
└── sample_database.db    # SQLite database (auto-generated)
```

## Technologies Used

- **Flask** - Web framework
- **SQLAlchemy** - Database ORM and schema inspection
- **Jinja2** - Template engine
- **Tailwind CSS** - UI styling (via CDN)

## License

MIT License