# imports
from flask import Flask, render_template, redirect, request, jsonify, session, url_for
from flask_scss import Scss
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
from azure.storage.blob import BlobServiceClient
import os
from dotenv import load_dotenv
from auth import token_mgr, azure_auth, token_required, optional_token
import uuid

# load environment variables
load_dotenv()

# flask config
app = Flask(__name__)
app.secret_key = os.getenv("FLASK_SECRET_KEY", "dev-secret-key-change-in-production")
Scss(app)

# Azure SQL Database config (or use SQLite for local development)
USE_AZURE = os.getenv("USE_AZURE", "False") == "True"

if USE_AZURE:
    # Azure SQL Database connection string
    server = os.getenv("AZURE_SQL_SERVER")
    database = os.getenv("AZURE_SQL_DATABASE")
    username = os.getenv("AZURE_SQL_USERNAME")
    password = os.getenv("AZURE_SQL_PASSWORD")
    app.config["SQLALCHEMY_DATABASE_URI"] = f"mssql+pyodbc://{username}:{password}@{server}:1433/{database}?driver=ODBC+Driver+17+for+SQL+Server"
else:
    # Local SQLite database
    app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///database.db"

db = SQLAlchemy(app)

# Azure Storage Blob client (optional)
AZURE_STORAGE_CONNECTION_STRING = os.getenv("AZURE_STORAGE_CONNECTION_STRING")
if AZURE_STORAGE_CONNECTION_STRING:
    blob_service_client = BlobServiceClient.from_connection_string(AZURE_STORAGE_CONNECTION_STRING)
    container_name = os.getenv("AZURE_CONTAINER_NAME", "tasks")
else:
    blob_service_client = None


# ==================== Database Models ====================

