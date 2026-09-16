const API = "http://127.0.0.1:8000/api";

let currentUser = null;
let lastInvestigation = null;
let graphInstance = null;
let pending2FAChallenge = null;


/* =========================================================
   PAGE LOAD
========================================================= */

document.addEventListener("DOMContentLoaded", () => {

    const token = localStorage.getItem("access_token");
    const page = window.location.pathname.split("/").pop();

    if (token) {
        loadCurrentUser();
    } else if (page === "index.html" || page === "") {
        window.location.href = "login.html";
    }

    const loginForm = document.getElementById("loginForm");

    if (loginForm) {
        loginForm.addEventListener("submit", login);
    }

    const registerForm = document.getElementById("registerForm");

    if (registerForm) {
        registerForm.addEventListener("submit", register);
    }

    const startNodeInput = document.getElementById("startNode");
    const targetNodeInput = document.getElementById("targetNode");

    if (startNodeInput) {
        startNodeInput.addEventListener("keydown", event => {
            if (event.key === "Enter") {
                event.preventDefault();
                runSelectedAlgorithm("BFS");
            }
        });
    }

    if (targetNodeInput) {
        targetNodeInput.addEventListener("keydown", event => {
            if (event.key === "Enter") {
                event.preventDefault();
                runSelectedAlgorithm("BFS");
            }
        });
    }

    setInvestigationStatus("closed");
});


/* =========================================================
   LOGIN
========================================================= */

async function login(event) {

    event.preventDefault();

    const email =
        document.getElementById("loginEmail")?.value.trim();

    const password =
        document.getElementById("loginPassword")?.value;

    if (!email || !password) {

        showMessage(
            "loginMessage",
            "Please enter email and password.",
            "error"
        );

        return;
    }

    showMessage(
        "loginMessage",
        "Signing in...",
        "success"
    );

    try {

        const response = await fetch(
            `${API}/auth/login`,
            {
                method: "POST",

                headers: {
                    "Content-Type": "application/json"
                },

                body: JSON.stringify({
                    email: email,
                    password: password
                })
            }
        );

        const data = await safeJson(response);

        if (!response.ok) {

            throw new Error(
                data.detail || "Login failed."
            );
        }


        /* =================================================
           2FA REQUIRED
        ================================================= */

        if (
            data.requires_2fa ||
            data.status === "2fa_required"
        ) {

            pending2FAChallenge =
                data.challenge_token;

            const modal =
                document.getElementById(
                    "twoFALoginModal"
                );

            if (modal) {
                modal.classList.remove("hidden");
            }

            showMessage(
                "loginMessage",
                "Password accepted. Enter your 2FA code.",
                "success"
            );

            const codeInput =
                document.getElementById(
                    "login2FACode"
                );

            if (codeInput) {
                codeInput.focus();
            }

            return;
        }


        /* =================================================
           NORMAL LOGIN
        ================================================= */

        if (data.token) {

            localStorage.setItem(
                "access_token",
                data.token
            );
        }

        if (data.user) {

            localStorage.setItem(
                "user",
                JSON.stringify(data.user)
            );
        }

        showMessage(
            "loginMessage",
            "Login successful. Redirecting...",
            "success"
        );

        setTimeout(() => {
            window.location.href = "index.html";
        }, 500);

    }

    catch (error) {

        console.error("Login error:", error);

        showMessage(
            "loginMessage",
            error.message,
            "error"
        );
    }
}


/* =========================================================
   VERIFY LOGIN 2FA
========================================================= */

async function verifyLogin2FA() {

    const codeElement =
        document.getElementById("login2FACode");

    if (!codeElement) {
        return;
    }

    const code =
        codeElement.value.trim();

    if (!code || !/^\d{6}$/.test(code)) {

        showMessage(
            "login2FAMessage",
            "Please enter the 6-digit code.",
            "error"
        );

        return;
    }

    if (!pending2FAChallenge) {

        showMessage(
            "login2FAMessage",
            "2FA session expired. Please login again.",
            "error"
        );

        return;
    }

    try {

        const response = await fetch(
            `${API}/auth/2fa/verify`,
            {
                method: "POST",

                headers: {
                    "Content-Type": "application/json"
                },

                body: JSON.stringify({
                    challenge_token:
                        pending2FAChallenge,

                    code: code
                })
            }
        );

        const data = await safeJson(response);

        if (!response.ok) {

            throw new Error(
                data.detail ||
                "Invalid 2FA code."
            );
        }

        if (data.token) {

            localStorage.setItem(
                "access_token",
                data.token
            );
        }

        if (data.user) {

            localStorage.setItem(
                "user",
                JSON.stringify(data.user)
            );
        }

        pending2FAChallenge = null;

        showMessage(
            "login2FAMessage",
            "Verification successful.",
            "success"
        );

        setTimeout(() => {

            window.location.href =
                "index.html";

        }, 500);

    }

    catch (error) {

        console.error(
            "2FA verification error:",
            error
        );

        showMessage(
            "login2FAMessage",
            error.message,
            "error"
        );
    }
}


/* =========================================================
   REGISTER
========================================================= */

async function register(event) {

    event.preventDefault();

    const username =
        document
            .getElementById("registerUsername")
            ?.value.trim();

    const email =
        document
            .getElementById("registerEmail")
            ?.value.trim();

    const password =
        document
            .getElementById("registerPassword")
            ?.value;

    if (!username || !email || !password) {

        showMessage(
            "registerMessage",
            "Please fill all fields.",
            "error"
        );

        return;
    }

    if (password.length < 8) {

        showMessage(
            "registerMessage",
            "Password must contain at least 8 characters.",
            "error"
        );

        return;
    }

    showMessage(
        "registerMessage",
        "Creating account...",
        "success"
    );

    try {

        const response = await fetch(
            `${API}/auth/register`,
            {
                method: "POST",

                headers: {
                    "Content-Type": "application/json"
                },

                body: JSON.stringify({
                    username: username,
                    email: email,
                    password: password
                })
            }
        );

        const data = await safeJson(response);

        if (!response.ok) {

            throw new Error(
                data.detail ||
                "Registration failed."
            );
        }

        showMessage(
            "registerMessage",
            "Account created successfully. You can now login.",
            "success"
        );

        const form =
            document.getElementById("registerForm");

        if (form) {
            form.reset();
        }

        setTimeout(() => {
            hideRegister();
        }, 1500);

    }

    catch (error) {

        console.error(
            "Registration error:",
            error
        );

        showMessage(
            "registerMessage",
            error.message,
            "error"
        );
    }
}


/* =========================================================
   CURRENT USER
========================================================= */

async function loadCurrentUser() {

    const token =
        localStorage.getItem("access_token");

    if (!token) {

        window.location.href =
            "login.html";

        return;
    }

    try {

        const response =
            await fetch(
                `${API}/auth/me`,
                {
                    method: "GET",

                    headers: {
                        "Authorization":
                            `Bearer ${token}`
                    }
                }
            );

        if (!response.ok) {

            localStorage.clear();

            window.location.href =
                "login.html";

            return;
        }

        const data =
            await safeJson(response);

        currentUser =
            data.user;

        updateUserUI();

        loadAuditLogs();

    }

    catch (error) {

        console.error(
            "Current user error:",
            error
        );
    }
}


/* =========================================================
   UPDATE USER UI
========================================================= */

