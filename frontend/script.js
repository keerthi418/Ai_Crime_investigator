const API = "http://127.0.0.1:8000/api";

let currentUser = null;
let lastInvestigation = null;


/* =========================================================
   PAGE LOAD
========================================================= */

document.addEventListener("DOMContentLoaded", () => {

    const token = localStorage.getItem("access_token");
    const page = window.location.pathname.split("/").pop();

    if (token) {
        loadCurrentUser();
    } 
    else if (page === "index.html" || page === "") {
        window.location.href = "login.html";
    }

    // Login form
    const loginForm = document.getElementById("loginForm");

    if (loginForm) {
        loginForm.addEventListener("submit", login);
    }

    // Register form
    const registerForm = document.getElementById("registerForm");

    if (registerForm) {
        registerForm.addEventListener("submit", register);
    }

});


/* =========================================================
   LOGIN
========================================================= */

async function login(event) {

    event.preventDefault();

    const email = document
        .getElementById("loginEmail")
        .value
        .trim();

    const password = document
        .getElementById("loginPassword")
        .value;

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

        const data = await response.json();

        if (!response.ok) {

            throw new Error(
                data.detail || "Login failed"
            );
        }

        // Backend returns token
        localStorage.setItem(
            "access_token",
            data.token
        );

        // Save user information
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
   REGISTER
========================================================= */

async function register(event) {

    event.preventDefault();

    const username = document
        .getElementById("registerUsername")
        .value
        .trim();

    const email = document
        .getElementById("registerEmail")
        .value
        .trim();

    const password = document
        .getElementById("registerPassword")
        .value;

    if (!username || !email || !password) {

        showMessage(
            "registerMessage",
            "Please fill all fields.",
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

        const data = await response.json();

        if (!response.ok) {

            throw new Error(
                data.detail || "Registration failed"
            );
        }

        showMessage(
            "registerMessage",
            "Account created successfully. You can now login.",
            "success"
        );

        document
            .getElementById("registerForm")
            .reset();

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

    const token = localStorage.getItem(
        "access_token"
    );

    if (!token) {

        window.location.href =
            "login.html";

        return;
    }

    try {

        const response = await fetch(
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
            await response.json();

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
        currentUser.username;

    const initial =
        username
            .charAt(0)
            .toUpperCase();

    const elements = {

        sidebarUsername: username,

        topUsername: username,

        welcomeName: username,

        profileUsername: username,

        profileEmail:
            currentUser.email,

        sidebarAvatar: initial,

        topAvatar: initial,

        profileAvatar: initial
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
        localStorage.getItem(
            "access_token"
        );

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
            "Investigator Profile"
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
   RUN INVESTIGATION
========================================================= */

async function runInvestigation() {

    const text =
        document
            .getElementById("caseText")
            .value
            .trim();

    const startNode =
        document
            .getElementById("startNode")
            .value
            .trim();

    const targetNode =
        document
            .getElementById("targetNode")
            .value
            .trim();

    if (!text) {

        showMessage(
            "investigationMessage",
            "Please enter a case description.",
            "error"
        );

        return;
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
                            startNode,

                        target_node:
                            targetNode
                    })
                }
            );

        const data =
            await response.json();

        if (!response.ok) {

            throw new Error(
                data.detail ||
                "Investigation failed"
            );
        }

        lastInvestigation =
            data;

        displayInvestigation(
            data
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

        showMessage(
            "investigationMessage",
            error.message,
            "error"
        );
    }
    finally {

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
        data.entities || [];

    const relations =
        data.relations || [];

    const contradictions =
        data.contradictions || [];

    const confidence =
        data.bayesian_confidence;

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

    renderGraph(
        data.graph
    );

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
                        ${entities.length} entities,
                        ${relations.length} relationships,
                        confidence
                        ${formatConfidence(confidence)}
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
            ).toLowerCase();

        tag.textContent =
            `${entity.text} · ${entity.type}`;

        container.appendChild(tag);
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
                    relation.source
                )}
            </b>

            &nbsp;

            ${escapeHtml(
                relation.relation
            )}

            →

            &nbsp;

            <b>
                ${escapeHtml(
                    relation.target
                )}
            </b>
        `;

        container.appendChild(item);
    });
}


/* =========================================================
   SEARCH ALGORITHMS
========================================================= */

function displayAlgorithms(results) {

    setText(
        "bfsResult",
        formatPath(results.BFS)
    );

    setText(
        "dfsResult",
        formatPath(results.DFS)
    );

    setText(
        "astarResult",
        formatPath(results["A*"])
    );
}


/* =========================================================
   FORMAT PATH
========================================================= */

function formatPath(path) {

    if (!path || !path.length) {

        return "No path found";
    }

    return path.join(" → ");
}


/* =========================================================
   CONFIDENCE
========================================================= */

function displayConfidence(
    confidence,
    explanation
) {

    const value =
        formatConfidence(
            confidence
        );

    setText(
        "confidenceCircle",
        value
    );

    setText(
        "confidenceExplanation",

        Array.isArray(explanation)
            ? explanation.join(" ")
            : String(
                explanation || ""
            )
    );
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

    if (!contradictions.length) {

        container.innerHTML =
            "✓ No contradictions detected.";

        return;
    }

    contradictions.forEach(item => {

        const div =
            document.createElement(
                "div"
            );

        div.className =
            "contradiction-item";

        div.textContent =
            item;

        container.appendChild(div);
    });
}


/* =========================================================
   EXPLAINABLE AI
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

    if (!explanation.length) {

        container.innerHTML = `
            <div class="explanation-item">
                No explanation available.
            </div>
        `;

        return;
    }

    explanation.forEach(item => {

        const div =
            document.createElement(
                "div"
            );

        div.className =
            "explanation-item";

        div.textContent =
            item;

        container.appendChild(div);
    });
}


/* =========================================================
   GRAPH
========================================================= */

function renderGraph(graphData) {

    const container =
        document.getElementById(
            "cy"
        );

    if (!container || !graphData) {
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

    const elements = [];

    (graphData.nodes || [])
        .forEach(node => {

            elements.push({

                data: {

                    id: String(
                        node.id
                    ),

                    label: String(
                        node.id
                    )
                }
            });

        });

    (graphData.edges || [])
        .forEach(
            (edge, index) => {

                elements.push({

                    data: {

                        id:
                            `edge-${index}`,

                        source:
                            String(
                                edge.source
                            ),

                        target:
                            String(
                                edge.target
                            ),

                        label:
                            String(
                                edge.relation
                            )
                    }
                });

            }
        );

    cytoscape({

        container:
            container,

        elements:
            elements,

        layout: {

            name:
                "cose",

            animate:
                true,

            padding:
                40
        },

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

                    "text-margin-y":
                        8,

                    "font-size":
                        12,

                    "font-weight":
                        "bold",

                    "width":
                        38,

                    "height":
                        38,

                    "border-width":
                        3,

                    "border-color":
                        "#dbeafe"
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
                        9,

                    "color":
                        "#475569",

                    "text-background-color":
                        "#ffffff",

                    "text-background-opacity":
                        1,

                    "text-background-padding":
                        3
                }
            }
        ]
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
            await response.json();

        const logs =
            data.logs || [];

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
                new Date(
                    log.created_at
                );

            row.innerHTML = `

                <td>
                    ${date.toLocaleString()}
                </td>

                <td>
                    <strong>
                        ${escapeHtml(
                            log.action
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

            table.appendChild(row);
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
   REPORT
========================================================= */

function openReport() {

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
        file
            .replace(/\\/g, "/")
            .split("/")
            .pop();

    const url =
        `http://127.0.0.1:8000/reports/${fileName}`;

    window.open(
        url,
        "_blank"
    );
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
   PASSWORD
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

        button.textContent =
            "Hide";
    }
    else {

        input.type =
            "password";

        button.textContent =
            "Show";
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
        value === undefined
    ) {

        return "—";
    }

    return (
        Math.round(
            Number(value) * 100
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
   SET TEXT HELPER
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