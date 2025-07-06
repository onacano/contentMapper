import firebase_admin
from firebase_admin import credentials, auth
from fastapi import HTTPException, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import os
from typing import Optional

# Firebase Admin SDK の初期化
if not firebase_admin._apps:
    # 開発環境用の設定（本番では適切なサービスアカウントキーを使用）
    try:
        # テスト用の初期化（実際のFirebaseプロジェクトIDに置き換えてください）
        cred = credentials.Certificate({
            "type": "service_account",
            "project_id": "demo-project-id",
            "private_key_id": "demo-key-id",
            "private_key": "-----BEGIN PRIVATE KEY-----\nMIIEvgIBADANBgkqhkiG9w0BAQEFAASCBKgwggSkAgEAAoIBAQC7VJTUt9Us8cKB\nXEp+OLUDQYpU5TQWwTKbOdSCzZuaKpHT8FWyaVOsR2Rm7JJoHWK7qGMkZoOIQpHY\nyXgWJOJr6jGvT9AhYx6hJ9wXJtZBJOGPv/bF3F0pQgXhw7vqkQwXoQGzKZOqgHYd\n9BF9vIBgFZF5qW2mX9ZFa0YtZKHq2l3mI7KNOdR8R0FjcmZI7/8OGz8fGNxUYjYz\n...(demo key)...\n-----END PRIVATE KEY-----\n",
            "client_email": "demo@demo-project-id.iam.gserviceaccount.com",
            "client_id": "demo-client-id",
            "auth_uri": "https://accounts.google.com/o/oauth2/auth",
            "token_uri": "https://oauth2.googleapis.com/token"
        })
        firebase_admin.initialize_app(cred)
        print("Firebase Admin initialized with demo credentials")
    except Exception as e:
        print(f"Warning: Firebase Admin initialization failed: {e}")
        print("Running without Firebase authentication")

security = HTTPBearer(auto_error=False)

# 許可されたユーザーのリスト（実際の運用では環境変数やDBで管理）
ALLOWED_USERS = [
    "yuco@example.com",
    "admin@onacano.com",
    "dev@example.com"  # 開発環境用ユーザー
]

async def verify_firebase_token(credentials: Optional[HTTPAuthorizationCredentials] = Depends(security)):
    """
    Firebase IDトークンを検証し、認証されたユーザー情報を返す
    開発環境では認証をスキップ
    """
    # 開発環境での認証スキップ
    if os.getenv("ENVIRONMENT") == "development":
        return {"email": "dev@example.com", "name": "Development User", "uid": "dev-uid"}
    
    if not credentials:
        return None
    
    # 開発用トークンのチェック
    if credentials.credentials == "dev-token":
        return {"email": "dev@example.com", "name": "Development User", "uid": "dev-uid"}
    
    try:
        # Firebaseトークンの検証
        decoded_token = auth.verify_id_token(credentials.credentials)
        user_email = decoded_token.get('email')
        
        # 許可されたユーザーかチェック
        if user_email not in ALLOWED_USERS:
            raise HTTPException(
                status_code=403, 
                detail=f"Access denied for user: {user_email}"
            )
        
        return decoded_token
    except Exception as e:
        print(f"Token verification failed: {e}")
        raise HTTPException(
            status_code=401, 
            detail="Invalid authentication token"
        )

async def require_auth(user = Depends(verify_firebase_token)):
    """
    認証が必須のエンドポイント用の依存関数
    開発環境では常に認証済みとして扱う
    """
    if os.getenv("ENVIRONMENT") == "development":
        return {"email": "dev@example.com", "name": "Development User", "uid": "dev-uid"}
    
    if not user:
        raise HTTPException(
            status_code=401, 
            detail="Authentication required"
        )
    
    # 許可されたユーザーかチェック
    if user.get("email") not in ALLOWED_USERS:
        raise HTTPException(status_code=403, detail="Access denied")
    
    return user

async def optional_auth(user = Depends(verify_firebase_token)):
    """
    認証がオプションのエンドポイント用の依存関数
    開発環境では常に認証済みとして扱う
    """
    if os.getenv("ENVIRONMENT") == "development":
        return {"email": "dev@example.com", "name": "Development User", "uid": "dev-uid"}
    
    return user
