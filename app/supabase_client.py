import os
from dotenv import load_dotenv
from supabase import create_client,Client

load_dotenv()

SUPABASE_URL=os.getenv("SUPABASE_URL")
SUPABASE_ANON_KEY=os.getenv("SUPABASE_ANON_KEY")
SUPABASE_SERVICE_KEY=os.getenv("SUPABASE_SERVICE_KEY")

supabase: Client=create_client(SUPABASE_URL,SUPABASE_ANON_KEY)

supabase_admin=create_client(SUPABASE_URL,SUPABASE_SERVICE_KEY)