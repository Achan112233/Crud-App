"""
Main Azure Functions entry point
Serverless Python app - No VMs required
"""
import azure.functions as func
import json
from auth import token_mgr, azure_auth
from database import SessionLocal, User, Task
from datetime import datetime

app = func.FunctionApp()


# ==================== Helper Functions ====================

def get_user_from_token(req: func.HttpRequest):
    """Extract and validate user from JWT token"""
    auth_header = req.headers.get("Authorization")
    if not auth_header:
        return None, {"error": "Missing authorization token"}, 401
    
    try:
        token = auth_header.split(" ")[1]
    except IndexError:
        return None, {"error": "Invalid authorization header"}, 401
    
    payload = token_mgr.verify_token(token)
    if not payload:
        return None, {"error": "Invalid or expired token"}, 401
    
    return payload, None, None


def json_response(data, status_code=200):
    """Create JSON response"""
    return func.HttpResponse(
        json.dumps(data),
        status_code=status_code,
        mimetype="application/json"
    )


# ==================== Authentication Routes ====================

@app.route("login", methods=["GET"])
def login(req: func.HttpRequest) -> func.HttpResponse:
    """Redirect to Azure AD login"""
    try:
        auth_url = azure_auth.get_auth_url()
        return func.HttpResponse(
            f'<a href="{auth_url}">Click here to login with Microsoft</a>',
            status_code=200,
            mimetype="text/html"
        )
    except Exception as e:
        return json_response({"error": str(e)}, 500)


@app.route("callback", methods=["GET"])
def auth_callback(req: func.HttpRequest) -> func.HttpResponse:
    """Handle Azure AD callback"""
    code = req.params.get("code")
    error = req.params.get("error")

    if error:
        return json_response({"error": error}, 400)

    if not code:
        return json_response({"error": "No authorization code"}, 400)

    try:
        token_result = azure_auth.get_token_by_code(code)
        if not token_result:
            return json_response({"error": "Failed to obtain access token"}, 400)

        user_info = azure_auth.get_user_info(token_result["access_token"])
        if not user_info:
            return json_response({"error": "Failed to retrieve user info"}, 400)

        db = SessionLocal()
        user = db.query(User).filter_by(azure_id=user_info["id"]).first()
        if not user:
            user = User(
                azure_id=user_info["id"],
                email=user_info["email"],
                name=user_info["name"],
            )
            db.add(user)
        
        user.last_login = datetime.utcnow()
        db.commit()

        access_token = token_mgr.create_access_token(user.id, user.email, user.name)
        refresh_token = token_mgr.create_refresh_token(user.id)

        response = {
            "access_token": access_token,
            "refresh_token": refresh_token,
            "user": user.to_dict()
        }
        db.close()
        
        return json_response(response, 200)

    except Exception as e:
        return json_response({"error": str(e)}, 500)


@app.route("refresh", methods=["POST"])
def refresh_access_token(req: func.HttpRequest) -> func.HttpResponse:
    """Refresh access token"""
    try:
        data = req.get_json()
        refresh_token = data.get("refresh_token")

        if not refresh_token:
            return json_response({"error": "Missing refresh token"}, 400)

        payload = token_mgr.verify_refresh_token(refresh_token)
        if not payload:
            return json_response({"error": "Invalid refresh token"}, 401)

        db = SessionLocal()
        user = db.query(User).get(payload["user_id"])
        if not user:
            db.close()
            return json_response({"error": "User not found"}, 404)

        new_access_token = token_mgr.create_access_token(user.id, user.email, user.name)
        db.close()
        
        return json_response({"access_token": new_access_token}, 200)
    except Exception as e:
        return json_response({"error": str(e)}, 500)


# ==================== Task API Routes ====================

@app.route("tasks", methods=["GET", "POST"])
def tasks(req: func.HttpRequest) -> func.HttpResponse:
    """Get all tasks or create new task"""
    user, error, status = get_user_from_token(req)
    if error:
        return json_response(error, status)

    db = SessionLocal()
    
    if req.method == "GET":
        status_filter = req.params.get("status")
        priority_filter = req.params.get("priority")

        query = db.query(Task).filter_by(user_id=user["user_id"])
        
        if status_filter:
            query = query.filter_by(status=status_filter)
        if priority_filter:
            query = query.filter_by(priority=priority_filter)

        tasks_list = query.order_by(Task.created_at.desc()).all()
        db.close()
        
        return json_response([t.to_dict() for t in tasks_list], 200)

    elif req.method == "POST":
        try:
            data = req.get_json()
            if not data or not data.get("title"):
                db.close()
                return json_response({"error": "Title is required"}, 400)

            new_task = Task(
                user_id=user["user_id"],
                title=data.get("title"),
                description=data.get("description"),
                priority=data.get("priority", "medium"),
                due_date=datetime.fromisoformat(data["due_date"]) if data.get("due_date") else None,
            )

            db.add(new_task)
            db.commit()
            db.refresh(new_task)
            result = new_task.to_dict()
            db.close()
            
            return json_response(result, 201)
        except Exception as e:
            db.close()
            return json_response({"error": str(e)}, 400)