function updateUserUI() {

    if (!currentUser) {
        return;
    }

    const username =
        currentUser.username || "";

    const initial =
        username
            .charAt(0)
            .toUpperCase();

    const elements = {

        sidebarUsername:
            username,

        topUsername:
            username,

        welcomeName:
            username,

        profileUsername:
            username,

        profileEmail:
            currentUser.email || "",

        sidebarAvatar:
            initial,

        topAvatar:
            initial,

        profileAvatar:
            initial
    };

    Object.keys(elements).forEach(id => {

        const element =
            document.getElementById(id);

        if (element) {

            element.textContent =
                elements[id];
        }
    });
}


/* =========================================================
   LOGOUT
========================================================= */

async function logout() {

    const token =
        localStorage.getItem("access_token");

    try {

        if (token) {

            await fetch(
                `${API}/auth/logout`,
                {
                    method: "POST",

                    headers: {
                        "Authorization":
                            `Bearer ${token}`
                    }
                }
            );
        }

    }

    catch (error) {

        console.error(
            "Logout error:",
            error
        );
    }

    localStorage.clear();

    window.location.href =
        "login.html";
}


/* =========================================================
   PAGE NAVIGATION
========================================================= */

function showPage(pageName, button) {

    document
        .querySelectorAll(".page")
        .forEach(page => {

            page.classList.remove(
                "active-page"
            );
        });

    const page =
        document.getElementById(
            pageName + "Page"
        );

    if (page) {

        page.classList.add(
            "active-page"
        );
    }

    document
        .querySelectorAll(".nav-item")
        .forEach(item => {

            item.classList.remove(
                "active"
            );
        });

    if (button) {

        button.classList.add(
            "active"
        );
    }

    const titles = {

        dashboard:
            "Investigation Dashboard",

        investigation:
            "New Investigation",

        activity:
            "Audit Logs",

        profile:
            "Investigator Profile",

        settings:
            "Account Settings"
    };

    const title =
        document.getElementById(
            "pageTitle"
        );

    if (title) {

        title.textContent =
            titles[pageName] ||
            "AI Crime Investigator";
    }

    if (pageName === "activity") {
        loadAuditLogs();
    }

    if (pageName === "settings") {
        load2FAStatus();
    }
}


/* =========================================================
   OPEN INVESTIGATION
========================================================= */

function openInvestigation() {

    const button =
        document.querySelector(
            ".nav-item:nth-child(2)"
        );

    showPage(
        "investigation",
        button
    );
}


/* =========================================================
   INVESTIGATION STATUS
========================================================= */

function setInvestigationStatus(status) {

    const statusElement =
        document.getElementById(
            "investigationStatus"
        );

    if (!statusElement) {
        return;
    }

    statusElement.classList.remove(
        "ongoing",
        "closed"
    );

    if (status === "ongoing") {

        statusElement.textContent =
            "● INVESTIGATION ONGOING";

        statusElement.classList.add(
            "ongoing"
        );

    } else {

        statusElement.textContent =
            "● INVESTIGATION CLOSED";

        statusElement.classList.add(
            "closed"
        );
    }
}


/* =========================================================
   RUN INVESTIGATION
========================================================= */

async function runInvestigation() {

    const text =
        document
            .getElementById("caseText")
            ?.value.trim();

    const startNode =
        document
            .getElementById("startNode")
            ?.value.trim();

    const targetNode =
        document
            .getElementById("targetNode")
            ?.value.trim();

    if (!text) {

        showMessage(
            "investigationMessage",
            "Please enter a case description.",
            "error"
        );

        return;
    }

    setInvestigationStatus("ongoing");

    const button =
        document.getElementById(
            "runAnalysisButton"
        );

    if (button) {
        button.disabled = true;
    }

    const buttonText =
        document.getElementById(
            "analysisButtonText"
        );

    if (buttonText) {

        buttonText.textContent =
            "Analyzing investigation...";
    }

    showMessage(
        "investigationMessage",
        "Running NLP, graph search and AI reasoning...",
        "success"
    );

    try {

        const token =
            localStorage.getItem(
                "access_token"
            );

        if (!token) {

            throw new Error(
                "Please login before starting an investigation."
            );
        }

        const response =
            await fetch(
                `${API}/investigate`,
                {
                    method: "POST",

                    headers: {

                        "Content-Type":
                            "application/json",

                        "Authorization":
                            `Bearer ${token}`
                    },

                    body: JSON.stringify({

                        text: text,

                        start_node:
                            startNode || null,

                        target_node:
                            targetNode || null
                    })
                }
            );

        const data =
            await safeJson(response);

        if (!response.ok) {

            throw new Error(
                data.detail ||
                "Investigation failed."
            );
        }

        lastInvestigation =
            data;

        displayInvestigation(
            data
        );

        setInvestigationStatus(
            "closed"
        );

        showMessage(
            "investigationMessage",
            "Investigation completed successfully.",
            "success"
        );

        loadAuditLogs();

    }

    catch (error) {

        console.error(
            "Investigation error:",
            error
        );

        setInvestigationStatus(
            "closed"
        );

        showMessage(
            "investigationMessage",
            error.message,
            "error"
        );
    }

    finally {

        if (button) {
            button.disabled = false;
        }

        if (buttonText) {

            buttonText.textContent =
                "Run AI Investigation";
        }
    }
}


/* =========================================================
   DISPLAY INVESTIGATION
========================================================= */

function displayInvestigation(data) {

    const results =
        document.getElementById(
            "resultsArea"
        );

    if (results) {

        results.classList.remove(
            "hidden"
        );
    }

    const entities =
        Array.isArray(data.entities)
            ? data.entities
            : [];

    const relations =
        Array.isArray(data.relations)
            ? data.relations
            : [];

    const contradictions =
        Array.isArray(data.contradictions)
            ? data.contradictions
            : [];

    const confidence =
        data.bayesian_confidence;


    /* =====================================================
       COUNTERS
    ===================================================== */

    setText(
        "resultEntityCount",
        entities.length
    );

    setText(
        "resultRelationCount",
        relations.length
    );

    setText(
        "resultConfidence",
        formatConfidence(confidence)
    );

    setText(
        "resultContradictions",
        contradictions.length
    );

    setText(
        "entityCount",
        entities.length
    );

    setText(
        "confidenceValue",
        formatConfidence(confidence)
    );


    /* =====================================================
       DISPLAY DATA
    ===================================================== */

    displayEntities(
        entities
    );

    displayRelations(
        relations
    );

    displayAlgorithms(
        data.search_results || {}
    );

    displayConfidence(
        confidence,
        data.explanation || []
    );

    displayContradictions(
        contradictions
    );

    displayExplanation(
        data.explanation || []
    );


    /* =====================================================
       GRAPH
    ===================================================== */

    renderGraph(
        data.graph
    );


    /* =====================================================
       DASHBOARD COUNT
    ===================================================== */

    const caseCountElement =
        document.getElementById(
            "caseCount"
        );

    if (caseCountElement) {

        const caseCount =
            parseInt(
                caseCountElement.textContent
            ) || 0;

        caseCountElement.textContent =
            caseCount + 1;
    }


    const dashboardResult =
        document.getElementById(
            "dashboardResult"
        );

    if (dashboardResult) {

        dashboardResult.classList.remove(
            "hidden"
        );
    }


    const lastSummary =
        document.getElementById(
            "lastSummary"
        );

    if (lastSummary) {

        lastSummary.innerHTML = `

            <div class="quick-card">

                <div class="quick-icon">
                    🧠
                </div>

                <div>

                    <strong>
                        Investigation completed
                    </strong>

                    <span>
                        ${escapeHtml(
                            String(entities.length)
                        )}
                        entities,

                        ${escapeHtml(
                            String(relations.length)
                        )}
                        relationships,

                        confidence
                        ${escapeHtml(
                            formatConfidence(confidence)
                        )}
                    </span>

                </div>

            </div>
        `;
    }
}


