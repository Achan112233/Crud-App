"""
Test Azure AD connection
"""
import os
from dotenv import load_dotenv
import sys

load_dotenv()

AZURE_TENANT_ID = os.getenv("AZURE_TENANT_ID")
AZURE_CLIENT_ID = os.getenv("AZURE_CLIENT_ID")
AZURE_CLIENT_SECRET = os.getenv("AZURE_CLIENT_SECRET")

print("=" * 60)
print("Azure AD Configuration Test")
print("=" * 60)
print(f"Tenant ID: {AZURE_TENANT_ID}")
print(f"Client ID: {AZURE_CLIENT_ID}")
print(f"Client Secret: {AZURE_CLIENT_SECRET[:10]}...")
print()

if not all([AZURE_TENANT_ID, AZURE_CLIENT_ID, AZURE_CLIENT_SECRET]):
    print("❌ Missing Azure AD credentials")
    sys.exit(1)

print("Testing MSAL initialization...")
try:
    import msal
    
    authority = f"https://login.microsoftonline.com/{AZURE_TENANT_ID}"
    print(f"Authority URL: {authority}")
    print()
    
    app = msal.ConfidentialClientApplication(
        AZURE_CLIENT_ID,
        authority=authority,
        client_credential=AZURE_CLIENT_SECRET
    )
    
    print("✓ MSAL app created successfully!")
    print()
    
    # Try to get an access token
    print("Attempting to acquire token...")
    result = app.acquire_token_for_client(scopes=["https://graph.microsoft.com/.default"])
    
    if "access_token" in result:
        print("✓ Successfully acquired access token!")
        print(f"  Token type: {result.get('token_type')}")
        print(f"  Expires in: {result.get('expires_in')} seconds")
        print()
        print("✓✓✓ Azure AD is fully configured and working! ✓✓✓")
    else:
        print(f"❌ Failed to acquire token: {result.get('error_description')}")
        sys.exit(1)
        
except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
