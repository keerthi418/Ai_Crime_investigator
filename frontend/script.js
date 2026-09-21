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

    /* -----------------------------------------------------
       Authentication check
    ----------------------------------------------------- */

    if (token) {
        loadCurrentUser();
    } else if (page === "index.html" || page === "") {
        window.location.href = "login.html";
        return;
    }


    /* -----------------------------------------------------
       Login / Register
    ----------------------------------------------------- */

    const loginForm = document.getElementById("loginForm");

    if (loginForm) {
        loginForm.addEventListener("submit", login);
    }


    const registerForm = document.getElementById("registerForm");

    if (registerForm) {
        registerForm.addEventListener("submit", register);
    }


    /* -----------------------------------------------------
       Enter key for graph source / target
    ----------------------------------------------------- */

    const startNodeInput =
        document.getElementById("startNode");

    const targetNodeInput =
        document.getElementById("targetNode");


    if (startNodeInput) {

        startNodeInput.addEventListener(
            "keydown",
            event => {

                if (event.key === "Enter") {

                    event.preventDefault();

                    runSelectedAlgorithm("BFS");
                }
            }
        );
    }


    if (targetNodeInput) {

        targetNodeInput.addEventListener(
            "keydown",
            event => {

                if (event.key === "Enter") {

                    event.preventDefault();

                    runSelectedAlgorithm("BFS");
                }
            }
        );
    }


    /* -----------------------------------------------------
       Initial UI
    ----------------------------------------------------- */

    setInvestigationStatus("ongoing");

    initSettingsAccordion();

    checkSystemHealth();

    setInterval(
        checkSystemHealth,
        30000
    );


    if (token) {
        loadCaseDashboard();
        load2FAStatus();
    }

});


/* =========================================================
   SYSTEM HEALTH
========================================================= */

function checkSystemHealth() {

    const statusElement =
        document.querySelector(".system-status");

    const statusText =
        document.getElementById(
            "systemStatusText"
        );


    if (!statusElement) {
        return;
    }


    fetch(
        `${window.location.origin}/health`,
        {
            method: "GET"
        }
    )
        .then(response => {

            const online = response.ok;


            statusElement.classList.toggle(
                "offline",
                !online
            );


            if (statusText) {

                statusText.textContent =
                    online
                        ? "System Online"
                        : "System Offline";
            }

        })
        .catch(() => {

            statusElement.classList.add(
                "offline"
            );


            if (statusText) {

                statusText.textContent =
                    "System Offline";
            }

        });

}


/* =========================================================
   LOGIN
========================================================= */

async function login(event) {

    event.preventDefault();


    const email =
        document
            .getElementById("loginEmail")
            ?.value
            .trim();


    const password =
        document
            .getElementById("loginPassword")
            ?.value;


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

        const response =
            await fetch(
                `${API}/auth/login`,
                {
                    method: "POST",

                    headers: {
                        "Content-Type":
                            "application/json"
                    },

                    body: JSON.stringify({
                        email: email,
                        password: password
                    })
                }
            );


        const data =
            await safeJson(response);


        if (!response.ok) {

            throw new Error(
                data.detail ||
                "Login failed."
            );
        }


        /* -------------------------------------------------
           2FA REQUIRED
        ------------------------------------------------- */

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

                modal.classList.remove(
                    "hidden"
                );
            }


            const codeInput =
                document.getElementById(
                    "login2FACode"
                );


            if (codeInput) {

                codeInput.focus();
            }


            showMessage(
                "loginMessage",
                "Password accepted. Enter your 2FA code.",
                "success"
            );


            return;
        }


        /* -------------------------------------------------
           NORMAL LOGIN
        ------------------------------------------------- */

        if (data.token) {

            localStorage.setItem(
                "access_token",
                data.token
            );

        }


        if (data.user) {

            localStorage.setItem(
                "user",
                JSON.stringify(
                    data.user
                )
            );

        }


        showMessage(
            "loginMessage",
            "Login successful. Redirecting...",
            "success"
        );


        setTimeout(
            () => {

                window.location.href = "/";

            },
            500
        );


    }
    catch (error) {

        console.error(
            "Login error:",
            error
        );


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

    const codeInput =
        document.getElementById(
            "login2FACode"
        );


    if (!codeInput) {
        return;
    }


    const code =
        codeInput.value.trim();


    if (!/^\d{6}$/.test(code)) {

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

        const response =
            await fetch(
                `${API}/auth/2fa/verify`,
                {
                    method: "POST",

                    headers: {
                        "Content-Type":
                            "application/json"
                    },

                    body: JSON.stringify({
                        challenge_token:
                            pending2FAChallenge,

                        code: code
                    })
                }
            );


        const data =
            await safeJson(response);


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
                JSON.stringify(
                    data.user
                )
            );
        }


        pending2FAChallenge = null;


        showMessage(
            "login2FAMessage",
            "Verification successful.",
            "success"
        );


        setTimeout(
            () => {

                window.location.href =
                    "index.html";

            },
            500
        );

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
            .getElementById(
                "registerUsername"
            )
            ?.value
            .trim();


    const email =
        document
            .getElementById(
                "registerEmail"
            )
            ?.value
            .trim();


    const password =
        document
            .getElementById(
                "registerPassword"
            )
            ?.value;


    if (
        !username ||
        !email ||
        !password
    ) {

        showMessage(
            "registerMessage",
            "Please fill all fields.",
            "error"
        );

        return;
    }


    const passwordError =
        passwordStrengthError(
            password
        );


    if (passwordError) {

        showMessage(
            "registerMessage",
            passwordError,
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

        const response =
            await fetch(
                `${API}/auth/register`,
                {
                    method: "POST",

                    headers: {
                        "Content-Type":
                            "application/json"
                    },

                    body: JSON.stringify({

                        username:
                            username,

                        email:
                            email,

                        password:
                            password

                    })
                }
            );


        const data =
            await safeJson(response);


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
            document.getElementById(
                "registerForm"
            );


        if (form) {
            form.reset();
        }


        setTimeout(
            () => {

                hideRegister();

            },
            1500
        );


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
        localStorage.getItem(
            "access_token"
        );


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

                        Authorization:
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
            await safeJson(
                response
            );


        currentUser =
            data.user;


        updateUserUI();


        await loadAuditLogs();


        await loadCaseDashboard();


        await load2FAStatus();

    }
    catch (error) {

        console.error(
            "Current user error:",
            error
        );

    }

}


/* =========================================================
   UPDATE USER INTERFACE
========================================================= */