/* =========================================================
   ENTITIES
========================================================= */

function displayEntities(entities) {

    const container =
        document.getElementById(
            "entitiesList"
        );

    if (!container) {
        return;
    }

    container.innerHTML = "";

    if (!entities.length) {

        container.innerHTML =
            "<span>No entities detected.</span>";

        return;
    }

    entities.forEach(entity => {

        const tag =
            document.createElement(
                "span"
            );

        tag.className =
            "entity-tag " +
            String(
                entity.type || ""
            )
                .toLowerCase()
                .replace(/\s+/g, "-");

        tag.textContent =
            `${entity.text || ""} · ${entity.type || ""}`;

        container.appendChild(
            tag
        );
    });
}


/* =========================================================
   RELATIONS
========================================================= */

function displayRelations(relations) {

    const container =
        document.getElementById(
            "relationsList"
        );

    if (!container) {
        return;
    }

    container.innerHTML = "";

    if (!relations.length) {

        container.innerHTML =
            "<span>No relationships detected.</span>";

        return;
    }

    relations.forEach(relation => {

        const item =
            document.createElement(
                "div"
            );

        item.className =
            "relation-item";

        item.innerHTML = `

            <b>
                ${escapeHtml(
                    relation.source || ""
                )}
            </b>

            &nbsp;

            <span>
                ${escapeHtml(
                    relation.relation || ""
                )}
            </span>

            →

            &nbsp;

            <b>
                ${escapeHtml(
                    relation.target || ""
                )}
            </b>
        `;

        container.appendChild(
            item
        );
    });
}


/* =========================================================
   SEARCH ALGORITHMS
========================================================= */

function displayAlgorithms(results) {

    const bfs =
        getSearchPath(results, "BFS");

    const dfs =
        getSearchPath(results, "DFS");

    const astar =
        getSearchPath(results, "A*");

    setText(
        "bfsResult",
        formatPath(bfs)
    );

    setText(
        "dfsResult",
        formatPath(dfs)
    );

    setText(
        "astarResult",
        formatPath(astar)
    );
}


/* =========================================================
   GET SEARCH PATH
========================================================= */

function getSearchPath(results, algorithm) {

    if (!results) {
        return [];
    }

    let result =
        results[algorithm];

    if (
        result === undefined &&
        algorithm === "A*"
    ) {
        result =
            results["astar"] ||
            results["Astar"] ||
            results["A_STAR"];
    }

    if (!result) {
        return [];
    }

    if (Array.isArray(result)) {
        return result;
    }

    if (
        typeof result === "object" &&
        Array.isArray(result.path)
    ) {
        return result.path;
    }

    return result;
}


/* =========================================================
   FORMAT PATH
========================================================= */

function formatPath(path) {

    if (!path) {
        return "No path found";
    }

    if (Array.isArray(path)) {

        if (!path.length) {
            return "No path found";
        }

        return path
            .map(item => String(item))
            .join(" → ");
    }

    if (
        typeof path === "object" &&
        Array.isArray(path.path)
    ) {

        if (!path.path.length) {
            return "No path found";
        }

        return path.path
            .map(item => String(item))
            .join(" → ");
    }

    const value =
        String(path).trim();

    return value || "No path found";
}


/* =========================================================
   RUN SELECTED ALGORITHM
========================================================= */

function runSelectedAlgorithm(algorithm) {

    if (!graphInstance) {

        showMessage(
            "investigationMessage",
            "Run an investigation first to create the knowledge graph.",
            "error"
        );

        return;
    }

    const start =
        document
            .getElementById("startNode")
            ?.value.trim();

    const target =
        document
            .getElementById("targetNode")
            ?.value.trim();

    if (!start || !target) {

        showMessage(
            "investigationMessage",
            "Enter both Start Entity and Target Entity.",
            "error"
        );

        return;
    }

    const startNode =
        findGraphNode(start);

    const targetNode =
        findGraphNode(target);

    if (!startNode || !targetNode) {

        showMessage(
            "investigationMessage",
            "Start or target entity was not found in the graph.",
            "error"
        );

        return;
    }

    let path = [];

    if (algorithm === "BFS") {

        path =
            graphSearchBFS(
                startNode.id(),
                targetNode.id()
            );
    }

    else if (algorithm === "DFS") {

        path =
            graphSearchDFS(
                startNode.id(),
                targetNode.id()
            );
    }

    else if (algorithm === "A*") {

        path =
            graphSearchAStar(
                startNode.id(),
                targetNode.id()
            );
    }

    highlightGraphPath(
        path
    );

    const resultElementId =
        algorithm === "BFS"
            ? "bfsResult"
            : algorithm === "DFS"
                ? "dfsResult"
                : "astarResult";

    setText(
        resultElementId,
        formatPath(path)
    );
}


/* =========================================================
   FIND GRAPH NODE
========================================================= */

function findGraphNode(value) {

    if (!graphInstance || !value) {
        return null;
    }

    const normalized =
        normalizeText(value);

    let node =
        graphInstance.nodes().filter(
            element => {

                return (
                    normalizeText(
                        element.id()
                    ) === normalized
                );
            }
        )[0];

    if (node) {
        return node;
    }

    node =
        graphInstance.nodes().filter(
            element => {

                const id =
                    normalizeText(
                        element.id()
                    );

                const label =
                    normalizeText(
                        element.data("label") || ""
                    );

                return (
                    id.includes(normalized) ||
                    normalized.includes(id) ||
                    label.includes(normalized) ||
                    normalized.includes(label)
                );
            }
        )[0];

    return node || null;
}


/* =========================================================
   NORMALIZE TEXT
========================================================= */

function normalizeText(value) {

    return String(value || "")
        .trim()
        .toLowerCase()
        .replace(/\s+/g, " ");
}


/* =========================================================
   GRAPH NEIGHBORS
========================================================= */

function getGraphNeighbors(nodeId) {

    if (!graphInstance) {
        return [];
    }

    const node =
        graphInstance.getElementById(
            nodeId
        );

    if (!node || node.empty()) {
        return [];
    }

    const neighbors = [];

    node.connectedEdges().forEach(edge => {

        const source =
            edge.source().id();

        const target =
            edge.target().id();

        /*
         * This is intentionally treated as an
         * undirected traversal so investigation
         * searches can discover connected evidence
         * even when the displayed relationship is
         * directional.
         */

        if (source === nodeId) {

            neighbors.push(target);

        } else if (target === nodeId) {

            neighbors.push(source);
        }
    });

    return [...new Set(neighbors)];
}


/* =========================================================
   GRAPH BFS
========================================================= */

function graphSearchBFS(
    startId,
    targetId
) {

    if (startId === targetId) {
        return [startId];
    }

    const queue = [
        startId
    ];

    const visited =
        new Set([
            startId
        ]);

    const parent = {};

    while (queue.length) {

        const current =
            queue.shift();

        if (current === targetId) {

            return reconstructPath(
                parent,
                startId,
                targetId
            );
        }

        const neighbors =
            getGraphNeighbors(current);

        neighbors.forEach(next => {

            if (!visited.has(next)) {

                visited.add(next);

                parent[next] =
                    current;

                queue.push(next);
            }
        });
    }

    return [];
}


/* =========================================================
   GRAPH DFS
========================================================= */

