from fastapi import (
    APIRouter,
    HTTPException,
    Depends,
    UploadFile,
    File
)

from fastapi.security import (
    HTTPBearer,
    HTTPAuthorizationCredentials
)

from pydantic import BaseModel

import pandas as pd
import io


# =========================================================
# DATABASE
# =========================================================

from backend.database.database import (
    init_database,
    log_activity
)

from backend.database.models import (
    create_user,
    get_user_by_username,
    get_user_by_email
)


# =========================================================
# AUTHENTICATION
# =========================================================

from backend.auth.auth import (
    hash_password,
    verify_password,
    create_session,
    get_session_user,
    remove_session
)


# =========================================================
# NLP
# =========================================================

from backend.nlp.ner_extractor import extract_entities
from backend.nlp.relation_extractor import extract_relations


# =========================================================
# GRAPH
# =========================================================

from backend.graph.graph_store import (
    build_graph,
    bfs_search,
    dfs_search,
    astar_search,
    graph_json
)


# =========================================================
# REASONING
# =========================================================

from backend.reasoning.bayesian import (
    calculate_confidence,
    explain_confidence
)

from backend.reasoning.csp import (
    detect_contradictions
)


# =========================================================
# REPORT
# =========================================================

from backend.report.report_generator import (
    generate_report
)


# =========================================================
# ROUTER
# =========================================================

router = APIRouter()


# =========================================================
# AUTHENTICATION SECURITY
# =========================================================

security = HTTPBearer(auto_error=False)


# =========================================================
# DATABASE INITIALIZATION
# =========================================================

init_database()


# =========================================================
# REQUEST MODELS
# =========================================================

class RegisterRequest(BaseModel):
    username: str
    email: str
    password: str


# LOGIN USES EMAIL
class LoginRequest(BaseModel):
    email: str
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

    # -----------------------------------------------------
    # Validation
    # -----------------------------------------------------

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

    # -----------------------------------------------------
    # Check username
    # -----------------------------------------------------

    if get_user_by_username(username):

        raise HTTPException(
            status_code=409,
            detail="Username already exists."
        )

    # -----------------------------------------------------
    # Check email
    # -----------------------------------------------------

    if get_user_by_email(email):

        raise HTTPException(
            status_code=409,
            detail="Email already registered."
        )

    # -----------------------------------------------------
    # Hash password
    # -----------------------------------------------------

    password_hash = hash_password(password)

    # -----------------------------------------------------
    # Create user
    # -----------------------------------------------------

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

    # -----------------------------------------------------
    # Activity log
    # -----------------------------------------------------

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

    # -----------------------------------------------------
    # Get email
    # -----------------------------------------------------

    email = request.email.strip().lower()

    # -----------------------------------------------------
    # Find user by EMAIL
    # -----------------------------------------------------

    user = get_user_by_email(email)

    if not user:

        raise HTTPException(
            status_code=401,
            detail="Invalid email or password."
        )

    # -----------------------------------------------------
    # Verify password
    # -----------------------------------------------------

    password_valid = verify_password(
        request.password,
        user["password_hash"]
    )

    if not password_valid:

        log_activity(
            user["username"],
            "LOGIN_FAILED",
            "Invalid password."
        )

        raise HTTPException(
            status_code=401,
            detail="Invalid email or password."
        )

    # -----------------------------------------------------
    # Create session
    # -----------------------------------------------------

    token = create_session(
        user["username"]
    )

    # -----------------------------------------------------
    # Activity log
    # -----------------------------------------------------

    log_activity(
        user["username"],
        "LOGIN",
        "Investigator logged into the system."
    )

    # -----------------------------------------------------
    # Return response
    # -----------------------------------------------------

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
    credentials: HTTPAuthorizationCredentials | None = Depends(security)
):

    # -----------------------------------------------------
    # No token
    # -----------------------------------------------------

    if not credentials:

        return {
            "status": "success",
            "message": "Already logged out."
        }

    # -----------------------------------------------------
    # Get token
    # -----------------------------------------------------

    token = credentials.credentials

    # -----------------------------------------------------
    # Find logged-in user
    # -----------------------------------------------------

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
    credentials: HTTPAuthorizationCredentials | None = Depends(security)
):

    # -----------------------------------------------------
    # Check authentication
    # -----------------------------------------------------

    if not credentials:

        raise HTTPException(
            status_code=401,
            detail="Authentication required."
        )

    # -----------------------------------------------------
    # Extract token
    # -----------------------------------------------------

    token = credentials.credentials

    username = get_session_user(token)

    if not username:

        raise HTTPException(
            status_code=401,
            detail="Invalid or expired session."
        )

    # -----------------------------------------------------
    # Get user
    # -----------------------------------------------------

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
# TEXT INVESTIGATION
# =========================================================

