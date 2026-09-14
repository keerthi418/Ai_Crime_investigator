from fastapi import APIRouter, HTTPException, Header
from pydantic import BaseModel

from backend.database.database import (
    init_database,
    log_activity
)

from backend.database.models import (
    create_user,
    get_user_by_username,
    get_user_by_email
)

from backend.auth.auth import (
    hash_password,
    verify_password,
    create_session,
    get_session_user,
    remove_session
)

from backend.nlp.ner_extractor import extract_entities
from backend.nlp.relation_extractor import extract_relations

from backend.graph.graph_store import (
    build_graph,
    bfs_search,
    dfs_search,
    astar_search,
    graph_json
)

from backend.reasoning.bayesian import (
    calculate_confidence,
    explain_confidence
)

from backend.reasoning.csp import (
    detect_contradictions
)

from backend.report.report_generator import (
    generate_report
)


router = APIRouter()


# Initialize database
init_database()


# =========================================================
# MODELS
# =========================================================

class RegisterRequest(BaseModel):

    username: str
    email: str
    password: str


class LoginRequest(BaseModel):

    username: str
    password: str


class InvestigationRequest(BaseModel):

    text: str
    start_node: str = ""
    target_node: str = ""


# =========================================================
# API STATUS
# =========================================================

@router.get("/")
def api_status():

    return {
        "message": "AI Crime Investigator API is running",
        "status": "success"
    }


# =========================================================
# REGISTER
# =========================================================

@router.post("/auth/register")
def register(request: RegisterRequest):

    username = request.username.strip()
    email = request.email.strip().lower()
    password = request.password

    # Validation
    if not username:

        raise HTTPException(
            status_code=400,
            detail="Username is required."
        )

    if not email:

        raise HTTPException(
            status_code=400,
            detail="Email is required."
        )

    if len(password) < 6:

        raise HTTPException(
            status_code=400,
            detail="Password must contain at least 6 characters."
        )

    # Check username
    if get_user_by_username(username):

        raise HTTPException(
            status_code=409,
            detail="Username already exists."
        )

    # Check email
    if get_user_by_email(email):

        raise HTTPException(
            status_code=409,
            detail="Email already registered."
        )

    # Hash password
    password_hash = hash_password(password)

    # Create user
    user_id = create_user(
        username,
        email,
        password_hash
    )

    if not user_id:

        raise HTTPException(
            status_code=500,
            detail="Account creation failed."
        )

    # Log activity
    log_activity(
        username,
        "ACCOUNT_CREATED",
        "New investigator account created."
    )

    return {

        "status": "success",

        "message": "Account created successfully.",

        "user": {

            "id": user_id,

            "username": username,

            "email": email

        }

    }


# =========================================================
# LOGIN
# =========================================================

@router.post("/auth/login")
def login(request: LoginRequest):

    username = request.username.strip()

    user = get_user_by_username(username)

    if not user:

        raise HTTPException(
            status_code=401,
            detail="Invalid username or password."
        )

    password_valid = verify_password(
        request.password,
        user["password_hash"]
    )

    if not password_valid:

        log_activity(
            username,
            "LOGIN_FAILED",
            "Invalid password."
        )

        raise HTTPException(
            status_code=401,
            detail="Invalid username or password."
        )

    token = create_session(username)

    log_activity(
        username,
        "LOGIN",
        "Investigator logged into the system."
    )

    return {

        "status": "success",

        "message": "Login successful.",

        "token": token,

        "user": {

            "id": user["id"],

            "username": user["username"],

            "email": user["email"]

        }

    }


# =========================================================
# LOGOUT
# =========================================================

@router.post("/auth/logout")
def logout(
    authorization: str | None = Header(default=None)
):

    if not authorization:

        return {
            "status": "success",
            "message": "Already logged out."
        }

    token = authorization.replace(
        "Bearer ",
        ""
    )

    username = get_session_user(token)

    if username:

        log_activity(
            username,
            "LOGOUT",
            "Investigator logged out."
        )

        remove_session(token)

    return {

        "status": "success",

        "message": "Logout successful."

    }


# =========================================================
# CURRENT USER
# =========================================================

@router.get("/auth/me")
def current_user(
    authorization: str | None = Header(default=None)
):

    if not authorization:

        raise HTTPException(
            status_code=401,
            detail="Authentication required."
        )

    token = authorization.replace(
        "Bearer ",
        ""
    )

    username = get_session_user(token)

    if not username:

        raise HTTPException(
            status_code=401,
            detail="Invalid or expired session."
        )

    user = get_user_by_username(username)

    if not user:

        raise HTTPException(
            status_code=401,
            detail="User not found."
        )

    return {

        "status": "success",

        "user": {

            "id": user["id"],

            "username": user["username"],

            "email": user["email"]

        }

    }


# =========================================================
# INVESTIGATION
# =========================================================

@router.post("/investigate")
def investigate(
    request: InvestigationRequest,
    authorization: str | None = Header(default=None)
):

    if not authorization:

        raise HTTPException(
            status_code=401,
            detail="Please login before starting an investigation."
        )

    token = authorization.replace(
        "Bearer ",
        ""
    )

    username = get_session_user(token)

    if not username:

        raise HTTPException(
            status_code=401,
            detail="Invalid session. Please login again."
        )

    if not request.text.strip():

        raise HTTPException(
            status_code=400,
            detail="Case description cannot be empty."
        )

    entities = extract_entities(
        request.text
    )

    relations = extract_relations(
        request.text
    )

    graph = build_graph(
        relations
    )

    start = request.start_node.strip()

    target = request.target_node.strip()

    bfs = bfs_search(
        graph,
        start,
        target
    )

    dfs = dfs_search(
        graph,
        start,
        target
    )

    astar = astar_search(
        graph,
        start,
        target
    )

    search_results = {

        "BFS": bfs,

        "DFS": dfs,

        "A*": astar

    }

    contradictions = detect_contradictions(
        request.text,
        relations
    )

    confidence = calculate_confidence(
        entities,
        relations,
        contradictions
    )

    explanation = explain_confidence(
        entities,
        relations,
        contradictions
    )

    report_file = generate_report(
        request.text,
        entities,
        relations,
        search_results,
        confidence,
        contradictions
    )

    log_activity(
        username,
        "INVESTIGATION",
        "Crime investigation executed."
    )

    return {

        "status": "success",

        "entities": entities,

        "relations": relations,

        "graph": graph_json(graph),

        "search_results": search_results,

        "bayesian_confidence": confidence,

        "contradictions": contradictions,

        "explanation": explanation,

        "report": {

            "file": report_file,

            "message":
            "Investigation report generated successfully."

        }

    }


# =========================================================
# ACTIVITY LOG
# =========================================================

@router.get("/auth/logs")
def get_logs(
    authorization: str | None = Header(default=None)
):

    if not authorization:

        raise HTTPException(
            status_code=401,
            detail="Authentication required."
        )

    token = authorization.replace(
        "Bearer ",
        ""
    )

    username = get_session_user(token)

    if not username:

        raise HTTPException(
            status_code=401,
            detail="Invalid session."
        )

    from backend.database.database import get_connection

    connection = get_connection()

    cursor = connection.cursor()

    cursor.execute(
        """
        SELECT
            action,
            details,
            created_at
        FROM activity_logs
        WHERE username = ?
        ORDER BY id DESC
        LIMIT 100
        """,
        (username,)
    )

    logs = [

        dict(row)

        for row in cursor.fetchall()

    ]

    connection.close()

    return {

        "status": "success",

        "logs": logs

    }