function graphSearchDFS(
    startId,
    targetId
) {

    if (startId === targetId) {
        return [startId];
    }

    const stack = [
        startId
    ];

    const visited =
        new Set();

    const parent = {};

    while (stack.length) {

        const current =
            stack.pop();

        if (visited.has(current)) {
            continue;
        }

        visited.add(current);

        if (current === targetId) {

            return reconstructPath(
                parent,
                startId,
                targetId
            );
        }

        const neighbors =
            getGraphNeighbors(current);

        /*
         * Reverse so traversal is deterministic
         * and similar to BFS ordering.
         */

        neighbors
            .slice()
            .reverse()
            .forEach(next => {

                if (!visited.has(next)) {

                    if (!(next in parent)) {

                        parent[next] =
                            current;
                    }

                    stack.push(next);
                }
            });
    }

    return [];
}


/* =========================================================
   GRAPH A*
========================================================= */

function graphSearchAStar(
    startId,
    targetId
) {

    if (startId === targetId) {
        return [startId];
    }

    if (!graphInstance) {
        return [];
    }

    const openSet = [
        startId
    ];

    const cameFrom = {};

    const gScore = {};
    const fScore = {};

    graphInstance.nodes().forEach(node => {

        gScore[node.id()] =
            Infinity;

        fScore[node.id()] =
            Infinity;
    });

    gScore[startId] = 0;

    fScore[startId] =
        heuristicDistance(
            startId,
            targetId
        );

    const closedSet =
        new Set();

    while (openSet.length) {

        openSet.sort(
            (a, b) => {

                if (fScore[a] !== fScore[b]) {
                    return fScore[a] - fScore[b];
                }

                return String(a).localeCompare(
                    String(b)
                );
            }
        );

        const current =
            openSet.shift();

        if (current === targetId) {

            return reconstructPath(
                cameFrom,
                startId,
                targetId
            );
        }

        closedSet.add(current);

        const neighbors =
            getGraphNeighbors(current);

        neighbors.forEach(neighbor => {

            if (closedSet.has(neighbor)) {
                return;
            }

            const tentativeScore =
                gScore[current] + 1;

            if (
                tentativeScore <
                gScore[neighbor]
            ) {

                cameFrom[neighbor] =
                    current;

                gScore[neighbor] =
                    tentativeScore;

                fScore[neighbor] =
                    tentativeScore +
                    heuristicDistance(
                        neighbor,
                        targetId
                    );

                if (
                    !openSet.includes(
                        neighbor
                    )
                ) {

                    openSet.push(
                        neighbor
                    );
                }
            }
        });
    }

    return [];
}


/* =========================================================
   HEURISTIC
========================================================= */

function heuristicDistance(
    nodeA,
    nodeB
) {

    if (!graphInstance) {
        return 0;
    }

    const a =
        graphInstance.getElementById(
            nodeA
        );

    const b =
        graphInstance.getElementById(
            nodeB
        );

    if (
        !a ||
        !b ||
        a.empty() ||
        b.empty()
    ) {
        return 0;
    }

    const positionA =
        a.position();

    const positionB =
        b.position();

    /*
     * Cytoscape coordinates are used only as a
     * heuristic. Every graph edge has cost 1.
     */

    return Math.sqrt(
        Math.pow(
            positionA.x -
            positionB.x,
            2
        ) +
        Math.pow(
            positionA.y -
            positionB.y,
            2
        )
    );
}


/* =========================================================
   RECONSTRUCT PATH
========================================================= */

function reconstructPath(
    parent,
    startId,
    targetId
) {

    const path = [];

    let current =
        targetId;

    const safetyLimit =
        graphInstance
            ? graphInstance.nodes().length + 5
            : 1000;

    let safetyCounter = 0;

    while (
        current !== undefined &&
        current !== null &&
        safetyCounter < safetyLimit
    ) {

        path.unshift(
            current
        );

        if (current === startId) {
            break;
        }

        current =
            parent[current];

        safetyCounter++;
    }

    if (
        path.length === 0 ||
        path[0] !== startId
    ) {

        return [];
    }

    return path;
}


/* =========================================================
   HIGHLIGHT GRAPH PATH
========================================================= */

function highlightGraphPath(path) {

    if (!graphInstance) {
        return;
    }

    graphInstance
        .elements()
        .removeClass(
            "path-node path-edge"
        );

    if (
        !path ||
        path.length === 0
    ) {

        showMessage(
            "investigationMessage",
            "No path found between the selected entities.",
            "error"
        );

        return;
    }


    /* =====================================================
       HIGHLIGHT NODES
    ===================================================== */

    path.forEach(nodeId => {

        const node =
            graphInstance.getElementById(
                nodeId
            );

        if (
            node &&
            !node.empty()
        ) {

            node.addClass(
                "path-node"
            );
        }
    });


    /* =====================================================
       HIGHLIGHT EDGES
    ===================================================== */

    for (
        let i = 0;
        i < path.length - 1;
        i++
    ) {

        const source =
            graphInstance.getElementById(
                path[i]
            );

        const target =
            graphInstance.getElementById(
                path[i + 1]
            );

        if (
            !source ||
            !target ||
            source.empty() ||
            target.empty()
        ) {
            continue;
        }

        const edge =
            source.edgesTo(target)
                .union(
                    target.edgesTo(source)
                );

        edge.addClass(
            "path-edge"
        );
    }


    /* =====================================================
       CENTER PATH
    ===================================================== */

    const pathNodes =
        path
            .map(nodeId =>
                graphInstance.getElementById(
                    nodeId
                )
            )
            .filter(node =>
                node &&
                !node.empty()
            );

    if (pathNodes.length) {

        graphInstance.fit(
            pathNodes,
            70
        );
    }


    showMessage(
        "investigationMessage",
        `Path found: ${path.join(" → ")}`,
        "success"
    );
}


/* =========================================================
   GRAPH
========================================================= */