@app.route("tasks/{task_id}", methods=["GET", "PUT", "DELETE"])
def task_detail(req: func.HttpRequest) -> func.HttpResponse:
    """Get, update, or delete specific task"""
    user, error, status = get_user_from_token(req)
    if error:
        return json_response(error, status)

    task_id = req.route_params.get("task_id")
    db = SessionLocal()
    task = db.query(Task).filter_by(id=task_id, user_id=user["user_id"]).first()

    if not task:
        db.close()
        return json_response({"error": "Task not found"}, 404)

    if req.method == "GET":
        result = task.to_dict()
        db.close()
        return json_response(result, 200)

    elif req.method == "PUT":
        try:
            data = req.get_json()
            
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
            db.commit()
            db.refresh(task)
            result = task.to_dict()
            db.close()
            
            return json_response(result, 200)
        except Exception as e:
            db.close()
            return json_response({"error": str(e)}, 400)

    elif req.method == "DELETE":
        try:
            db.delete(task)
            db.commit()
            db.close()
            return func.HttpResponse("", status_code=204)
        except Exception as e:
            db.close()
            return json_response({"error": str(e)}, 500)


@app.route("tasks/{task_id}/status", methods=["PATCH"])
def update_task_status(req: func.HttpRequest) -> func.HttpResponse:
    """Update task status"""
    user, error, status = get_user_from_token(req)
    if error:
        return json_response(error, status)

    task_id = req.route_params.get("task_id")
    db = SessionLocal()
    task = db.query(Task).filter_by(id=task_id, user_id=user["user_id"]).first()

    if not task:
        db.close()
        return json_response({"error": "Task not found"}, 404)

    try:
        data = req.get_json()
        new_status = data.get("status")

        if new_status not in ["pending", "in_progress", "completed"]:
            db.close()
            return json_response({"error": "Invalid status"}, 400)

        task.status = new_status
        if new_status == "completed" and not task.completed_at:
            task.completed_at = datetime.utcnow()
        elif new_status != "completed":
            task.completed_at = None

        task.updated_at = datetime.utcnow()
        db.commit()
        db.refresh(task)
        result = task.to_dict()
        db.close()
        
        return json_response(result, 200)
    except Exception as e:
        db.close()
        return json_response({"error": str(e)}, 400)


# ==================== User Routes ====================

@app.route("user/profile", methods=["GET"])
def user_profile(req: func.HttpRequest) -> func.HttpResponse:
    """Get current user profile"""
    user, error, status = get_user_from_token(req)
    if error:
        return json_response(error, status)

    db = SessionLocal()
    user_obj = db.query(User).get(user["user_id"])
    
    if not user_obj:
        db.close()
        return json_response({"error": "User not found"}, 404)
    
    result = user_obj.to_dict()
    db.close()
    return json_response(result, 200)


@app.route("stats", methods=["GET"])
def stats(req: func.HttpRequest) -> func.HttpResponse:
    """Get user task statistics"""
    user, error, status = get_user_from_token(req)
    if error:
        return json_response(error, status)

    db = SessionLocal()
    tasks_list = db.query(Task).filter_by(user_id=user["user_id"]).all()

    stats_data = {
        "total_tasks": len(tasks_list),
        "completed_tasks": len([t for t in tasks_list if t.status == "completed"]),
        "pending_tasks": len([t for t in tasks_list if t.status == "pending"]),
        "in_progress_tasks": len([t for t in tasks_list if t.status == "in_progress"]),
        "high_priority_tasks": len([t for t in tasks_list if t.priority == "high"]),
    }
    
    db.close()
    return json_response(stats_data, 200)


# ==================== Health Check ====================

@app.route("health", methods=["GET"])
def health(req: func.HttpRequest) -> func.HttpResponse:
    """Health check endpoint"""
    return json_response({"status": "healthy"}, 200)