function updateUserUI() {

    if (!currentUser) {
        return;
    }


    const username =
        currentUser.username ||
        "Investigator";


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


    Object.keys(
        elements
    ).forEach(id => {

        const element =
            document.getElementById(
                id
            );


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
        localStorage.getItem(
            "access_token"
        );


    try {

        if (token) {

            await fetch(
                `${API}/auth/logout`,
                {
                    method:
                        "POST",

                    headers: {

                        Authorization:
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

    sessionStorage.clear();


    window.location.href =
        "login.html";

}


/* =========================================================
   PAGE NAVIGATION
========================================================= */

function showPage(
    pageName,
    button = null
) {

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
    else {

        const matchingButton =
            [...document.querySelectorAll(
                ".nav-item"
            )].find(item => {

                return (
                    item
                        .getAttribute(
                            "onclick"
                        )
                        ?.includes(
                            `'${pageName}'`
                        )
                );

            });


        if (matchingButton) {

            matchingButton.classList.add(
                "active"
            );

        }

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


    if (
        pageName ===
        "activity"
    ) {

        loadAuditLogs();

    }


    if (
        pageName ===
        "dashboard"
    ) {

        loadCaseDashboard();

    }


    if (
        pageName ===
        "settings"
    ) {

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

function setInvestigationStatus(
    status
) {

    const element =
        document.getElementById(
            "investigationStatus"
        );


    if (!element) {
        return;
    }


    element.classList.remove(
        "ongoing",
        "closed"
    );


    if (
        String(
            status
        ).toLowerCase() ===
        "ongoing"
    ) {

        element.textContent =
            "● INVESTIGATION ONGOING";


        element.classList.add(
            "ongoing"
        );

    }
    else {

        element.textContent =
            "● INVESTIGATION CLOSED";


        element.classList.add(
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
            .getElementById(
                "caseText"
            )
            ?.value
            .trim();


    const caseName =
        document
            .getElementById(
                "caseName"
            )
            ?.value
            .trim() || "";


    const startNode =
        document
            .getElementById(
                "startNode"
            )
            ?.value
            .trim() || "";


    const targetNode =
        document
            .getElementById(
                "targetNode"
            )
            ?.value
            .trim() || "";


    if (!text) {

        showMessage(
            "investigationMessage",
            "Please enter a case description.",
            "error"
        );

        return;
    }


    const token =
        localStorage.getItem(
            "access_token"
        );


    if (!token) {

        showMessage(
            "investigationMessage",
            "Please login before starting an investigation.",
            "error"
        );

        return;
    }


    setInvestigationStatus(
        "ongoing"
    );


    const button =
        document.getElementById(
            "runAnalysisButton"
        );


    if (button) {

        button.disabled =
            true;
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

        const response =
            await fetch(
                `${API}/investigate`,
                {
                    method: "POST",

                    headers: {

                        "Content-Type":
                            "application/json",

                        Authorization:
                            `Bearer ${token}`
                    },

                    body: JSON.stringify({

                        text:
                            text,

                        case_name:
                            caseName,

                        start_node:
                            startNode,

                        target_node:
                            targetNode

                    })
                }
            );


        const data =
            await safeJson(
                response
            );


        if (!response.ok) {

            throw new Error(
                data.detail ||
                "Investigation failed."
            );
        }


        lastInvestigation =
            data;


        localStorage.setItem(
            "last_investigation",
            JSON.stringify(
                data
            )
        );


        displayInvestigation(
            data
        );


        setInvestigationStatus(
            "ongoing"
        );


        showMessage(
            "investigationMessage",
            `Investigation completed successfully. Case ${data.case_id ? "#" + data.case_id : ""} is ONGOING.`,
            "success"
        );


        await loadCaseDashboard();

        await loadAuditLogs();


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
            button.disabled =
                false;
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

function displayInvestigation(
    data
) {

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
        Array.isArray(
            data.entities
        )
            ? data.entities
            : [];


    const relations =
        Array.isArray(
            data.relations
        )
            ? data.relations
            : [];


    const contradictions =
        Array.isArray(
            data.contradictions
        )
            ? data.contradictions
            : [];


    const confidence =
        data.bayesian_confidence ??
        data.confidence ??
        0;


    /* -----------------------------------------------------
       Counters
    ----------------------------------------------------- */

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
        formatConfidence(
            confidence
        )
    );


    setText(
        "resultContradictions",
        contradictions.length
    );


    setText(
        "entityCount",
        entities.length
    );


    /* -----------------------------------------------------
       Content
    ----------------------------------------------------- */

    displayEntities(
        entities
    );


    displayRelations(
        relations
    );


    displayAlgorithms(
        data.search_results ||
        {}
    );


    displayConfidence(
        confidence,
        data.explanation ||
        []
    );


    displayContradictions(
        contradictions
    );


    displayExplanation(
        data.explanation ||
        []
    );


    /* -----------------------------------------------------
       Graph
    ----------------------------------------------------- */

    renderGraph(
        data.graph_data ||
        data.graph
    );


    /* -----------------------------------------------------
       Dashboard latest result
    ----------------------------------------------------- */

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

                        ${entities.length}
                        entities ·

                        ${relations.length}
                        relationships ·

                        ${formatConfidence(
                            confidence
                        )}
                        confidence

                    </span>

                </div>

            </div>
        `;
    }

}


/* =========================================================
   DISPLAY ENTITIES
========================================================= */

function displayEntities(
    entities
) {

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


    entities.forEach(
        entity => {

            const tag =
                document.createElement(
                    "span"
                );


            const type =
                String(
                    entity.type ||
                    "ENTITY"
                )
                    .toLowerCase()
                    .replace(
                        /\s+/g,
                        "-"
                    );


            tag.className =
                `entity-tag ${type}`;


            tag.textContent =
                `${entity.text || ""} · ${entity.type || "ENTITY"}`;


            container.appendChild(
                tag
            );

        }
    );

}


/* =========================================================
   DISPLAY RELATIONS
========================================================= */

function displayRelations(
    relations
) {

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


    relations.forEach(
        relation => {

            const item =
                document.createElement(
                    "div"
                );


            item.className =
                "relation-item";


            const source =
                relation.source ||
                "";


            const target =
                relation.target ||
                "";


            const relationName =
                relation.relation ||
                "related_to";


            const reason =
                relation.reason ||
                relation.evidence ||
                relation.supporting_evidence ||
                "Relationship detected from case evidence.";


            item.innerHTML = `

                <div>

                    <b>
                        ${escapeHtml(
                            source
                        )}
                    </b>

                    →

                    <span>
                        ${escapeHtml(
                            relationName
                        )}
                    </span>

                    →

                    <b>
                        ${escapeHtml(
                            target
                        )}
                    </b>

                </div>


                <div class="relationship-reason">

                    <strong>
                        Relationship Reason
                    </strong>

                    ${escapeHtml(
                        reason
                    )}

                </div>

            `;


            container.appendChild(
                item
            );

        }
    );

}


/* =========================================================
   SEARCH ALGORITHMS
========================================================= */

function displayAlgorithms(
    results
) {

    const legacyStart =
        document
            .getElementById(
                "startNode"
            )
            ?.value
            .trim();

    const legacyTarget =
        document
            .getElementById(
                "targetNode"
            )
            ?.value
            .trim();

    if (
        !legacyStart &&
        !legacyTarget
    ) {

        return;
    }

    const bfs =
        getSearchPath(
            results,
            "BFS"
        );


    const dfs =
        getSearchPath(
            results,
            "DFS"
        );


    const astar =
        getSearchPath(
            results,
            "A*"
        );


    setText(
        "bfsResult",
        formatPath(
            bfs
        )
    );


    setText(
        "dfsResult",
        formatPath(
            dfs
        )
    );


    setText(
        "astarResult",
        formatPath(
            astar
        )
    );

}


/* =========================================================
   SEARCH PATH NORMALIZER
========================================================= */

function getSearchPath(
    results,
    algorithm
) {

    if (
        !results ||
        typeof results !==
            "object"
    ) {

        return [];
    }


    let result =
        results[algorithm];


    if (
        result === undefined &&
        algorithm === "A*"
    ) {

        result =
            results.astar ||
            results.Astar ||
            results.A_STAR ||
            results.a_star;

    }


    if (!result) {
        return [];
    }


    if (
        Array.isArray(
            result
        )
    ) {

        return result;
    }


    if (
        typeof result ===
            "object" &&
        Array.isArray(
            result.path
        )
    ) {

        return result.path;
    }


    return [];
}


/* =========================================================
   FORMAT PATH
========================================================= */

function formatPath(
    path
) {

    if (
        !Array.isArray(
            path
        ) ||
        path.length === 0
    ) {

        return "No path found";
    }


    return path
        .map(item =>
            String(item)
        )
        .join(
            " → "
        );
}


/* =========================================================
   MANUAL ALGORITHM RUNNER
========================================================= */

function runSelectedAlgorithm(
    algorithm
) {

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
            .getElementById(
                "startNode"
            )
            ?.value
            .trim();


    const target =
        document
            .getElementById(
                "targetNode"
            )
            ?.value
            .trim();


    if (!start || !target) {

        showMessage(
            "investigationMessage",
            "Enter both Start Entity and Target Entity.",
            "error"
        );

        return;
    }


    const startNode =
        findGraphNode(
            start
        );


    const targetNode =
        findGraphNode(
            target
        );


    if (
        !startNode ||
        !targetNode
    ) {

        showMessage(
            "investigationMessage",
            "Start or target entity was not found in the graph.",
            "error"
        );

        return;
    }


    let path = [];


    if (
        algorithm ===
        "BFS"
    ) {

        path =
            graphSearchBFS(
                startNode.id(),
                targetNode.id()
            );

    }
    else if (
        algorithm ===
        "DFS"
    ) {

        path =
            graphSearchDFS(
                startNode.id(),
                targetNode.id()
            );

    }
    else if (
        algorithm ===
        "A*"
    ) {

        path =
            graphSearchAStar(
                startNode.id(),
                targetNode.id()
            );

    }


    highlightGraphPath(
        path
    );


    const elementId =
        algorithm === "BFS"
            ? "bfsResult"
            : algorithm === "DFS"
                ? "dfsResult"
                : "astarResult";


    setText(
        elementId,
        formatPath(
            path
        )
    );

}


/* =========================================================
   GRAPH PATH RUNNER
   Runs BFS / DFS / A* on the loaded cytoscape graph.
   Wired to the "Run Search" button in the Graph Search panel.
========================================================= */

function runGraphPathSearch() {

    const sourceSelect =
        document.getElementById(
            "searchStartNode"
        );

    const targetSelect =
        document.getElementById(
            "searchTargetNode"
        );

    const algorithmSelect =
        document.getElementById(
            "searchAlgorithm"
        );

    const sourceId =
        sourceSelect
            ? sourceSelect.value
            : "";

    const targetId =
        targetSelect
            ? targetSelect.value
            : "";

    const algorithm =
        algorithmSelect
            ? algorithmSelect.value
            : "BFS";

    const sourceValue =
        sourceSelect
            ? sourceSelect
                .options[sourceSelect.selectedIndex]
                .textContent
                .trim()
            : "";

    const targetValue =
        targetSelect
            ? targetSelect
                .options[targetSelect.selectedIndex]
                .textContent
                .trim()
            : "";

    console.log(
        "SEARCH SOURCE",
        sourceValue
    );

    console.log(
        "SEARCH DESTINATION",
        targetValue
    );

    console.log(
        "SEARCH ALGORITHM",
        algorithm
    );

    console.log(
        "SEARCH GRAPH",
        graphInstance
    );

    if (!graphInstance) {

        setText(
            "searchResultDetails",
            "No graph loaded. Run an investigation first."
        );

        return;
    }

    if (!sourceId || !targetId) {

        setText(
            "searchResultDetails",
            "Please select both a source and a destination node."
        );

        return;
    }

    const sourceNode =
        findGraphNode(
            sourceValue
        );

    const targetNode =
        findGraphNode(
            targetValue
        );

    if (
        !sourceNode ||
        !targetNode
    ) {

        setText(
            "searchResultDetails",
            "Source or destination node not found on the current graph."
        );

        return;
    }

    const bfsPath =
        graphSearchBFS(
            sourceId,
            targetId
        );

    const dfsPath =
        graphSearchDFS(
            sourceId,
            targetId
        );

    const astarPath =
        graphSearchAStar(
            sourceId,
            targetId
        );

    setText(
        "bfsResult",
        formatPath(
            bfsPath
        )
    );

    setText(
        "dfsResult",
        formatPath(
            dfsPath
        )
    );

    setText(
        "astarResult",
        formatPath(
            astarPath
        )
    );

    switch (
        algorithm
    ) {

        case "DFS":
            highlightGraphPath(
                dfsPath
            );

            break;

        case "A*":
            highlightGraphPath(
                astarPath
            );

            break;

        case "BFS":
        default:
            highlightGraphPath(
                bfsPath
            );

            break;

    }

    const selectedPath =
        algorithm === "DFS"
            ? dfsPath
            : algorithm === "A*"
                ? astarPath
                : bfsPath;

    setText(
        "searchResultDetails",
        selectedPath.length === 0
            ? "Path not found between the selected nodes for " +
                algorithm +
                "."
            : "Path found with " +
                algorithm +
                ": " +
                formatPath(
                    selectedPath
                )
    );
}


/* =========================================================
   GRAPH SEARCH
========================================================= */

function findGraphNode(
    value
) {

    if (
        !graphInstance ||
        !value
    ) {

        return null;
    }


    const normalized =
        normalizeText(
            value
        );


    const exact =
        graphInstance
            .nodes()
            .filter(
                node => {

                    return (
                        normalizeText(
                            node.id()
                        ) ===
                        normalized
                    );

                }
            );


    if (
        exact.length
    ) {

        return exact[0];
    }


    const partial =
        graphInstance
            .nodes()
            .filter(
                node => {

                    const id =
                        normalizeText(
                            node.id()
                        );


                    const label =
                        normalizeText(
                            node.data(
                                "label"
                            ) ||
                            ""
                        );


                    return (
                        id.includes(
                            normalized
                        ) ||
                        normalized.includes(
                            id
                        ) ||
                        label.includes(
                            normalized
                        ) ||
                        normalized.includes(
                            label
                        )
                    );

                }
            );


    return partial.length
        ? partial[0]
        : null;
}


/* =========================================================
   NORMALIZE TEXT
========================================================= */

function normalizeText(
    value
) {

    return String(
        value ||
        ""
    )
        .trim()
        .toLowerCase()
        .replace(
            /\s+/g,
            " "
        );
}


/* =========================================================
   GRAPH NEIGHBORS
========================================================= */

function getGraphNeighbors(
    nodeId
) {

    if (!graphInstance) {
        return [];
    }


    const node =
        graphInstance.getElementById(
            nodeId
        );


    if (
        !node ||
        node.empty()
    ) {

        return [];
    }


    const neighbors = [];


    node
        .connectedEdges()
        .forEach(
            edge => {

                const source =
                    edge.source()
                        .id();


                const target =
                    edge.target()
                        .id();


                /*
                 * Treat relationships as connected
                 * for investigation traversal.
                 */

                if (
                    source ===
                    nodeId
                ) {

                    neighbors.push(
                        target
                    );

                }
                else if (
                    target ===
                    nodeId
                ) {

                    neighbors.push(
                        source
                    );

                }

            }
        );


    return [
        ...new Set(
            neighbors
        )
    ];
}


/* =========================================================
   BFS
========================================================= */

function graphSearchBFS(
    startId,
    targetId
) {

    if (
        startId ===
        targetId
    ) {

        return [
            startId
        ];
    }


    const queue = [
        startId
    ];


    const visited =
        new Set([
            startId
        ]);


    const parent = {};


    while (
        queue.length
    ) {

        const current =
            queue.shift();


        if (
            current ===
            targetId
        ) {

            return reconstructPath(
                parent,
                startId,
                targetId
            );
        }


        const neighbors =
            getGraphNeighbors(
                current
            );


        neighbors.forEach(
            next => {

                if (
                    visited.has(
                        next
                    )
                ) {

                    return;
                }


                visited.add(
                    next
                );


                parent[next] =
                    current;


                queue.push(
                    next
                );

            }
        );
    }


    return [];
}


/* =========================================================
   DFS
========================================================= */

function graphSearchDFS(
    startId,
    targetId
) {

    if (
        startId ===
        targetId
    ) {

        return [
            startId
        ];
    }


    const stack = [
        startId
    ];


    const visited =
        new Set();


    const parent = {};


    while (
        stack.length
    ) {

        const current =
            stack.pop();


        if (
            visited.has(
                current
            )
        ) {

            continue;
        }


        visited.add(
            current
        );


        if (
            current ===
            targetId
        ) {

            return reconstructPath(
                parent,
                startId,
                targetId
            );
        }


        const neighbors =
            getGraphNeighbors(
                current
            );


        neighbors
            .slice()
            .reverse()
            .forEach(
                next => {

                    if (
                        !visited.has(
                            next
                        )
                    ) {

                        if (
                            !(next in parent)
                        ) {

                            parent[next] =
                                current;
                        }


                        stack.push(
                            next
                        );

                    }

                }
            );
    }


    return [];
}


/* =========================================================
   A*
========================================================= */

function graphSearchAStar(
    startId,
    targetId
) {

    if (
        startId ===
        targetId
    ) {

        return [
            startId
        ];
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


    graphInstance
        .nodes()
        .forEach(
            node => {

                gScore[
                    node.id()
                ] = Infinity;


                fScore[
                    node.id()
                ] = Infinity;

            }
        );


    gScore[
        startId
    ] = 0;


    fScore[
        startId
    ] =
        heuristicDistance(
            startId,
            targetId
        );


    const closedSet =
        new Set();


    while (
        openSet.length
    ) {

        openSet.sort(
            (a, b) =>
                fScore[a] -
                fScore[b]
        );


        const current =
            openSet.shift();


        if (
            current ===
            targetId
        ) {

            return reconstructPath(
                cameFrom,
                startId,
                targetId
            );
        }


        closedSet.add(
            current
        );


        const neighbors =
            getGraphNeighbors(
                current
            );


        neighbors.forEach(
            neighbor => {

                if (
                    closedSet.has(
                        neighbor
                    )
                ) {

                    return;
                }


                const tentative =
                    gScore[current] +
                    1;


                if (
                    tentative <
                    gScore[neighbor]
                ) {

                    cameFrom[
                        neighbor
                    ] =
                        current;


                    gScore[
                        neighbor
                    ] =
                        tentative;


                    fScore[
                        neighbor
                    ] =
                        tentative +
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

            }
        );
    }


    return [];
}


/* =========================================================
   A* HEURISTIC
========================================================= */

function heuristicDistance(
    nodeA,
    nodeB
) {

    if (!graphInstance) {
        return 0;
    }


    const first =
        graphInstance.getElementById(
            nodeA
        );


    const second =
        graphInstance.getElementById(
            nodeB
        );


    if (
        first.empty() ||
        second.empty()
    ) {

        return 0;
    }


    const a =
        first.position();


    const b =
        second.position();


    return Math.sqrt(

        Math.pow(
            a.x - b.x,
            2
        ) +

        Math.pow(
            a.y - b.y,
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


    const limit =
        graphInstance
            ? graphInstance
                .nodes()
                .length + 5
            : 1000;


    let counter = 0;


    while (
        current !== undefined &&
        current !== null &&
        counter < limit
    ) {

        path.unshift(
            current
        );


        if (
            current ===
            startId
        ) {

            break;
        }


        current =
            parent[current];


        counter++;
    }


    if (
        !path.length ||
        path[0] !== startId
    ) {

        return [];
    }


    return path;
}


/* =========================================================
   HIGHLIGHT PATH
========================================================= */

function highlightGraphPath(
    path
) {

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

        return;
    }


    path.forEach(
        nodeId => {

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

        }
    );


    for (
        let index = 0;
        index <
        path.length - 1;
        index++
    ) {

        const source =
            graphInstance.getElementById(
                path[index]
            );


        const target =
            graphInstance.getElementById(
                path[index + 1]
            );


        if (
            source.empty() ||
            target.empty()
        ) {

            continue;
        }


        const edge =
            source
                .edgesTo(target)
                .union(
                    target.edgesTo(source)
                );


        edge.addClass(
            "path-edge"
        );

    }


    const nodes =
        path
            .map(
                nodeId =>
                    graphInstance.getElementById(
                        nodeId
                    )
            )
            .filter(
                node =>
                    node &&
                    !node.empty()
            );


    if (nodes.length) {

        graphInstance.fit(
            nodes,
            70
        );

    }

}


/* =========================================================
   THE ONLY GRAPH RENDERER
========================================================= */

function renderGraph(
    graphData
) {

    const container =
        document.getElementById(
            "cy"
        );


    if (!container) {
        return;
    }


    /* -----------------------------------------------------
       Destroy previous graph
    ----------------------------------------------------- */

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


    /* -----------------------------------------------------
       Library check
    ----------------------------------------------------- */

    if (
        typeof cytoscape ===
        "undefined"
    ) {

        container.innerHTML = `
            <div style="
                height:100%;
                display:flex;
                align-items:center;
                justify-content:center;
                color:#ef4444;
                font-size:13px;
            ">
                Cytoscape library failed to load.
            </div>
        `;

        return;
    }


    /* -----------------------------------------------------
       Data validation
    ----------------------------------------------------- */

    if (
        !graphData ||
        !Array.isArray(
            graphData.nodes
        )
    ) {

        container.innerHTML = `
            <div style="
                height:100%;
                display:flex;
                align-items:center;
                justify-content:center;
                color:#64748b;
                font-size:13px;
            ">
                No graph data available.
            </div>
        `;

        return;
    }


    const startValue =
        document
            .getElementById(
                "startNode"
            )
            ?.value
            .trim() || "";


    const targetValue =
        document
            .getElementById(
                "targetNode"
            )
            ?.value
            .trim() || "";


    const startLower =
        startValue.toLowerCase();


    const targetLower =
        targetValue.toLowerCase();


    const elements = [];

    const nodeIds =
        new Set();


    /* -----------------------------------------------------
       NORMALIZE NODES
    ----------------------------------------------------- */

    graphData.nodes.forEach(
        rawNode => {

            /*
             * Supports BOTH:
             *
             * { id, label, type }
             *
             * and:
             *
             * { data: { id, label, type } }
             */

            const node =
                rawNode &&
                rawNode.data
                    ? rawNode.data
                    : rawNode;


            if (!node) {
                return;
            }


            const rawId =
                node.id ??
                node.name ??
                "";


            const nodeId =
                String(
                    rawId
                ).trim();


            /*
             * THIS prevents the "undefined" node.
             */

            if (!nodeId) {
                return;
            }


            if (
                nodeId.toLowerCase() ===
                "undefined"
            ) {

                return;
            }


            if (
                nodeId.toLowerCase() ===
                "null"
            ) {

                return;
            }


            if (
                nodeIds.has(
                    nodeId
                )
            ) {

                return;
            }


            nodeIds.add(
                nodeId
            );


            const label =
                String(
                    node.label ??
                    nodeId
                );


            const type =
                String(
                    node.type ??
                    "PERSON"
                ).toUpperCase();


            let role =
                "normal";


            if (
                nodeId.toLowerCase() ===
                startLower
            ) {

                role =
                    "start";

            }
            else if (
                nodeId.toLowerCase() ===
                targetLower
            ) {

                role =
                    "target";
            }


            elements.push({

                data: {

                    id:
                        nodeId,

                    label:
                        label,

                    fullLabel:
                        label,

                    nodeType:
                        type,

                    role:
                        role

                }

            });

        }
    );


    /* -----------------------------------------------------
       NORMALIZE EDGES
    ----------------------------------------------------- */

    if (
        Array.isArray(
            graphData.edges
        )
    ) {

        graphData.edges.forEach(
            (rawEdge, index) => {

                const edge =
                    rawEdge &&
                    rawEdge.data
                        ? rawEdge.data
                        : rawEdge;


                if (!edge) {
                    return;
                }


                const source =
                    String(
                        edge.source ??
                        ""
                    ).trim();


                const target =
                    String(
                        edge.target ??
                        ""
                    ).trim();


                /*
                 * Invalid edge = skip
                 */

                if (
                    !source ||
                    !target
                ) {

                    return;
                }


                /*
                 * Ensure endpoints exist.
                 */

                if (
                    !nodeIds.has(
                        source
                    )
                ) {

                    nodeIds.add(
                        source
                    );


                    elements.push({

                        data: {

                            id:
                                source,

                            label:
                                source,

                            fullLabel:
                                source,

                            nodeType:
                                "PERSON",

                            role:
                                source.toLowerCase() ===
                                startLower
                                    ? "start"
                                    : "normal"

                        }

                    });

                }


                if (
                    !nodeIds.has(
                        target
                    )
                ) {

                    nodeIds.add(
                        target
                    );


                    elements.push({

                        data: {

                            id:
                                target,

                            label:
                                target,

                            fullLabel:
                                target,

                            nodeType:
                                "PERSON",

                            role:
                                target.toLowerCase() ===
                                targetLower
                                    ? "target"
                                    : "normal"

                        }

                    });

                }


                const relation =
                    String(
                        edge.relation ??
                        edge.label ??
                        "related"
                    );


                const reason =
                    String(
                        edge.reason ??
                        edge.evidence ??
                        edge.supporting_evidence ??
                        "Relationship detected from case evidence."
                    );


                elements.push({

                    data: {

                        id:
                            `edge-${index}`,

                        source:
                            source,

                        target:
                            target,

                        label:
                            relation,

                        relation:
                            relation,

                        reason:
                            reason

                    }

                });

            }
        );

    }


    /* -----------------------------------------------------
       If no elements
    ----------------------------------------------------- */

    if (!elements.length) {

        container.innerHTML = `
            <div style="
                height:100%;
                display:flex;
                align-items:center;
                justify-content:center;
                color:#64748b;
                font-size:13px;
            ">
                No valid entities were returned by the backend.
            </div>
        `;

        return;
    }


    /* -----------------------------------------------------
       CREATE GRAPH
    ----------------------------------------------------- */

    graphInstance =
        cytoscape({

            container:
                container,

            elements:
                elements,

            minZoom:
                0.2,

            maxZoom:
                3.5,

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
                    70,

                nodeRepulsion:
                    9000,

                idealEdgeLength:
                    160,

                edgeElasticity:
                    0.25,

                gravity:
                    0.15
            },


            style: [

                /* -----------------------------------------
                   BASE NODE
                ----------------------------------------- */

                {

                    selector:
                        "node",

                    style: {

                        "background-color":
                            "#64748b",

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
                            45,

                        "height":
                            45,

                        "border-width":
                            3,

                        "border-color":
                            "#dbeafe",

                        "text-wrap":
                            "wrap",

                        "text-max-width":
                            115
                    }

                },


                /* -----------------------------------------
                   PERSON
                ----------------------------------------- */

                {

                    selector:
                        'node[nodeType="PERSON"]',

                    style: {

                        "shape":
                            "ellipse",

                        "background-color":
                            "#2563eb",

                        "border-color":
                            "#bfdbfe"

                    }

                },


                /* -----------------------------------------
                   EVIDENCE
                ----------------------------------------- */

                {

                    selector:
                        'node[nodeType="EVIDENCE"]',

                    style: {

                        "shape":
                            "roundrectangle",

                        "background-color":
                            "#f59e0b",

                        "border-color":
                            "#fde68a",

                        "width":
                            95,

                        "height":
                            58

                    }

                },


                /* -----------------------------------------
                   LOCATION
                ----------------------------------------- */

                {

                    selector:
                        'node[nodeType="LOCATION"]',

                    style: {

                        "shape":
                            "diamond",

                        "background-color":
                            "#7c3aed",

                        "border-color":
                            "#ddd6fe"

                    }

                },


                /* -----------------------------------------
                   DATE
                ----------------------------------------- */

                {

                    selector:
                        'node[nodeType="DATE"]',

                    style: {

                        "shape":
                            "hexagon",

                        "background-color":
                            "#0891b2",

                        "border-color":
                            "#bae6fd"

                    }

                },


                /* -----------------------------------------
                   START
                ----------------------------------------- */

                {

                    selector:
                        'node[role="start"]',

                    style: {

                        "background-color":
                            "#16a34a",

                        "border-color":
                            "#166534",

                        "border-width":
                            5,

                        "width":
                            60,

                        "height":
                            60

                    }

                },


                /* -----------------------------------------
                   TARGET
                ----------------------------------------- */

                {

                    selector:
                        'node[role="target"]',

                    style: {

                        "background-color":
                            "#dc2626",

                        "border-color":
                            "#991b1b",

                        "border-width":
                            5,

                        "width":
                            60,

                        "height":
                            60

                    }

                },


                /* -----------------------------------------
                   EDGE
                ----------------------------------------- */

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
                            9,

                        "font-weight":
                            "bold",

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


                /* -----------------------------------------
                   PATH NODE
                ----------------------------------------- */

                {

                    selector:
                        "node.path-node",

                    style: {

                        "border-color":
                            "#111827",

                        "border-width":
                            5

                    }

                },


                /* -----------------------------------------
                   PATH EDGE
                ----------------------------------------- */

                {

                    selector:
                        "edge.path-edge",

                    style: {

                        "line-color":
                            "#16a34a",

                        "target-arrow-color":
                            "#16a34a",

                        "width":
                            5

                    }

                }

            ]

        });


    /* -----------------------------------------------------
       Automatic BFS highlighting from backend
    ----------------------------------------------------- */

    const backendBfs =
        lastInvestigation
            ?.search_results
            ?.BFS;


    if (
        Array.isArray(
            backendBfs
        ) &&
        backendBfs.length > 1
    ) {

        highlightGraphPath(
            backendBfs
        );

    }


    /* -----------------------------------------------------
       NODE CLICK
    ----------------------------------------------------- */

    graphInstance.on(
        "tap",
        "node",
        event => {

            const node =
                event.target;


            const nodeId =
                node.data(
                    "fullLabel"
                );


            const nodeType =
                node.data(
                    "nodeType"
                );


            const role =
                node.data(
                    "role"
                );


            let message =
                `${node.degree()} relationship connection(s) in the graph.`;


            if (
                role ===
                "start"
            ) {

                message =
                    "Selected START entity.";

            }
            else if (
                role ===
                "target"
            ) {

                message =
                    "Selected TARGET entity.";

            }


            showGraphInsight({

                title:
                    nodeId,

                type:
                    nodeType,

                message:
                    message

            });

        }
    );


    /* -----------------------------------------------------
       EDGE CLICK
    ----------------------------------------------------- */

    graphInstance.on(
        "tap",
        "edge",
        event => {

            const edge =
                event.target;


            const source =
                edge
                    .source()
                    .data(
                        "fullLabel"
                    );


            const target =
                edge
                    .target()
                    .data(
                        "fullLabel"
                    );


            const relation =
                edge.data(
                    "relation"
                );


            const reason =
                edge.data(
                    "reason"
                );


            showGraphInsight({

                title:
                    `${source} → ${target}`,

                type:
                    "RELATIONSHIP",

                message:
                    `${relation}. ${reason}`

            });

        }
    );


    /* -----------------------------------------------------
       Fit graph
    ----------------------------------------------------- */

    setTimeout(
        () => {

            if (graphInstance) {

                graphInstance.fit(
                    graphInstance.elements(),
                    60
                );

            }

        },
        200
    );


    /* -----------------------------------------------------
       Search dropdowns
    ----------------------------------------------------- */

    populateSearchSelects();

}


/* =========================================================
   GRAPH INSIGHT
========================================================= */

function showGraphInsight(
    information
) {

    const panel =
        document.getElementById(
            "graphInsight"
        );


    if (!panel) {
        return;
    }


    panel.innerHTML = `

        <strong>
            ${escapeHtml(
                information.title ||
                "Graph Item"
            )}
        </strong>

        <div class="graph-insight-type">
            ${escapeHtml(
                information.type ||
                "ENTITY"
            )}
        </div>

        <div class="graph-insight-message">

            ${escapeHtml(
                information.message ||
                ""
            )}

        </div>

    `;

}


/* =========================================================
   GRAPH SEARCH DROPDOWNS
========================================================= */

function populateSearchSelects() {

    const source =
        document.getElementById(
            "searchStartNode"
        );


    const target =
        document.getElementById(
            "searchTargetNode"
        );


    const selects =
        [
            source,
            target
        ];


    selects.forEach(
        select => {

            if (!select) {
                return;
            }


            select.innerHTML =
                "";


            select.appendChild(
                optionElement(
                    "",
                    "Select a node"
                )
            );


            if (
                !graphInstance ||
                !graphInstance.nodes().length
            ) {

                return;
            }


            graphInstance
                .nodes()
                .forEach(
                    node => {

                        const id =
                            node.id();


                        const label =
                            node.data(
                                "label"
                            ) ||
                            id;


                        select.appendChild(
                            optionElement(
                                id,
                                label
                            )
                        );

                    }
                );

        }
    );

}


/* =========================================================
   OPTION
========================================================= */

function optionElement(
    value,
    text
) {

    const option =
        document.createElement(
            "option"
        );


    option.value =
        value;


    option.textContent =
        text;


    return option;

}


/* =========================================================
   GRAPH ZOOM IN
========================================================= */

function zoomGraphIn() {

    if (!graphInstance) {
        return;
    }


    const current =
        graphInstance.zoom();


    graphInstance.zoom({

        level:
            Math.min(
                current * 1.2,
                3.5
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


    const current =
        graphInstance.zoom();


    graphInstance.zoom({

        level:
            Math.max(
                current / 1.2,
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
   FIT GRAPH
========================================================= */

function fitGraph() {

    if (!graphInstance) {
        return;
    }


    graphInstance.fit(
        graphInstance.elements(),
        60
    );

}


/* =========================================================
   RESET GRAPH
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
        graphInstance.elements(),
        60
    );

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
   MANUAL GRAPH REBUILD
========================================================= */

function rebuildGraph() {

    if (
        !lastInvestigation
    ) {

        const stored =
            localStorage.getItem(
                "last_investigation"
            );


        if (stored) {

            try {

                lastInvestigation =
                    JSON.parse(
                        stored
                    );

            }
            catch (error) {

                console.error(
                    error
                );

            }

        }

    }


    if (!lastInvestigation) {

        showMessage(
            "investigationMessage",
            "No investigation data available.",
            "error"
        );

        return;
    }


    renderGraph(
        lastInvestigation.graph_data ||
        lastInvestigation.graph
    );

}


/* =========================================================
   CONFIDENCE
========================================================= */

function displayConfidence(
    confidence,
    explanation
) {

    const formatted =
        formatConfidence(
            confidence
        );


    setText(
        "confidenceValue",
        formatted
    );


    setText(
        "resultConfidence",
        formatted
    );


    const explanationElement =
        document.getElementById(
            "confidenceExplanation"
        );


    if (
        explanationElement
    ) {

        if (
            Array.isArray(
                explanation
            )
        ) {

            explanationElement.textContent =
                explanation.length
                    ? explanation.join(" ")
                    : "Confidence calculated from the extracted investigation evidence.";

        }
        else {

            explanationElement.textContent =
                String(
                    explanation ||
                    "Confidence calculated from the extracted investigation evidence."
                );

        }

    }


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


    container.innerHTML =
        "";


    if (
        !Array.isArray(
            contradictions
        ) ||
        contradictions.length ===
            0
    ) {

        container.innerHTML = `

            <div class="empty-state">

                No contradictions detected.

            </div>
        `;

        return;
    }


    contradictions.forEach(
        item => {

            const row =
                document.createElement(
                    "div"
                );


            row.className =
                "contradiction-item";


            row.textContent =
                typeof item ===
                    "object"
                    ? (
                        item.message ||
                        item.description ||
                        JSON.stringify(
                            item
                        )
                    )
                    : String(
                        item
                    );


            container.appendChild(
                row
            );

        }
    );

}


/* =========================================================
   EXPLANATION
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


    container.innerHTML =
        "";


    if (
        !Array.isArray(
            explanation
        ) ||
        explanation.length ===
            0
    ) {

        container.innerHTML = `

            <div class="explanation-item">

                No explanation available.

            </div>

        `;

        return;
    }


    explanation.forEach(
        item => {

            const row =
                document.createElement(
                    "div"
                );


            row.className =
                "explanation-item";


            row.textContent =
                typeof item ===
                    "object"
                    ? (
                        item.message ||
                        item.explanation ||
                        JSON.stringify(
                            item
                        )
                    )
                    : String(
                        item
                    );


            container.appendChild(
                row
            );

        }
    );

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

                        Authorization:
                            `Bearer ${token}`
                    }
                }
            );


        if (!response.ok) {
            return;
        }


        const data =
            await safeJson(
                response
            );


        const logs =
            Array.isArray(
                data.logs
            )
                ? data.logs
                : [];


        setText(
            "logCount",
            logs.length
        );


        const table =
            document.getElementById(
                "auditTable"
            );


        if (!table) {
            return;
        }


        table.innerHTML =
            "";


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


        logs.forEach(
            log => {

                const row =
                    document.createElement(
                        "tr"
                    );


                const date =
                    log.created_at
                        ? new Date(
                            log.created_at
                        )
                        : null;


                const failed =
                    /FAILED|ERROR/i.test(
                        String(
                            log.action ||
                            ""
                        )
                    );


                row.innerHTML = `

                    <td>
                        ${
                            date
                                ? escapeHtml(
                                    date.toLocaleString()
                                )
                                : "—"
                        }
                    </td>

                    <td>

                        <strong>
                            ${escapeHtml(
                                log.action ||
                                ""
                            )}
                        </strong>

                    </td>

                    <td>
                        ${escapeHtml(
                            currentUser?.username ||
                            "—"
                        )}
                    </td>

                    <td>
                        ${escapeHtml(
                            log.details ||
                            ""
                        )}
                    </td>

                    <td>

                        <span class="log-status ${
                            failed
                                ? "failed"
                                : "success"
                        }">

                            ${
                                failed
                                    ? "FAILED"
                                    : "SUCCESS"
                            }

                        </span>

                    </td>

                `;


                table.appendChild(
                    row
                );

            }
        );

    }
    catch (error) {

        console.error(
            "Audit log error:",
            error
        );

    }

}


/* =========================================================
   REPORT
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
        String(
            file
        )
            .replace(
                /\\/g,
                "/"
            )
            .split(
                "/"
            )
            .pop();


    const token =
        localStorage.getItem(
            "access_token"
        );


    const url =
        `${window.location.origin}/reports/${encodeURIComponent(fileName)}`;


    try {

        const response =
            await fetch(
                url,
                {
                    headers: token
                        ? {
                            Authorization:
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


        const objectUrl =
            URL.createObjectURL(
                blob
            );


        window.open(
            objectUrl,
            "_blank"
        );


        setTimeout(
            () => {

                URL.revokeObjectURL(
                    objectUrl
                );

            },
            60000
        );

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
            lastInvestigation
                .report
                .file
        )
            .replace(
                /\\/g,
                "/"
            )
            .split(
                "/"
            )
            .pop();


    const token =
        localStorage.getItem(
            "access_token"
        );


    const url =
        `${window.location.origin}/reports/${encodeURIComponent(fileName)}`;


    try {

        const response =
            await fetch(
                url,
                {
                    headers: token
                        ? {
                            Authorization:
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


        const objectUrl =
            URL.createObjectURL(
                blob
            );


        const link =
            document.createElement(
                "a"
            );


        link.href =
            objectUrl;


        link.download =
            fileName;


        document.body.appendChild(
            link
        );


        link.click();


        link.remove();


        setTimeout(
            () => {

                URL.revokeObjectURL(
                    objectUrl
                );

            },
            1000
        );

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
   CASE DASHBOARD
========================================================= */

async function loadCaseDashboard() {

    const token =
        localStorage.getItem(
            "access_token"
        );


    if (!token) {
        return;
    }


    try {

        const statsResponse =
            await fetch(
                `${API}/dashboard/stats`,
                {
                    headers: {

                        Authorization:
                            `Bearer ${token}`
                    }
                }
            );


        const casesResponse =
            await fetch(
                `${API}/cases`,
                {
                    headers: {

                        Authorization:
                            `Bearer ${token}`
                    }
                }
            );


        const stats =
            await safeJson(
                statsResponse
            );


        const cases =
            await safeJson(
                casesResponse
            );


        if (
            !statsResponse.ok
        ) {

            console.warn(
                "Dashboard stats unavailable:",
                stats
            );

        }
        else {

            setText(
                "caseCount",
                stats.total || 0
            );


            setText(
                "entityCount",
                stats.entities || 0
            );


            setText(
                "resultConfidence",
                formatConfidence(
                    stats.confidence || 0
                )
            );


            setText(
                "resultContradictions",
                stats.contradictions || 0
            );

        }


        renderCaseList(
            cases.cases ||
            []
        );


    }
    catch (error) {

        console.error(
            "Case dashboard error:",
            error
        );

    }

}


/* =========================================================
   CASE LIST
========================================================= */

function renderCaseList(
    cases
) {

    const box =
        document.getElementById(
            "caseList"
        );


    if (!box) {
        return;
    }


    if (!cases.length) {

        box.innerHTML = `

            <div class="empty-state">

                No investigation cases yet.

            </div>

        `;

        return;
    }


    box.innerHTML =
        cases
            .map(
                caseItem => {

                    const status =
                        String(
                            caseItem.status ||
                            ""
                        ).toUpperCase();


                    const closed =
                        status ===
                        "CLOSED";


                    return `

                        <div class="case-row">

                            <div class="case-info">

                                <div class="case-title">

                                    #${escapeHtml(
                                        caseItem.id
                                    )}

                                    ·

                                    ${escapeHtml(
                                        caseItem.case_name ||
                                        "Investigation"
                                    )}

                                </div>


                                <div class="case-meta">

                                    ${escapeHtml(
                                        caseItem.created_at ||
                                        ""
                                    )}

                                    ·

                                    ${Number(
                                        caseItem.entities_count ||
                                        0
                                    )}

                                    entities

                                    ·

                                    ${Number(
                                        caseItem.relations_count ||
                                        0
                                    )}

                                    relationships

                                </div>

                            </div>


                            <span class="case-status ${
                                closed
                                    ? "closed"
                                    : "ongoing"
                            }">

                                ${
                                    closed
                                        ? "🔴 CLOSED"
                                        : "🟢 ONGOING"
                                }

                            </span>


                            <div class="case-actions">

                                <button
                                    type="button"
                                    class="secondary-button"
                                    onclick="openCaseDetails(${Number(
                                        caseItem.id
                                    )})"
                                >
                                    View
                                </button>


                                ${
                                    closed
                                        ? `
                                            <button
                                                type="button"
                                                class="success-button"
                                                onclick="changeCaseStatus(
                                                    ${Number(caseItem.id)},
                                                    'ONGOING'
                                                )"
                                            >
                                                Reopen
                                            </button>
                                          `
                                        : `
                                            <button
                                                type="button"
                                                class="success-button"
                                                onclick="changeCaseStatus(
                                                    ${Number(caseItem.id)},
                                                    'CLOSED'
                                                )"
                                            >
                                                Close Case
                                            </button>
                                          `
                                }


                                <button
                                    type="button"
                                    class="danger-button"
                                    onclick="deleteCase(${Number(
                                        caseItem.id
                                    )})"
                                >
                                    Delete
                                </button>

                            </div>

                        </div>
                    `;
                }
            )
            .join("");

}


/* =========================================================
   CHANGE CASE STATUS
========================================================= */

async function changeCaseStatus(
    id,
    status
) {

    const message =
        status === "CLOSED"
            ? "Close this case?"
            : "Reopen this case?";


    if (
        !confirm(
            message
        )
    ) {

        return;
    }


    const token =
        localStorage.getItem(
            "access_token"
        );


    try {

        const response =
            await fetch(
                `${API}/cases/${id}/status`,
                {

                    method:
                        "PATCH",

                    headers: {

                        "Content-Type":
                            "application/json",

                        Authorization:
                            `Bearer ${token}`

                    },

                    body:
                        JSON.stringify({
                            status:
                                status
                        })

                }
            );


        const data =
            await safeJson(
                response
            );


        if (!response.ok) {

            throw new Error(
                data.detail ||
                "Could not update case."
            );
        }


        await loadCaseDashboard();

        await loadAuditLogs();


    }
    catch (error) {

        console.error(
            "Case status error:",
            error
        );


        alert(
            error.message
        );

    }

}


/* =========================================================
   DELETE CASE
========================================================= */

async function deleteCase(
    id
) {

    if (
        !confirm(
            "Are you sure you want to delete this case?"
        )
    ) {

        return;
    }


    const token =
        localStorage.getItem(
            "access_token"
        );


    try {

        const response =
            await fetch(
                `${API}/cases/${id}`,
                {

                    method:
                        "DELETE",

                    headers: {

                        Authorization:
                            `Bearer ${token}`

                    }

                }
            );


        const data =
            await safeJson(
                response
            );


        if (!response.ok) {

            throw new Error(
                data.detail ||
                "Could not delete case."
            );
        }


        await loadCaseDashboard();

        await loadAuditLogs();

    }
    catch (error) {

        console.error(
            "Delete case error:",
            error
        );


        alert(
            error.message
        );

    }

}


/* =========================================================
   OPEN CASE DETAILS
========================================================= */

async function openCaseDetails(
    id
) {

    const modal =
        document.getElementById(
            "caseDetailsModal"
        );


    if (!modal) {

        /*
         * Your current index.html does not contain
         * a caseDetailsModal, so don't crash.
         */

        return;
    }


    modal.classList.remove(
        "hidden"
    );


    const body =
        document.getElementById(
            "caseDetailsBody"
        );


    if (body) {

        body.innerHTML =
            `<div class="empty-state">
                Loading case details...
            </div>`;

    }


    const token =
        localStorage.getItem(
            "access_token"
        );


    try {

        const response =
            await fetch(
                `${API}/cases/${id}`,
                {
                    headers: {

                        Authorization:
                            `Bearer ${token}`
                    }
                }
            );


        const data =
            await safeJson(
                response
            );


        if (!response.ok) {

            throw new Error(
                data.detail ||
                "Could not load case."
            );
        }


        const caseData =
            data.case ||
            {};


        if (!body) {
            return;
        }


        const closed =
            String(
                caseData.status ||
                ""
            ).toUpperCase() ===
            "CLOSED";


        body.innerHTML = `

            <div class="case-detail-row">

                <span>
                    Case
                </span>

                <strong>

                    #${escapeHtml(
                        caseData.id
                    )}

                    ·

                    ${escapeHtml(
                        caseData.case_name ||
                        "Investigation"
                    )}

                </strong>

            </div>


            <div class="case-detail-row">

                <span>
                    Status
                </span>

                <strong>

                    <span class="case-status ${
                        closed
                            ? "closed"
                            : "ongoing"
                    }">

                        ${
                            closed
                                ? "🔴 CLOSED"
                                : "🟢 ONGOING"
                        }

                    </span>

                </strong>

            </div>


            <div class="case-detail-row">

                <span>
                    Created
                </span>

                <strong>
                    ${escapeHtml(
                        caseData.created_at ||
                        "—"
                    )}
                </strong>

            </div>


            <div class="case-detail-row">

                <span>
                    Entities
                </span>

                <strong>
                    ${Number(
                        caseData.entities_count ||
                        0
                    )}
                </strong>

            </div>


            <div class="case-detail-row">

                <span>
                    Relationships
                </span>

                <strong>
                    ${Number(
                        caseData.relations_count ||
                        0
                    )}
                </strong>

            </div>


            <div class="case-detail-row">

                <span>
                    Confidence
                </span>

                <strong>
                    ${formatConfidence(
                        Number(
                            caseData.confidence ||
                            0
                        )
                    )}
                </strong>

            </div>


            <div class="case-detail-row">

                <span>
                    Contradictions
                </span>

                <strong>
                    ${Number(
                        caseData.contradictions_count ||
                        0
                    )}
                </strong>

            </div>

        `;

    }
    catch (error) {

        console.error(
            "Case detail error:",
            error
        );


        if (body) {

            body.innerHTML =
                `<div class="empty-state">
                    ${escapeHtml(
                        error.message
                    )}
                </div>`;

        }

    }

}


/* =========================================================
   SETTINGS CARD TOGGLE
========================================================= */

function toggleSettingsCard(
    header
) {

    const card =
        header
            ? header
                .closest(
                    ".settings-card"
                )
            : null;


    if (!card) {
        return;
    }


    if (
        header.dataset
            .accordionBound ===
        "1"
    ) {

        return;
    }


    card.classList.toggle(
        "settings-card-open"
    );

}


/* =========================================================
   REQUEST RESET FROM SETTINGS
========================================================= */

async function requestResetFromSettings() {

    const email =
        document
            .getElementById(
                "resetEmail"
            )
            ?.value
            .trim();


    const message =
        document.getElementById(
            "settingsResetMessage"
        );


    if (!email) {

        setText(
            "settingsResetMessage",
            "Please enter your registered email address."
        );

        return;
    }


    setText(
        "settingsResetMessage",
        "Requesting reset token..."
    );


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
                    body: JSON.stringify(
                        {
                            email: email
                        }
                    )
                }
            );


        const data =
            await safeJson(
                response
            );


        if (!response.ok) {

            throw new Error(
                data.detail ||
                data.message ||
                "Unable to request a password reset."
            );

        }


        const token =
            data.reset_token ||
            "";


        if (token) {

            document.getElementById(
                "settingsResetToken"
            ).value =
                token;

        }


        const form =
            document.getElementById(
                "settingsResetForm"
            );


        if (form) {

            form.classList.remove(
                "hidden"
            );

        }


        setText(
            "settingsResetMessage",
            data.message ||
            "Reset token generated successfully."
        );

    }
    catch (error) {

        setText(
            "settingsResetMessage",
            error.message
        );

    }

}


/* =========================================================
   COMPLETE RESET FROM SETTINGS
========================================================= */

async function completeResetFromSettings() {

    const token =
        document
            .getElementById(
                "settingsResetToken"
            )
            ?.value
            .trim();


    const newPassword =
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


    if (!token) {

        setText(
            "settingsResetMessage",
            "Please enter the reset token."
        );

        return;
    }


    if (
        !newPassword ||
        newPassword.length <
            8
    ) {

        setText(
            "settingsResetMessage",
            "New password must be at least 8 characters."
        );

        return;
    }


    if (
        newPassword !==
        confirmPassword
    ) {

        setText(
            "settingsResetMessage",
            "Passwords do not match."
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
                    body: JSON.stringify(
                        {
                            token: token,
                            new_password:
                                newPassword
                        }
                    )
                }
            );


        const data =
            await safeJson(
                response
            );


        if (!response.ok) {

            throw new Error(
                data.detail ||
                data.message ||
                "Unable to reset password."
            );

        }


        setText(
            "settingsResetMessage",
            data.message ||
            "Password reset successfully."
        );


        const form =
            document.getElementById(
                "settingsResetForm"
            );


        if (form) {

            form.classList.add(
                "hidden"
            );

        }


        document
            .getElementById(
                "settingsResetPassword"
            ).value =
            "";


        document
            .getElementById(
                "settingsResetConfirm"
            ).value =
            "";


    }
    catch (error) {

        setText(
            "settingsResetMessage",
            error.message
        );

    }

}


/* =========================================================
   2FA LOGIN MODAL (LOGIN PAGE)
========================================================= */

function closeTwoFALoginModal() {

    const modal =
        document.getElementById(
            "twoFALoginModal"
        );


    if (modal) {

        modal.classList.add(
            "hidden"
        );

    }

}


/* =========================================================
   FORGOT PASSWORD — MODAL TOGGLE (LOGIN PAGE)
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
   REQUEST PASSWORD RESET (LOGIN PAGE)
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

        setText(
            "forgotMessage",
            "Please enter your registered email address."
        );

        return;
    }


    setText(
        "forgotMessage",
        "Requesting reset token..."
    );


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
                    body: JSON.stringify(
                        {
                            email: email
                        }
                    )
                }
            );


        const data =
            await safeJson(
                response
            );


        if (!response.ok) {

            throw new Error(
                data.detail ||
                data.message ||
                "Unable to request a password reset."
            );

        }


        const token =
            data.reset_token ||
            "";


        if (token) {

            document.getElementById(
                "resetToken"
            ).value =
                token;

        }


        const form =
            document.getElementById(
                "resetForm"
            );


        if (form) {

            form.classList.remove(
                "hidden"
            );

        }


        setText(
            "forgotMessage",
            data.message ||
            "Reset token generated successfully. Enter a new password below."
        );

    }
    catch (error) {

        setText(
            "forgotMessage",
            error.message
        );

    }

}


/* =========================================================
   RESET PASSWORD (LOGIN PAGE)
========================================================= */

async function resetPassword() {

    const token =
        document
            .getElementById(
                "resetToken"
            )
            ?.value
            .trim();


    const newPassword =
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


    if (!token) {

        setText(
            "forgotMessage",
            "Please enter the reset token."
        );

        return;
    }


    if (
        !newPassword ||
        newPassword.length <
            8
    ) {

        setText(
            "forgotMessage",
            "New password must be at least 8 characters."
        );

        return;
    }


    if (
        newPassword !==
        confirmPassword
    ) {

        setText(
            "forgotMessage",
            "Passwords do not match."
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
                    body: JSON.stringify(
                        {
                            token: token,
                            new_password:
                                newPassword
                        }
                    )
                }
            );


        const data =
            await safeJson(
                response
            );


        if (!response.ok) {

            throw new Error(
                data.detail ||
                data.message ||
                "Unable to reset password."
            );

        }


        setText(
            "forgotMessage",
            data.message ||
            "Password reset successfully."
        );


        document
            .getElementById(
                "resetNewPassword"
            ).value =
            "";


        document
            .getElementById(
                "resetConfirmPassword"
            ).value =
            "";


        setTimeout(
            () => {

                hideForgotPassword();

            },
            1200
        );


    }
    catch (error) {

        setText(
            "forgotMessage",
            error.message
        );

    }

}


/* =========================================================
   CLOSE CASE DETAILS
========================================================= */

function closeCaseDetails() {

    const modal =
        document.getElementById(
            "caseDetailsModal"
        );


    if (modal) {

        modal.classList.add(
            "hidden"
        );

    }

}


/* =========================================================
   SETTINGS ACCORDION
========================================================= */

function initSettingsAccordion() {

    document
        .querySelectorAll(
            ".settings-card .settings-card-header"
        )
        .forEach(
            header => {

                if (
                    header.dataset
                        .accordionBound
                ) {

                    return;
                }


                header.dataset
                    .accordionBound =
                    "1";


                header.addEventListener(
                    "click",
                    () => {

                        header
                            .parentElement
                            .classList
                            .toggle(
                                "settings-open"
                            );

                    }
                );

            }
        );

}


/* =========================================================
   CHANGE PASSWORD
========================================================= */

async function changePassword() {

    const currentPassword =
        document
            .getElementById(
                "currentPassword"
            )
            ?.value;


    const newPassword =
        document
            .getElementById(
                "newPassword"
            )
            ?.value;


    const confirmPassword =
        document
            .getElementById(
                "confirmPassword"
            )
            ?.value;


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


    const error =
        passwordStrengthError(
            newPassword
        );


    if (error) {

        showMessage(
            "passwordMessage",
            error,
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

                    method:
                        "POST",

                    headers: {

                        "Content-Type":
                            "application/json",

                        Authorization:
                            `Bearer ${token}`

                    },

                    body:
                        JSON.stringify({

                            current_password:
                                currentPassword,

                            new_password:
                                newPassword

                        })

                }
            );


        const data =
            await safeJson(
                response
            );


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


        await loadAuditLogs();

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
                    method:
                        "POST",

                    headers: {

                        Authorization:
                            `Bearer ${token}`

                    }
                }
            );


        const data =
            await safeJson(
                response
            );


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
            "Secret generated. Add it to your authenticator application.",
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
        !/^\d{6}$/.test(
            code
        )
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

                    method:
                        "POST",

                    headers: {

                        "Content-Type":
                            "application/json",

                        Authorization:
                            `Bearer ${token}`

                    },

                    body:
                        JSON.stringify({

                            code:
                                code

                        })

                }
            );


        const data =
            await safeJson(
                response
            );


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


        await load2FAStatus();

        await loadAuditLogs();

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

    if (
        !confirm(
            "Are you sure you want to disable 2FA?"
        )
    ) {

        return;
    }


    const code =
        prompt(
            "Enter your current 6-digit authenticator code:"
        );


    if (
        !code ||
        !/^\d{6}$/.test(
            code
        )
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

                    method:
                        "POST",

                    headers: {

                        "Content-Type":
                            "application/json",

                        Authorization:
                            `Bearer ${token}`

                    },

                    body:
                        JSON.stringify({

                            code:
                                code

                        })

                }
            );


        const data =
            await safeJson(
                response
            );


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


        await load2FAStatus();

        await loadAuditLogs();

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

                    method:
                        "GET",

                    headers: {

                        Authorization:
                            `Bearer ${token}`

                    }

                }
            );


        if (!response.ok) {

            return;
        }


        const data =
            await safeJson(
                response
            );


        const status =
            document.getElementById(
                "twoFAStatus"
            );


        if (status) {

            const enabled =
                Boolean(
                    data.enabled
                );


            status.textContent =
                enabled
                    ? "Enabled"
                    : "Disabled";


            status.classList.remove(
                "enabled",
                "disabled"
            );


            status.classList.add(
                enabled
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
                Boolean(
                    data.enabled
                )
            );

        }


        if (disableButton) {

            disableButton.classList.toggle(
                "hidden",
                !Boolean(
                    data.enabled
                )
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

    }
    else {

        input.type =
            "password";


        if (button) {

            button.textContent =
                "Show";

        }

    }

}


/* =========================================================
   PASSWORD STRENGTH
========================================================= */

function passwordStrengthError(
    password
) {

    if (!password) {

        return "Please enter a password.";

    }


    if (
        password.length <
        8
    ) {

        return "Password must contain at least 8 characters.";

    }


    if (
        !/[A-Z]/.test(
            password
        )
    ) {

        return "Password must contain at least one uppercase letter.";

    }


    if (
        !/[a-z]/.test(
            password
        )
    ) {

        return "Password must contain at least one lowercase letter.";

    }


    if (
        !/[0-9]/.test(
            password
        )
    ) {

        return "Password must contain at least one number.";

    }


    if (
        !/[^A-Za-z0-9]/.test(
            password
        )
    ) {

        return "Password must contain at least one special character.";

    }


    return null;

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
        `message ${type || ""}`;

}


/* =========================================================
   FORMAT CONFIDENCE
========================================================= */

function formatConfidence(
    value
) {

    if (
        value ===
            null ||
        value ===
            undefined ||
        value ===
            ""
    ) {

        return "—";
    }


    const number =
        Number(
            value
        );


    if (
        Number.isNaN(
            number
        )
    ) {

        return "—";
    }


    /*
     * Backend returns values such as:
     *
     * 0.95
     *
     * which becomes:
     *
     * 95%
     */

    const percent =
        number <= 1
            ? number * 100
            : number;


    return (
        Math.round(
            percent
        ) +
        "%"
    );

}


/* =========================================================
   SAFE JSON
========================================================= */

async function safeJson(
    response
) {

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


/* =========================================================
   HTML ESCAPE
========================================================= */

function escapeHtml(
    value
) {

    return String(
        value ??
        ""
    )

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
   GLOBAL FUNCTIONS
   Required because your HTML uses onclick=""
========================================================= */

window.login =
    login;

window.register =
    register;

window.logout =
    logout;

window.showPage =
    showPage;

window.openInvestigation =
    openInvestigation;

window.runInvestigation =
    runInvestigation;

window.runSelectedAlgorithm =
    runSelectedAlgorithm;

window.openReport =
    openReport;

window.downloadReport =
    downloadReport;

window.zoomGraphIn =
    zoomGraphIn;

window.zoomGraphOut =
    zoomGraphOut;

window.fitGraph =
    fitGraph;

window.resetGraph =
    resetGraph;

window.clearGraphPath =
    clearGraphPath;

window.rebuildGraph =
    rebuildGraph;

window.changePassword =
    changePassword;

window.setup2FA =
    setup2FA;

window.enable2FA =
    enable2FA;

window.disable2FA =
    disable2FA;

window.togglePassword =
    togglePassword;

window.showRegister =
    showRegister;

window.hideRegister =
    hideRegister;

window.verifyLogin2FA =
    verifyLogin2FA;

window.requestResetFromSettings =
    requestResetFromSettings;

window.completeResetFromSettings =
    completeResetFromSettings;

window.openCaseDetails =
    openCaseDetails;

window.closeCaseDetails =
    closeCaseDetails;

window.changeCaseStatus =
    changeCaseStatus;

window.deleteCase =
    deleteCase;