function renderGraph(graphData) {

    const container =
        document.getElementById(
            "cy"
        );

    if (!container) {
        return;
    }

    if (!graphData) {

        container.innerHTML =
            "<p style='padding:20px'>No graph data available.</p>";

        return;
    }

    if (
        typeof cytoscape ===
        "undefined"
    ) {

        container.innerHTML =
            "<p style='padding:20px'>Cytoscape failed to load.</p>";

        return;
    }


    /* =====================================================
       DESTROY PREVIOUS GRAPH
    ===================================================== */

    if (graphInstance) {

        try {
            graphInstance.destroy();
        }

        catch (error) {
            console.warn(
                "Graph destroy warning:",
                error
            );
        }

        graphInstance =
            null;
    }


    container.innerHTML = "";


    /* =====================================================
       BUILD ELEMENTS
    ===================================================== */

    const elements = [];

    const nodeIds =
        new Set();


    /* =====================================================
       NODES
    ===================================================== */

    (graphData.nodes || [])
        .forEach(node => {

            const nodeId =
                String(
                    node.id
                );

            if (nodeIds.has(nodeId)) {
                return;
            }

            nodeIds.add(nodeId);

            elements.push({

                data: {

                    id:
                        nodeId,

                    label:
                        node.label ||
                        nodeId,

                    type:
                        node.type ||
                        "ENTITY"
                }
            });
        });


    /* =====================================================
       EDGES
    ===================================================== */

    (graphData.edges || [])
        .forEach(
            (edge, index) => {

                const source =
                    String(
                        edge.source
                    );

                const target =
                    String(
                        edge.target
                    );

                /*
                 * Skip invalid edges.
                 */

                if (
                    !nodeIds.has(source) ||
                    !nodeIds.has(target) ||
                    source === target
                ) {
                    return;
                }

                elements.push({

                    data: {

                        id:
                            `edge-${index}`,

                        source:
                            source,

                        target:
                            target,

                        label:
                            String(
                                edge.relation ||
                                ""
                            )
                    }
                });
            }
        );


    /* =====================================================
       CREATE CYTOSCAPE GRAPH
    ===================================================== */

    graphInstance =
        cytoscape({

            container:
                container,

            elements:
                elements,

            minZoom:
                0.2,

            maxZoom:
                3,

            wheelSensitivity:
                0.15,

            layout: {

                name:
                    "cose",

                animate:
                    true,

                animationDuration:
                    500,

                padding:
                    60,

                nodeRepulsion:
                    9000,

                idealEdgeLength:
                    160,

                edgeElasticity:
                    0.25,

                nestingFactor:
                    1.2,

                gravity:
                    0.15
            },


            /* =================================================
               GRAPH STYLE
            ================================================= */

            style: [

                {
                    selector:
                        "node",

                    style: {

                        "background-color":
                            "#2563eb",

                        "label":
                            "data(label)",

                        "color":
                            "#172033",

                        "text-valign":
                            "bottom",

                        "text-halign":
                            "center",

                        "text-margin-y":
                            9,

                        "font-size":
                            11,

                        "font-weight":
                            "bold",

                        "width":
                            42,

                        "height":
                            42,

                        "border-width":
                            3,

                        "border-color":
                            "#dbeafe",

                        "text-wrap":
                            "wrap",

                        "text-max-width":
                            110
                    }
                },


                {
                    selector:
                        "edge",

                    style: {

                        "width":
                            2,

                        "line-color":
                            "#94a3b8",

                        "target-arrow-color":
                            "#64748b",

                        "target-arrow-shape":
                            "triangle",

                        "curve-style":
                            "bezier",

                        "label":
                            "data(label)",

                        "font-size":
                            8,

                        "color":
                            "#475569",

                        "text-background-color":
                            "#ffffff",

                        "text-background-opacity":
                            1,

                        "text-background-padding":
                            3,

                        "text-rotation":
                            "autorotate"
                    }
                },


                {
                    selector:
                        "node.path-node",

                    style: {

                        "background-color":
                            "#16a34a",

                        "border-color":
                            "#166534",

                        "border-width":
                            5,

                        "width":
                            48,

                        "height":
                            48
                    }
                },


                {
                    selector:
                        "edge.path-edge",

                    style: {

                        "line-color":
                            "#16a34a",

                        "target-arrow-color":
                            "#16a34a",

                        "width":
                            5,

                        "z-index":
                            999
                    }
                }

            ]
        });


    /* =====================================================
       GRAPH EVENTS
    ===================================================== */

    graphInstance.on(
        "tap",
        "node",
        event => {

            const node =
                event.target;

            const nodeId =
                node.id();

            const startInput =
                document.getElementById(
                    "startNode"
                );

            const targetInput =
                document.getElementById(
                    "targetNode"
                );

            if (
                startInput &&
                !startInput.value
            ) {

                startInput.value =
                    nodeId;

            }

            else if (
                targetInput &&
                !targetInput.value
            ) {

                targetInput.value =
                    nodeId;

            }

            else if (
                startInput &&
                targetInput
            ) {

                /*
                 * If both fields already contain values,
                 * clicking a node replaces the target.
                 */

                targetInput.value =
                    nodeId;
            }
        }
    );
}


/* =========================================================
   GRAPH ZOOM IN
========================================================= */

function zoomGraphIn() {

    if (!graphInstance) {
        return;
    }

    const currentZoom =
        graphInstance.zoom();

    graphInstance.zoom({

        level:
            Math.min(
                currentZoom * 1.2,
                3
            ),

        renderedPosition: {

            x:
                graphInstance.width() / 2,

            y:
                graphInstance.height() / 2
        }
    });
}


/* =========================================================
   GRAPH ZOOM OUT
========================================================= */

function zoomGraphOut() {

    if (!graphInstance) {
        return;
    }

    const currentZoom =
        graphInstance.zoom();

    graphInstance.zoom({

        level:
            Math.max(
                currentZoom / 1.2,
                0.2
            ),

        renderedPosition: {

            x:
                graphInstance.width() / 2,

            y:
                graphInstance.height() / 2
        }
    });
}


/* =========================================================
   BACKWARD COMPATIBILITY
========================================================= */

function zoomGraph(amount) {

    if (!graphInstance) {
        return;
    }

    if (amount > 0) {
        zoomGraphIn();
    }

    else {
        zoomGraphOut();
    }
}


/* =========================================================
   GRAPH FIT
========================================================= */

function fitGraph() {

    if (!graphInstance) {
        return;
    }

    graphInstance.fit(
        undefined,
        50
    );
}


/* =========================================================
   GRAPH RESET
========================================================= */

function resetGraph() {

    if (!graphInstance) {
        return;
    }

    graphInstance
        .elements()
        .removeClass(
            "path-node path-edge"
        );

    graphInstance.fit(
        undefined,
        50
    );
}


/* =========================================================
   OLD HTML COMPATIBILITY
========================================================= */

function resetGraphZoom() {
    resetGraph();
}


/* =========================================================
   CLEAR GRAPH PATH
========================================================= */

function clearGraphPath() {

    if (!graphInstance) {
        return;
    }

    graphInstance
        .elements()
        .removeClass(
            "path-node path-edge"
        );

    fitGraph();
}


/* =========================================================
   CONFIDENCE DISPLAY
========================================================= */

function displayConfidence(
    confidence,
    explanation
) {

    const formatted =
        formatConfidence(
            confidence
        );


    /* =====================================================
       MAIN CIRCLE
    ===================================================== */

    setText(
        "confidenceCircle",
        formatted
    );


    /* =====================================================
       SMALL CONFIDENCE VALUE
    ===================================================== */

    setText(
        "confidenceValue",
        formatted
    );


    /* =====================================================
       EXPLANATION
    ===================================================== */

    const confidenceExplanation =
        document.getElementById(
            "confidenceExplanation"
        );

    if (confidenceExplanation) {

        if (Array.isArray(explanation)) {

            confidenceExplanation.textContent =
                explanation.length
                    ? explanation.join(" ")
                    : "Confidence calculated from detected entities, relationships and contradictions.";

        }

        else {

            confidenceExplanation.textContent =
                String(
                    explanation || ""
                );
        }
    }


    /* =====================================================
       CIRCLE ACCESSIBILITY
    ===================================================== */

    const circle =
        document.getElementById(
            "confidenceCircle"
        );

    if (circle) {

        circle.setAttribute(
            "aria-label",
            `Bayesian confidence ${formatted}`
        );
    }
}


/* =========================================================
   CONTRADICTIONS
========================================================= */

function displayContradictions(
    contradictions
) {

    const container =
        document.getElementById(
            "contradictionsList"
        );

    if (!container) {
        return;
    }

    container.innerHTML = "";

    if (
        !Array.isArray(contradictions) ||
        contradictions.length === 0
    ) {

        container.innerHTML =
            "<div class='empty-state'>No contradictions detected.</div>";

        return;
    }

    contradictions.forEach(item => {

        const row =
            document.createElement(
                "div"
            );

        row.className =
            "contradiction-item";

        if (
            typeof item === "object"
        ) {

            row.textContent =
                item.message ||
                item.description ||
                JSON.stringify(item);

        }

        else {

            row.textContent =
                String(item);
        }

        container.appendChild(
            row
        );
    });
}


