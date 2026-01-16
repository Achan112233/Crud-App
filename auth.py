"""
Azure AD Authentication Module
Handles OAuth 2.0 flow and JWT token management
"""
import os
import jwt
import json
import requests
from datetime import datetime, timedelta
from functools import wraps
from flask import request, jsonify, session, redirect, url_for
from typing import Optional, Dict, Any
import msal

# JWT Configuration
JWT_SECRET = os.getenv("JWT_SECRET", "your-secret-key-change-this-in-production")
JWT_ALGORITHM = "HS256"
JWT_EXPIRATION_HOURS = int(os.getenv("JWT_EXPIRATION_HOURS", "24"))

# Azure AD Configuration
AZURE_TENANT_ID = os.getenv("AZURE_TENANT_ID")
AZURE_CLIENT_ID = os.getenv("AZURE_CLIENT_ID")
AZURE_CLIENT_SECRET = os.getenv("AZURE_CLIENT_SECRET")
AZURE_REDIRECT_URI = os.getenv("AZURE_REDIRECT_URI", "http://localhost:5000/auth/callback")
AUTHORITY = f"https://login.microsoftonline.com/{AZURE_TENANT_ID}/v2.0"


class TokenManager:
    """Manage JWT token creation and validation"""
    
    @staticmethod
    def create_access_token(user_id: str, user_email: str, user_name: str) -> str:
        """Create JWT access token"""
        payload = {
            "user_id": user_id,
            "email": user_email,
            "name": user_name,
            "iat": datetime.utcnow(),
            "exp": datetime.utcnow() + timedelta(hours=JWT_EXPIRATION_HOURS)
        }
        return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)
    
    @staticmethod
    def create_refresh_token(user_id: str) -> str:
        """Create JWT refresh token (longer expiration)"""
        payload = {
            "user_id": user_id,
            "type": "refresh",
            "iat": datetime.utcnow(),
            "exp": datetime.utcnow() + timedelta(days=30)
        }
        return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)
    
    @staticmethod
    def verify_token(token: str) -> Optional[Dict[str, Any]]:
        """Verify and decode JWT token"""
        try:
            payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
            return payload
        except jwt.ExpiredSignatureError:
            return None  # Token expired
        except jwt.InvalidTokenError:
            return None  # Invalid token
    
    @staticmethod
    def verify_refresh_token(token: str) -> Optional[Dict[str, Any]]:
        """Verify refresh token"""
        payload = TokenManager.verify_token(token)
        if payload and payload.get("type") == "refresh":
            return payload
        return None


class AzureADAuth:
    """Handle Azure AD OAuth 2.0 authentication"""
    
    def __init__(self):
        self.app = None
        self.msal_app = None
        self._initialize_msal()
    
    def _initialize_msal(self):
        """Initialize MSAL application"""
        if not all([AZURE_TENANT_ID, AZURE_CLIENT_ID, AZURE_CLIENT_SECRET]):
            print("Warning: Azure AD credentials not configured. Auth disabled.")
            return
        
        try:
            self.msal_app = msal.ConfidentialClientApplication(
                AZURE_CLIENT_ID,
                authority=AUTHORITY,
                client_credential=AZURE_CLIENT_SECRET
            )
        except Exception as e:
            print(f"Warning: Failed to initialize Azure AD: {e}")
            print("Auth disabled. You can still use the app locally with SQLite.")
    
    def get_auth_url(self) -> str:
        """Get Azure AD authorization URL"""
        if not self.msal_app:
            raise RuntimeError("Azure AD not configured")
        
        auth_url = self.msal_app.get_authorization_request_url(
            scopes=["https://graph.microsoft.com/.default"],
            redirect_uri=AZURE_REDIRECT_URI
        )
        return auth_url
    
    def get_token_by_code(self, code: str) -> Optional[Dict[str, Any]]:
        """Exchange authorization code for access token"""
        if not self.msal_app:
            raise RuntimeError("Azure AD not configured")
        
        result = self.msal_app.acquire_token_by_authorization_code(
            code,
            scopes=["https://graph.microsoft.com/.default"],
            redirect_uri=AZURE_REDIRECT_URI
        )
        return result if "access_token" in result else None
    
    @staticmethod
    def get_user_info(access_token: str) -> Optional[Dict[str, str]]:
        """Fetch user info from Microsoft Graph"""
        headers = {"Authorization": f"Bearer {access_token}"}
        response = requests.get(
            "https://graph.microsoft.com/v1.0/me",
            headers=headers
        )
        
        if response.status_code == 200:
            data = response.json()
            return {
                "id": data.get("id"),
                "email": data.get("userPrincipalName") or data.get("mail"),
                "name": data.get("displayName"),
            }
        return None


# Token Manager instance
token_mgr = TokenManager()
azure_auth = AzureADAuth()


def token_required(f):
    """Decorator to protect routes with JWT token validation"""
    @wraps(f)
    def decorated(*args, **kwargs):
        token = None
        
        # Check for token in Authorization header
        if "Authorization" in request.headers:
            auth_header = request.headers["Authorization"]
            try:
                token = auth_header.split(" ")[1]
            except IndexError:
                return jsonify({"error": "Invalid authorization header"}), 401
        
        if not token:
            return jsonify({"error": "Missing authorization token"}), 401
        
        # Verify token
        payload = token_mgr.verify_token(token)
        if not payload:
            return jsonify({"error": "Invalid or expired token"}), 401
        
        # Attach user info to request context
        request.user = payload
        return f(*args, **kwargs)
    
    return decorated


def optional_token(f):
    """Decorator for optional JWT authentication"""
    @wraps(f)
    def decorated(*args, **kwargs):
        token = None
        
        if "Authorization" in request.headers:
            auth_header = request.headers["Authorization"]
            try:
                token = auth_header.split(" ")[1]
                payload = token_mgr.verify_token(token)
                if payload:
                    request.user = payload
            except (IndexError, jwt.InvalidTokenError):
                pass
        
        request.user = getattr(request, "user", None)
        return f(*args, **kwargs)
    
    return decorated