@router.post("/investigate")
def investigate(
    request: InvestigationRequest,
    credentials: HTTPAuthorizationCredentials | None = Depends(security)
):

    # -----------------------------------------------------
    # Authentication
    # -----------------------------------------------------

    if not credentials:

        raise HTTPException(
            status_code=401,
            detail="Please login before starting an investigation."
        )

    token = credentials.credentials

    username = get_session_user(token)

    if not username:

        raise HTTPException(
            status_code=401,
            detail="Invalid session. Please login again."
        )

    # -----------------------------------------------------
    # Validate case description
    # -----------------------------------------------------

    if not request.text.strip():

        raise HTTPException(
            status_code=400,
            detail="Case description cannot be empty."
        )

    # =====================================================
    # NLP - ENTITY EXTRACTION
    # =====================================================

    entities = extract_entities(
        request.text
    )

    # =====================================================
    # NLP - RELATION EXTRACTION
    # =====================================================

    relations = extract_relations(
        request.text
    )

    # =====================================================
    # GRAPH CONSTRUCTION
    # =====================================================

    graph = build_graph(
        relations
    )

    # =====================================================
    # SEARCH PARAMETERS
    # =====================================================

    start = request.start_node.strip()
    target = request.target_node.strip()

    # =====================================================
    # BFS
    # =====================================================

    bfs = bfs_search(
        graph,
        start,
        target
    )

    # =====================================================
    # DFS
    # =====================================================

    dfs = dfs_search(
        graph,
        start,
        target
    )

    # =====================================================
    # A*
    # =====================================================

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

    # =====================================================
    # CSP - CONTRADICTION DETECTION
    # =====================================================

    contradictions = detect_contradictions(
        request.text,
        relations
    )

    # =====================================================
    # BAYESIAN CONFIDENCE
    # =====================================================

    confidence = calculate_confidence(
        entities,
        relations,
        contradictions
    )

    # =====================================================
    # CONFIDENCE EXPLANATION
    # =====================================================

    explanation = explain_confidence(
        entities,
        relations,
        contradictions
    )

    # =====================================================
    # PDF REPORT GENERATION
    # =====================================================

    report_file = generate_report(
        request.text,
        entities,
        relations,
        search_results,
        confidence,
        contradictions
    )

    # =====================================================
    # ACTIVITY LOG
    # =====================================================

    log_activity(
        username,
        "INVESTIGATION",
        "Crime investigation executed."
    )

    # =====================================================
    # FINAL RESPONSE
    # =====================================================

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
            "message": "Investigation report generated successfully."
        }
    }


# =========================================================
# EXCEL CASE REPORT INVESTIGATION
# =========================================================