/* =========================================================
   AI EXPLANATION
========================================================= */

function displayExplanation(
    explanation
) {

    const container =
        document.getElementById(
            "explanationList"
        );

    if (!container) {
        return;
    }

    container.innerHTML = "";

    if (
        !Array.isArray(explanation) ||
        explanation.length === 0
    ) {

        const item =
            document.createElement(
                "div"
            );

        item.className =
            "explanation-item";

        item.textContent =
            "AI explanation will appear after investigation analysis.";

        container.appendChild(
            item
        );

        return;
    }

    explanation.forEach((item, index) => {

        const row =
            document.createElement(
                "div"
            );

        row.className =
            "explanation-item";

        if (
            typeof item === "object"
        ) {

            row.textContent =
                item.message ||
                item.explanation ||
                JSON.stringify(item);

        }

        else {

            row.textContent =
                String(item);
        }

        container.appendChild(
            row
        );
    });
}


/* =========================================================
   AUDIT LOGS
========================================================= */

async function loadAuditLogs() {

    const token =
        localStorage.getItem(
            "access_token"
        );

    if (!token) {
        return;
    }

    try {

        const response =
            await fetch(
                `${API}/auth/logs`,
                {
                    method: "GET",

                    headers: {

                        "Authorization":
                            `Bearer ${token}`
                    }
                }
            );

        if (!response.ok) {
            return;
        }

        const data =
            await safeJson(response);

        const logs =
            Array.isArray(data.logs)
                ? data.logs
                : [];

        const logCount =
            document.getElementById(
                "logCount"
            );

        if (logCount) {

            logCount.textContent =
                logs.length;
        }

        const table =
            document.getElementById(
                "auditTable"
            );

        if (!table) {
            return;
        }

        table.innerHTML = "";

        if (!logs.length) {

            table.innerHTML = `

                <tr>

                    <td colspan="5">
                        No audit events found.
                    </td>

                </tr>
            `;

            return;
        }


        logs.forEach(log => {

            const row =
                document.createElement(
                    "tr"
                );

            const date =
                log.created_at
                    ? new Date(
                        log.created_at
                    )
                    : new Date();

            row.innerHTML = `

                <td>
                    ${escapeHtml(
                        date.toLocaleString()
                    )}
                </td>

                <td>

                    <strong>
                        ${escapeHtml(
                            log.action || ""
                        )}
                    </strong>

                </td>

                <td>
                    —
                </td>

                <td>
                    ${escapeHtml(
                        log.details || ""
                    )}
                </td>

                <td>

                    <span class="log-status success">
                        SUCCESS
                    </span>

                </td>
            `;

            table.appendChild(
                row
            );
        });

    }

    catch (error) {

        console.error(
            "Audit log error:",
            error
        );
    }
}


/* =========================================================
   OPEN REPORT
========================================================= */

async function openReport() {

    if (
        !lastInvestigation ||
        !lastInvestigation.report
    ) {

        alert(
            "No report available."
        );

        return;
    }

    const file =
        lastInvestigation
            .report
            .file;

    if (!file) {

        alert(
            "Report file is not available."
        );

        return;
    }

    const fileName =
        String(file)
            .replace(/\\/g, "/")
            .split("/")
            .pop();

    if (!fileName) {

        alert(
            "Invalid report filename."
        );

        return;
    }

    const token =
        localStorage.getItem(
            "access_token"
        );

    const url =
        `${API.replace("/api", "")}/reports/${encodeURIComponent(fileName)}`;

    try {

        const response =
            await fetch(
                url,
                {
                    method: "GET",

                    headers: token
                        ? {
                            "Authorization":
                                `Bearer ${token}`
                        }
                        : {}
                }
            );

        if (!response.ok) {

            throw new Error(
                "Unable to open report."
            );
        }

        const blob =
            await response.blob();

        const blobUrl =
            URL.createObjectURL(
                blob
            );

        window.open(
            blobUrl,
            "_blank"
        );

        setTimeout(() => {

            URL.revokeObjectURL(
                blobUrl
            );

        }, 60000);

    }

    catch (error) {

        console.error(
            "Report error:",
            error
        );

        alert(
            error.message
        );
    }
}


/* =========================================================
   DOWNLOAD REPORT
========================================================= */

async function downloadReport() {

    if (
        !lastInvestigation ||
        !lastInvestigation.report ||
        !lastInvestigation.report.file
    ) {

        alert(
            "No report available."
        );

        return;
    }

    const fileName =
        String(
            lastInvestigation.report.file
        )
            .replace(/\\/g, "/")
            .split("/")
            .pop();

    const token =
        localStorage.getItem(
            "access_token"
        );

    const url =
        `${API.replace("/api", "")}/reports/${encodeURIComponent(fileName)}`;

    try {

        const response =
            await fetch(
                url,
                {
                    headers: token
                        ? {
                            "Authorization":
                                `Bearer ${token}`
                        }
                        : {}
                }
            );

        if (!response.ok) {

            throw new Error(
                "Unable to download report."
            );
        }

        const blob =
            await response.blob();

        const blobUrl =
            URL.createObjectURL(
                blob
            );

        const link =
            document.createElement(
                "a"
            );

        link.href =
            blobUrl;

        link.download =
            fileName;

        document.body.appendChild(
            link
        );

        link.click();

        link.remove();

        setTimeout(() => {

            URL.revokeObjectURL(
                blobUrl
            );

        }, 1000);

    }

    catch (error) {

        console.error(
            "Download report error:",
            error
        );

        alert(
            error.message
        );
    }
}

/* =========================================================
   REGISTER MODAL
========================================================= */

function showRegister() {

    const modal =
        document.getElementById(
            "registerModal"
        );

    if (modal) {

        modal.classList.remove(
            "hidden"
        );
    }
}


function hideRegister() {

    const modal =
        document.getElementById(
            "registerModal"
        );

    if (modal) {

        modal.classList.add(
            "hidden"
        );
    }
}


/* =========================================================
   PASSWORD VISIBILITY
========================================================= */

function togglePassword(
    inputId,
    button
) {

    const input =
        document.getElementById(
            inputId
        );

    if (!input) {
        return;
    }

    if (
        input.type ===
        "password"
    ) {

        input.type =
            "text";

        if (button) {

            button.textContent =
                "Hide";
        }

    } else {

        input.type =
            "password";

        if (button) {

            button.textContent =
                "Show";
        }
    }
}


/* =========================================================
   CHANGE PASSWORD
========================================================= */

async function changePassword() {

    const currentPassword =
        document.getElementById(
            "currentPassword"
        )?.value;

    const newPassword =
        document.getElementById(
            "newPassword"
        )?.value;

    const confirmPassword =
        document.getElementById(
            "confirmPassword"
        )?.value;


    if (
        !currentPassword ||
        !newPassword ||
        !confirmPassword
    ) {

        showMessage(
            "passwordMessage",
            "Please fill all password fields.",
            "error"
        );

        return;
    }


    if (newPassword.length < 8) {

        showMessage(
            "passwordMessage",
            "New password must contain at least 8 characters.",
            "error"
        );

        return;
    }


    if (
        newPassword !==
        confirmPassword
    ) {

        showMessage(
            "passwordMessage",
            "New passwords do not match.",
            "error"
        );

        return;
    }


    const token =
        localStorage.getItem(
            "access_token"
        );

    try {

        const response =
            await fetch(
                `${API}/auth/change-password`,
                {
                    method: "POST",

                    headers: {

                        "Content-Type":
                            "application/json",

                        "Authorization":
                            `Bearer ${token}`
                    },

                    body: JSON.stringify({

                        current_password:
                            currentPassword,

                        new_password:
                            newPassword
                    })
                }
            );

        const data =
            await safeJson(response);

        if (!response.ok) {

            throw new Error(
                data.detail ||
                "Password change failed."
            );
        }

        showMessage(
            "passwordMessage",
            "Password changed successfully.",
            "success"
        );

        clearInput(
            "currentPassword"
        );

        clearInput(
            "newPassword"
        );

        clearInput(
            "confirmPassword"
        );

    }

    catch (error) {

        console.error(
            "Password change error:",
            error
        );

        showMessage(
            "passwordMessage",
            error.message,
            "error"
        );
    }
}


