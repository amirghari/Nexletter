# NeXletter

A news article collection and storage system using NewsData.io API and PostgreSQL.

## Setup

### Prerequisites
- Python 3.x
- PostgreSQL
- NewsData.io API key (get one at [newsdata.io](https://newsdata.io))

### Installation

1. Clone the repository:
```
git clone https://github.com/yourusername/NeXletter.git
cd NeXletter
```

2. Install required packages:
```
pip install psycopg2 requests python-dotenv
```

3. Set up environment variables:
   - Copy `.env.example` to a new file called `.env`
   - Fill in your actual credentials in the `.env` file

```
cp .env.example .env.
```

4. Edit the `.env` file with your actual credentials:
```
# NewsData.io API credentials
API_KEY=your_actual_api_key

# Database credentials
DB_HOST=localhost
DB_PORT=5432
DB_NAME=nexletter
DB_USER=your_actual_username
DB_PASSWORD=your_actual_password
```

5. Make sure PostgreSQL is running and create a database named `nexletter`.

### Running the Application

Run the script to fetch articles and store them in the database:
```
python db.py
```

## Security Note

This repository uses environment variables to store sensitive information like API keys and database credentials. The actual `.env` file containing these values is not committed to the repository for security reasons (it's listed in `.gitignore`).

When deploying to production, always use environment variables or a secure secrets management system instead of hardcoded credentials.