class User(db.Model):
    """User model for storing authenticated users"""
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    azure_id = db.Column(db.String(255), unique=True, nullable=False)
    email = db.Column(db.String(255), unique=True, nullable=False)
    name = db.Column(db.String(255), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    last_login = db.Column(db.DateTime, default=datetime.utcnow)
    tasks = db.relationship("Task", backref="owner", lazy=True, cascade="all, delete-orphan")

    def to_dict(self):
        return {
            "id": self.id,
            "email": self.email,
            "name": self.name,
            "created_at": self.created_at.isoformat(),
            "last_login": self.last_login.isoformat(),
        }

    def __repr__(self):
        return f"User {self.email}"


class Task(db.Model):
    """Enhanced Task model with user association and status tracking"""
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = db.Column(db.String(36), db.ForeignKey("user.id"), nullable=False)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text, nullable=True)
    status = db.Column(db.String(20), default="pending", nullable=False)  # pending, in_progress, completed
    priority = db.Column(db.String(20), default="medium", nullable=False)  # low, medium, high
    due_date = db.Column(db.DateTime, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    completed_at = db.Column(db.DateTime, nullable=True)

    def to_dict(self):
        return {
            "id": self.id,
            "title": self.title,
            "description": self.description,
            "status": self.status,
            "priority": self.priority,
            "due_date": self.due_date.isoformat() if self.due_date else None,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
        }

    def __repr__(self):
        return f"Task {self.id}: {self.title}"


# ==================== Authentication Routes ====================

@app.route("/auth/login")
def login():
    """Redirect to Azure AD login"""
    try:
        auth_url = azure_auth.get_auth_url()
        return redirect(auth_url)
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/auth/callback")
def auth_callback():
    """Handle Azure AD callback"""
    code = request.args.get("code")
    error = request.args.get("error")

    if error:
        return jsonify({"error": error}), 400

    if not code:
        return jsonify({"error": "No authorization code"}), 400

    try:
        # Exchange code for token
        token_result = azure_auth.get_token_by_code(code)
        if not token_result:
            return jsonify({"error": "Failed to obtain access token"}), 400

        # Get user info from Microsoft Graph
        user_info = azure_auth.get_user_info(token_result["access_token"])
        if not user_info:
            return jsonify({"error": "Failed to retrieve user info"}), 400

        # Find or create user in database
        user = User.query.filter_by(azure_id=user_info["id"]).first()
        if not user:
            user = User(
                azure_id=user_info["id"],
                email=user_info["email"],
                name=user_info["name"],
            )
            db.session.add(user)
        
        user.last_login = datetime.utcnow()
        db.session.commit()

        # Create JWT tokens
        access_token = token_mgr.create_access_token(user.id, user.email, user.name)
        refresh_token = token_mgr.create_refresh_token(user.id)

        # Store tokens in session
        session["access_token"] = access_token
        session["refresh_token"] = refresh_token
        session["user_id"] = user.id
        session["user_email"] = user.email
        session["user_name"] = user.name

        # Redirect to dashboard
        return redirect(url_for("dashboard"))

    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/auth/logout")
def logout():
    """Logout user"""
    session.clear()
    return redirect(url_for("index"))


@app.route("/auth/refresh", methods=["POST"])
def refresh_token():
    """Refresh access token using refresh token"""
    data = request.get_json()
    refresh_token = data.get("refresh_token")

    if not refresh_token:
        return jsonify({"error": "Missing refresh token"}), 400

    payload = token_mgr.verify_refresh_token(refresh_token)
    if not payload:
        return jsonify({"error": "Invalid refresh token"}), 401

    user = User.query.get(payload["user_id"])
    if not user:
        return jsonify({"error": "User not found"}), 404

    new_access_token = token_mgr.create_access_token(user.id, user.email, user.name)
    return jsonify({"access_token": new_access_token}), 200


# ==================== Web Routes ====================

@app.route("/")
def index():
    """Landing page"""
    if "user_id" in session:
        return redirect(url_for("dashboard"))
    return render_template("index.html")


@app.route("/dashboard")
def dashboard():
    """User dashboard - requires authentication"""
    if "user_id" not in session:
        return redirect(url_for("login"))
    
    user_id = session["user_id"]
    tasks = Task.query.filter_by(user_id=user_id).order_by(Task.created_at.desc()).all()
    
    return render_template("dashboard.html", 
                         tasks=tasks, 
                         user_name=session.get("user_name"),
                         user_email=session.get("user_email"))


# ==================== REST API Endpoints ====================

@app.route("/api/tasks", methods=["GET"])
@token_required
def get_tasks():
    """Get all tasks for authenticated user"""
    user_id = request.user["user_id"]
    status = request.args.get("status")
    priority = request.args.get("priority")

    query = Task.query.filter_by(user_id=user_id)

    if status:
        query = query.filter_by(status=status)
    if priority:
        query = query.filter_by(priority=priority)

    tasks = query.order_by(Task.created_at.desc()).all()
    return jsonify([task.to_dict() for task in tasks]), 200


@app.route("/api/tasks/<task_id>", methods=["GET"])
@token_required
def get_task(task_id):
    """Get specific task"""
    user_id = request.user["user_id"]
    task = Task.query.filter_by(id=task_id, user_id=user_id).first_or_404()
    return jsonify(task.to_dict()), 200


@app.route("/api/tasks", methods=["POST"])
@token_required
def create_task():
    """Create new task"""
    user_id = request.user["user_id"]
    data = request.get_json()

    if not data or not data.get("title"):
        return jsonify({"error": "Title is required"}), 400

    task = Task(
        user_id=user_id,
        title=data.get("title"),
        description=data.get("description"),
        priority=data.get("priority", "medium"),
        due_date=datetime.fromisoformat(data["due_date"]) if data.get("due_date") else None,
    )

    db.session.add(task)
    db.session.commit()

    return jsonify(task.to_dict()), 201


@app.route("/api/tasks/<task_id>", methods=["PUT"])
@token_required
def update_task(task_id):
    """Update task"""
    user_id = request.user["user_id"]
    task = Task.query.filter_by(id=task_id, user_id=user_id).first_or_404()
    data = request.get_json()

    if "title" in data:
        task.title = data["title"]
    if "description" in data:
        task.description = data["description"]
    if "status" in data:
        task.status = data["status"]
        if data["status"] == "completed" and not task.completed_at:
            task.completed_at = datetime.utcnow()
    if "priority" in data:
        task.priority = data["priority"]
    if "due_date" in data:
        task.due_date = datetime.fromisoformat(data["due_date"]) if data["due_date"] else None

    task.updated_at = datetime.utcnow()
    db.session.commit()

    return jsonify(task.to_dict()), 200


@app.route("/api/tasks/<task_id>", methods=["DELETE"])
@token_required
def delete_task(task_id):
    """Delete task"""
    user_id = request.user["user_id"]
    task = Task.query.filter_by(id=task_id, user_id=user_id).first_or_404()

    db.session.delete(task)
    db.session.commit()

    return "", 204


@app.route("/api/tasks/<task_id>/status", methods=["PATCH"])
@token_required
def update_task_status(task_id):
    """Update task status"""
    user_id = request.user["user_id"]
    task = Task.query.filter_by(id=task_id, user_id=user_id).first_or_404()
    data = request.get_json()

    new_status = data.get("status")
    if new_status not in ["pending", "in_progress", "completed"]:
        return jsonify({"error": "Invalid status"}), 400

    task.status = new_status
    if new_status == "completed" and not task.completed_at:
        task.completed_at = datetime.utcnow()
    elif new_status != "completed":
        task.completed_at = None

    task.updated_at = datetime.utcnow()
    db.session.commit()

    return jsonify(task.to_dict()), 200


@app.route("/api/user/profile", methods=["GET"])
@token_required
def get_user_profile():
    """Get current user profile"""
    user = User.query.get(request.user["user_id"])
    if not user:
        return jsonify({"error": "User not found"}), 404
    return jsonify(user.to_dict()), 200


@app.route("/api/stats", methods=["GET"])
@token_required
def get_stats():
    """Get user task statistics"""
    user_id = request.user["user_id"]
    tasks = Task.query.filter_by(user_id=user_id).all()

    stats = {
        "total_tasks": len(tasks),
        "completed_tasks": len([t for t in tasks if t.status == "completed"]),
        "pending_tasks": len([t for t in tasks if t.status == "pending"]),
        "in_progress_tasks": len([t for t in tasks if t.status == "in_progress"]),
        "high_priority_tasks": len([t for t in tasks if t.priority == "high"]),
    }

    return jsonify(stats), 200


# ==================== Error Handlers ====================

@app.errorhandler(404)
def not_found(error):
    """404 error handler"""
    if request.path.startswith("/api/"):
        return jsonify({"error": "Not found"}), 404
    return render_template("404.html"), 404


@app.errorhandler(500)
def server_error(error):
    """500 error handler"""
    if request.path.startswith("/api/"):
        return jsonify({"error": "Internal server error"}), 500
    return render_template("500.html"), 500


# ==================== Application Setup ====================

if __name__ == "__main__":
    with app.app_context():
        db.create_all()
    app.run(debug=True)