/* =========================================================
   2FA SETUP
========================================================= */

async function setup2FA() {

    const token =
        localStorage.getItem(
            "access_token"
        );

    if (!token) {
        return;
    }

    try {

        const response =
            await fetch(
                `${API}/auth/2fa/setup`,
                {
                    method: "POST",

                    headers: {

                        "Authorization":
                            `Bearer ${token}`
                    }
                }
            );

        const data =
            await safeJson(response);

        if (!response.ok) {

            throw new Error(
                data.detail ||
                "Unable to setup 2FA."
            );
        }


        const secret =
            document.getElementById(
                "twoFASecret"
            );

        if (secret) {

            secret.textContent =
                data.secret ||
                "—";
        }


        const setup =
            document.getElementById(
                "twoFASetup"
            );

        if (setup) {

            setup.classList.remove(
                "hidden"
            );
        }


        /* Show QR if backend returns one */

        const qr =
            document.getElementById(
                "twoFAQr"
            );

        if (
            qr &&
            data.qr_code
        ) {

            qr.src =
                data.qr_code;

            qr.classList.remove(
                "hidden"
            );
        }


        /* Show provisioning URI */

        const uri =
            document.getElementById(
                "twoFAUri"
            );

        if (
            uri &&
            data.otpauth_url
        ) {

            uri.textContent =
                data.otpauth_url;
        }


        showMessage(
            "twoFAMessage",
            "Secret generated. Add it to your authenticator app.",
            "success"
        );

    }

    catch (error) {

        console.error(
            "2FA setup error:",
            error
        );

        showMessage(
            "twoFAMessage",
            error.message,
            "error"
        );
    }
}


/* =========================================================
   ENABLE 2FA
========================================================= */

async function enable2FA() {

    const code =
        document
            .getElementById(
                "twoFACode"
            )
            ?.value
            .trim();

    if (
        !code ||
        !/^\d{6}$/.test(code)
    ) {

        showMessage(
            "twoFAMessage",
            "Enter the 6-digit authenticator code.",
            "error"
        );

        return;
    }

    const token =
        localStorage.getItem(
            "access_token"
        );

    try {

        const response =
            await fetch(
                `${API}/auth/2fa/enable`,
                {
                    method: "POST",

                    headers: {

                        "Content-Type":
                            "application/json",

                        "Authorization":
                            `Bearer ${token}`
                    },

                    body: JSON.stringify({

                        code:
                            code
                    })
                }
            );

        const data =
            await safeJson(response);

        if (!response.ok) {

            throw new Error(
                data.detail ||
                "Unable to enable 2FA."
            );
        }

        showMessage(
            "twoFAMessage",
            "Two-factor authentication enabled successfully.",
            "success"
        );

        clearInput(
            "twoFACode"
        );

        load2FAStatus();

    }

    catch (error) {

        console.error(
            "Enable 2FA error:",
            error
        );

        showMessage(
            "twoFAMessage",
            error.message,
            "error"
        );
    }
}


/* =========================================================
   DISABLE 2FA
========================================================= */

async function disable2FA() {

    const confirmDisable =
        confirm(
            "Are you sure you want to disable 2FA?"
        );

    if (!confirmDisable) {
        return;
    }


    const code =
        prompt(
            "Enter your current 6-digit authenticator code:"
        );

    if (
        !code ||
        !/^\d{6}$/.test(code)
    ) {

        alert(
            "Valid 6-digit 2FA code is required."
        );

        return;
    }


    const token =
        localStorage.getItem(
            "access_token"
        );

    try {

        const response =
            await fetch(
                `${API}/auth/2fa/disable`,
                {
                    method: "POST",

                    headers: {

                        "Content-Type":
                            "application/json",

                        "Authorization":
                            `Bearer ${token}`
                    },

                    body: JSON.stringify({

                        code:
                            code
                    })
                }
            );

        const data =
            await safeJson(response);

        if (!response.ok) {

            throw new Error(
                data.detail ||
                "Unable to disable 2FA."
            );
        }

        showMessage(
            "twoFAMessage",
            "Two-factor authentication disabled.",
            "success"
        );

        load2FAStatus();

    }

    catch (error) {

        console.error(
            "Disable 2FA error:",
            error
        );

        showMessage(
            "twoFAMessage",
            error.message,
            "error"
        );
    }
}


/* =========================================================
   LOAD 2FA STATUS
========================================================= */

async function load2FAStatus() {

    const token =
        localStorage.getItem(
            "access_token"
        );

    if (!token) {
        return;
    }

    try {

        const response =
            await fetch(
                `${API}/auth/2fa/status`,
                {
                    method: "GET",

                    headers: {

                        "Authorization":
                            `Bearer ${token}`
                    }
                }
            );

        if (!response.ok) {
            return;
        }

        const data =
            await safeJson(response);


        const status =
            document.getElementById(
                "twoFAStatus"
            );

        if (status) {

            status.textContent =
                data.enabled
                    ? "Enabled"
                    : "Disabled";
        }


        /* Optional visual class */

        if (status) {

            status.classList.remove(
                "enabled",
                "disabled"
            );

            status.classList.add(
                data.enabled
                    ? "enabled"
                    : "disabled"
            );
        }


        const enableButton =
            document.getElementById(
                "enable2FAButton"
            );

        const disableButton =
            document.getElementById(
                "disable2FAButton"
            );

        if (enableButton) {

            enableButton.classList.toggle(
                "hidden",
                Boolean(data.enabled)
            );
        }

        if (disableButton) {

            disableButton.classList.toggle(
                "hidden",
                !data.enabled
            );
        }

    }

    catch (error) {

        console.error(
            "2FA status error:",
            error
        );
    }
}


/* =========================================================
   FORGOT PASSWORD
========================================================= */

function showForgotPassword() {

    const modal =
        document.getElementById(
            "forgotPasswordModal"
        );

    if (modal) {

        modal.classList.remove(
            "hidden"
        );
    }
}


function hideForgotPassword() {

    const modal =
        document.getElementById(
            "forgotPasswordModal"
        );

    if (modal) {

        modal.classList.add(
            "hidden"
        );
    }
}


/* =========================================================
   REQUEST PASSWORD RESET
========================================================= */

