import os
from supabase import create_client, Client
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Get Supabase credentials from environment variables
supabase_url = os.getenv("SUPABASE_URL")
supabase_key = os.getenv("SUPABASE_KEY")

# Initialize Supabase client
assert supabase_url is not None, "SUPABASE_URL environment variable is not set"
assert supabase_key is not None, "SUPABASE_KEY environment variable is not set"
supabase: Client = create_client(supabase_url, supabase_key)


def fetch_users():
    try:
        # Query the users table
        response = supabase.table("users").select("*").execute()

        # Extract data from response
        users = response.data

        if users:
            print("Users found:")
            for user in users:
                print(user)
        else:
            print("No users found in the table.")

    except Exception as e:
        print(f"Error fetching users: {str(e)}")


if __name__ == "__main__":
    fetch_users()