@router.post("/investigate/excel")
async def investigate_excel(
    file: UploadFile = File(...),
    credentials: HTTPAuthorizationCredentials | None = Depends(security)
):

    # -----------------------------------------------------
    # AUTHENTICATION
    # -----------------------------------------------------

    if not credentials:

        raise HTTPException(
            status_code=401,
            detail="Please login before uploading a case report."
        )

    token = credentials.credentials

    username = get_session_user(token)

    if not username:

        raise HTTPException(
            status_code=401,
            detail="Invalid session. Please login again."
        )

    # -----------------------------------------------------
    # FILE VALIDATION
    # -----------------------------------------------------

    if not file.filename:

        raise HTTPException(
            status_code=400,
            detail="Please upload an Excel case report."
        )

    filename = file.filename.lower()

    if not filename.endswith((".xlsx", ".xls")):

        raise HTTPException(
            status_code=400,
            detail="Only Excel files (.xlsx or .xls) are supported."
        )

    # -----------------------------------------------------
    # READ EXCEL FILE
    # -----------------------------------------------------

    try:

        file_content = await file.read()

        if not file_content:

            raise HTTPException(
                status_code=400,
                detail="Uploaded Excel file is empty."
            )

        excel_file = io.BytesIO(
            file_content
        )

        # -------------------------------------------------
        # XLSX
        # -------------------------------------------------

        if filename.endswith(".xlsx"):

            dataframe = pd.read_excel(
                excel_file,
                engine="openpyxl"
            )

        # -------------------------------------------------
        # XLS
        # -------------------------------------------------

        else:

            dataframe = pd.read_excel(
                excel_file,
                engine="xlrd"
            )

    except HTTPException:

        raise

    except Exception as e:

        raise HTTPException(
            status_code=400,
            detail=f"Unable to read Excel file: {str(e)}"
        )

    # -----------------------------------------------------
    # VALIDATE DATA
    # -----------------------------------------------------

    if dataframe.empty:

        raise HTTPException(
            status_code=400,
            detail="The Excel case report is empty."
        )

    # -----------------------------------------------------
    # REMOVE EMPTY ROWS
    # -----------------------------------------------------

    dataframe = dataframe.dropna(
        how="all"
    )

    # -----------------------------------------------------
    # REMOVE EMPTY COLUMNS
    # -----------------------------------------------------

    dataframe = dataframe.dropna(
        axis=1,
        how="all"
    )

    if dataframe.empty:

        raise HTTPException(
            status_code=400,
            detail="The Excel case report contains no usable data."
        )

    # -----------------------------------------------------
    # LIMIT LARGE FILES
    # -----------------------------------------------------

    MAX_ROWS = 5000

    original_rows = len(dataframe)

    rows_limited = False

    if original_rows > MAX_ROWS:

        dataframe = dataframe.head(
            MAX_ROWS
        )

        rows_limited = True

    # -----------------------------------------------------
    # CONVERT EXCEL TO TEXT
    # -----------------------------------------------------

    case_parts = []

    for _, row in dataframe.iterrows():

        row_values = []

        for column, value in row.items():

            if pd.notna(value):

                row_values.append(
                    f"{column}: {value}"
                )

        if row_values:

            case_parts.append(
                " | ".join(row_values)
            )

    case_text = "\n".join(
        case_parts
    )

    if not case_text.strip():

        raise HTTPException(
            status_code=400,
            detail="No readable case information was found in the Excel file."
        )

    # =====================================================
    # NLP - ENTITY EXTRACTION
    # =====================================================

    try:

        entities = extract_entities(
            case_text
        )

    except Exception as e:

        raise HTTPException(
            status_code=500,
            detail=f"Entity extraction failed: {str(e)}"
        )

    # =====================================================
    # NLP - RELATION EXTRACTION
    # =====================================================

    try:

        relations = extract_relations(
            case_text
        )

    except Exception as e:

        raise HTTPException(
            status_code=500,
            detail=f"Relation extraction failed: {str(e)}"
        )

    # =====================================================
    # GRAPH CONSTRUCTION
    # =====================================================

    try:

        graph = build_graph(
            relations
        )

    except Exception as e:

        raise HTTPException(
            status_code=500,
            detail=f"Graph construction failed: {str(e)}"
        )

    # -----------------------------------------------------
    # FIND GRAPH NODES
    # -----------------------------------------------------

    nodes = []

    if hasattr(graph, "nodes"):

        try:

            nodes = list(
                graph.nodes
            )

        except Exception:

            nodes = []

    if len(nodes) >= 2:

        start = nodes[0]
        target = nodes[-1]

    else:

        start = ""
        target = ""

    # =====================================================
    # BFS
    # =====================================================

    try:

        bfs = bfs_search(
            graph,
            start,
            target
        )

    except Exception:

        bfs = []

    # =====================================================
    # DFS
    # =====================================================

    try:

        dfs = dfs_search(
            graph,
            start,
            target
        )

    except Exception:

        dfs = []

    # =====================================================
    # A*
    # =====================================================

    try:

        astar = astar_search(
            graph,
            start,
            target
        )

    except Exception:

        astar = []

    search_results = {
        "BFS": bfs,
        "DFS": dfs,
        "A*": astar
    }

    # =====================================================
    # CSP
    # =====================================================

    try:

        contradictions = detect_contradictions(
            case_text,
            relations
        )

    except Exception as e:

        contradictions = [
            f"Contradiction analysis failed: {str(e)}"
        ]

    # =====================================================
    # BAYESIAN CONFIDENCE
    # =====================================================

    try:

        confidence = calculate_confidence(
            entities,
            relations,
            contradictions
        )

    except Exception:

        confidence = 0

    # =====================================================
    # CONFIDENCE EXPLANATION
    # =====================================================

    try:

        explanation = explain_confidence(
            entities,
            relations,
            contradictions
        )

    except Exception as e:

        explanation = (
            f"Confidence explanation unavailable: {str(e)}"
        )

    # =====================================================
    # PDF REPORT
    # =====================================================

    try:

        report_file = generate_report(
            case_text,
            entities,
            relations,
            search_results,
            confidence,
            contradictions
        )

    except Exception as e:

        report_file = None

        explanation = (
            f"{explanation}\n"
            f"PDF report generation failed: {str(e)}"
        )

    # =====================================================
    # ACTIVITY LOG
    # =====================================================

    try:

        log_activity(
            username,
            "EXCEL_INVESTIGATION",
            f"Excel case report analyzed: {file.filename}"
        )

    except Exception:

        pass

    # =====================================================
    # FINAL RESPONSE
    # =====================================================

    return {

        "status": "success",

        "message": "Excel case report analyzed successfully.",

        "filename": file.filename,

        "original_rows": original_rows,

        "rows_processed": len(dataframe),

        "rows_limited": rows_limited,

        "columns_detected": [
            str(column)
            for column in dataframe.columns
        ],

        "entities": entities,

        "relations": relations,

        "graph": graph_json(graph),

        "search_results": search_results,

        "bayesian_confidence": confidence,

        "contradictions": contradictions,

        "explanation": explanation,

        "report": {

            "file": report_file,

            "message": (
                "Investigation PDF report generated successfully."
                if report_file
                else "PDF report could not be generated."
            )
        }
    }


# =========================================================
# ACTIVITY LOGS
# =========================================================

@router.get("/auth/logs")
def get_logs(
    credentials: HTTPAuthorizationCredentials | None = Depends(security)
):

    # -----------------------------------------------------
    # Authentication
    # -----------------------------------------------------

    if not credentials:

        raise HTTPException(
            status_code=401,
            detail="Authentication required."
        )

    token = credentials.credentials

    username = get_session_user(token)

    if not username:

        raise HTTPException(
            status_code=401,
            detail="Invalid session."
        )

    # -----------------------------------------------------
    # Database connection
    # -----------------------------------------------------

    from backend.database.database import get_connection

    connection = get_connection()

    cursor = connection.cursor()

    # -----------------------------------------------------
    # Get logs
    # -----------------------------------------------------

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

    # -----------------------------------------------------
    # Return logs
    # -----------------------------------------------------

    return {
        "status": "success",
        "logs": logs
    }