async function requestPasswordReset() {

    const email =
        document
            .getElementById(
                "forgotEmail"
            )
            ?.value
            .trim();

    if (!email) {

        showMessage(
            "forgotMessage",
            "Please enter your email.",
            "error"
        );

        return;
    }

    try {

        const response =
            await fetch(
                `${API}/auth/forgot-password`,
                {
                    method: "POST",

                    headers: {

                        "Content-Type":
                            "application/json"
                    },

                    body: JSON.stringify({

                        email:
                            email
                    })
                }
            );

        const data =
            await safeJson(response);

        if (!response.ok) {

            throw new Error(
                data.detail ||
                "Unable to generate reset token."
            );
        }

        showMessage(
            "forgotMessage",
            data.message ||
            "Reset token generated.",
            "success"
        );


        const resetForm =
            document.getElementById(
                "resetForm"
            );

        if (resetForm) {

            resetForm.classList.remove(
                "hidden"
            );
        }


        if (data.token) {

            const tokenInput =
                document.getElementById(
                    "resetToken"
                );

            if (tokenInput) {

                tokenInput.value =
                    data.token;
            }
        }

    }

    catch (error) {

        console.error(
            "Forgot password error:",
            error
        );

        showMessage(
            "forgotMessage",
            error.message,
            "error"
        );
    }
}


/* =========================================================
   RESET PASSWORD
========================================================= */

async function resetPassword() {

    const token =
        document
            .getElementById(
                "resetToken"
            )
            ?.value
            .trim();

    const password =
        document
            .getElementById(
                "resetNewPassword"
            )
            ?.value;

    const confirmPassword =
        document
            .getElementById(
                "resetConfirmPassword"
            )
            ?.value;


    if (
        !token ||
        !password ||
        !confirmPassword
    ) {

        showMessage(
            "forgotMessage",
            "Please fill all reset fields.",
            "error"
        );

        return;
    }


    if (password.length < 8) {

        showMessage(
            "forgotMessage",
            "Password must contain at least 8 characters.",
            "error"
        );

        return;
    }


    if (
        password !==
        confirmPassword
    ) {

        showMessage(
            "forgotMessage",
            "Passwords do not match.",
            "error"
        );

        return;
    }


    try {

        const response =
            await fetch(
                `${API}/auth/reset-password`,
                {
                    method: "POST",

                    headers: {

                        "Content-Type":
                            "application/json"
                    },

                    body: JSON.stringify({

                        token:
                            token,

                        new_password:
                            password
                    })
                }
            );

        const data =
            await safeJson(response);

        if (!response.ok) {

            throw new Error(
                data.detail ||
                "Password reset failed."
            );
        }


        showMessage(
            "forgotMessage",
            "Password reset successfully. You can now login.",
            "success"
        );


        clearInput(
            "resetToken"
        );

        clearInput(
            "resetNewPassword"
        );

        clearInput(
            "resetConfirmPassword"
        );


        setTimeout(() => {

            hideForgotPassword();

        }, 1500);

    }

    catch (error) {

        console.error(
            "Reset password error:",
            error
        );

        showMessage(
            "forgotMessage",
            error.message,
            "error"
        );
    }
}


/* =========================================================
   SETTINGS - REQUEST RESET
========================================================= */

async function requestResetFromSettings() {

    const email =
        document
            .getElementById(
                "resetEmail"
            )
            ?.value
            .trim();

    if (!email) {

        showMessage(
            "settingsResetMessage",
            "Please enter your email.",
            "error"
        );

        return;
    }


    try {

        const response =
            await fetch(
                `${API}/auth/forgot-password`,
                {
                    method: "POST",

                    headers: {

                        "Content-Type":
                            "application/json"
                    },

                    body: JSON.stringify({

                        email:
                            email
                    })
                }
            );

        const data =
            await safeJson(response);

        if (!response.ok) {

            throw new Error(
                data.detail ||
                "Unable to generate reset token."
            );
        }


        showMessage(
            "settingsResetMessage",
            data.message ||
            "Reset token generated.",
            "success"
        );


        const form =
            document.getElementById(
                "settingsResetForm"
            );

        if (form) {

            form.classList.remove(
                "hidden"
            );
        }


        if (data.token) {

            const tokenInput =
                document.getElementById(
                    "settingsResetToken"
                );

            if (tokenInput) {

                tokenInput.value =
                    data.token;
            }
        }

    }

    catch (error) {

        console.error(
            "Settings reset error:",
            error
        );

        showMessage(
            "settingsResetMessage",
            error.message,
            "error"
        );
    }
}


/* =========================================================
   SETTINGS - COMPLETE RESET
========================================================= */

async function completeResetFromSettings() {

    const token =
        document
            .getElementById(
                "settingsResetToken"
            )
            ?.value
            .trim();

    const password =
        document
            .getElementById(
                "settingsResetPassword"
            )
            ?.value;

    const confirmPassword =
        document
            .getElementById(
                "settingsResetConfirm"
            )
            ?.value;


    if (
        !token ||
        !password ||
        !confirmPassword
    ) {

        showMessage(
            "settingsResetMessage",
            "Please fill all reset fields.",
            "error"
        );

        return;
    }


    if (password.length < 8) {

        showMessage(
            "settingsResetMessage",
            "Password must contain at least 8 characters.",
            "error"
        );

        return;
    }


    if (
        password !==
        confirmPassword
    ) {

        showMessage(
            "settingsResetMessage",
            "Passwords do not match.",
            "error"
        );

        return;
    }


    try {

        const response =
            await fetch(
                `${API}/auth/reset-password`,
                {
                    method: "POST",

                    headers: {

                        "Content-Type":
                            "application/json"
                    },

                    body: JSON.stringify({

                        token:
                            token,

                        new_password:
                            password
                    })
                }
            );

        const data =
            await safeJson(response);

        if (!response.ok) {

            throw new Error(
                data.detail ||
                "Password reset failed."
            );
        }


        showMessage(
            "settingsResetMessage",
            "Password reset successfully.",
            "success"
        );


        clearInput(
            "settingsResetToken"
        );

        clearInput(
            "settingsResetPassword"
        );

        clearInput(
            "settingsResetConfirm"
        );

    }

    catch (error) {

        console.error(
            "Settings password reset error:",
            error
        );

        showMessage(
            "settingsResetMessage",
            error.message,
            "error"
        );
    }
}


/* =========================================================
   MESSAGE
========================================================= */

function showMessage(
    elementId,
    message,
    type
) {

    const element =
        document.getElementById(
            elementId
        );

    if (!element) {
        return;
    }

    element.textContent =
        message;

    element.className =
        `message ${type}`;
}


/* =========================================================
   CONFIDENCE FORMAT
========================================================= */

function formatConfidence(value) {

    if (
        value === null ||
        value === undefined ||
        value === ""
    ) {

        return "—";
    }

    const number =
        Number(value);

    if (Number.isNaN(number)) {
        return "—";
    }


    /*
       Backend normally returns 0.82.
       Display = 82%.
    */

    return (
        Math.round(
            number * 100
        ) + "%"
    );
}


/* =========================================================
   HTML ESCAPE
========================================================= */

function escapeHtml(value) {

    return String(value)

        .replaceAll(
            "&",
            "&amp;"
        )

        .replaceAll(
            "<",
            "&lt;"
        )

        .replaceAll(
            ">",
            "&gt;"
        )

        .replaceAll(
            '"',
            "&quot;"
        )

        .replaceAll(
            "'",
            "&#039;"
        );
}


/* =========================================================
   SET TEXT
========================================================= */

function setText(
    elementId,
    value
) {

    const element =
        document.getElementById(
            elementId
        );

    if (element) {

        element.textContent =
            value;
    }
}


/* =========================================================
   CLEAR INPUT
========================================================= */

function clearInput(
    elementId
) {

    const element =
        document.getElementById(
            elementId
        );

    if (element) {

        element.value =
            "";
    }
}


/* =========================================================
   SAFE JSON
========================================================= */

async function safeJson(response) {

    try {

        return await response.json();

    }

    catch (error) {

        return {
            detail:
                `Server returned HTTP ${response.status}.`
        };
    }
}