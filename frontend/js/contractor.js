const API_BASE = "http://127.0.0.1:8001"; 
let currentAuthority = null;

document.addEventListener("DOMContentLoaded", async () => {
    try {
        const response = await fetch(`${API_BASE}/api/contractor/authorities`);
        const data = await response.json();
        
        const select = document.getElementById("authority-select");
        select.innerHTML = '<option value="">-- Select Authority --</option>';
        
        data.authorities.forEach(auth => {
            const option = document.createElement("option");
            option.value = auth;
            option.textContent = auth;
            select.appendChild(option);
        });
    } catch (error) {
        console.error("Failed to load authorities:", error);
        document.getElementById("authority-select").innerHTML = '<option value="">Error loading authorities. Ensure contractor_app.py is running on port 8001.</option>';
    }
});

function loginContractor() {
    const select = document.getElementById("authority-select");
    if (!select.value) {
        alert("Please select an authority first.");
        return;
    }
    
    currentAuthority = select.value;
    document.getElementById("logged-in-authority").textContent = currentAuthority;
    
    document.getElementById("login-screen").classList.add("hidden");
    document.getElementById("dashboard-screen").classList.remove("hidden");
    
    // Hide routing box on fresh login
    document.getElementById("routing-result-box").classList.add("hidden");
    loadTasks();
}

function logoutContractor() {
    currentAuthority = null;
    document.getElementById("login-screen").classList.remove("hidden");
    document.getElementById("dashboard-screen").classList.add("hidden");
    document.getElementById("authority-select").value = "";
}

function switchTab(tabName) {
    document.getElementById("tab-unrepaired").classList.remove("active");
    document.getElementById("tab-repaired").classList.remove("active");
    document.getElementById("unrepaired-list-container").classList.add("hidden");
    document.getElementById("repaired-list").classList.add("hidden");

    document.getElementById(`tab-${tabName}`).classList.add("active");
    
    if (tabName === 'unrepaired') {
        document.getElementById("unrepaired-list-container").classList.remove("hidden");
    } else {
        document.getElementById("repaired-list").classList.remove("hidden");
    }
}

async function loadTasks() {
    if (!currentAuthority) return;

    try {
        const response = await fetch(`${API_BASE}/api/contractor/tasks?authority=${encodeURIComponent(currentAuthority)}`);
        const data = await response.json();
        
        renderUnrepairedTasks(data.unrepaired);
        renderRepairedTasks(data.repaired);
        checkCheckboxes(); // Update button visibility
    } catch (error) {
        console.error("Failed to load tasks:", error);
    }
}

function getUrgencyClass(score) {
    if (score >= 80) return "urgency-high";
    if (score >= 50) return "urgency-med";
    return "urgency-low";
}

function renderUnrepairedTasks(tasks) {
    const container = document.getElementById("unrepaired-list");
    container.innerHTML = "";

    if (tasks.length === 0) {
        container.innerHTML = "<p>No pending work orders! Excellent job.</p>";
        return;
    }

    tasks.forEach(task => {
        const div = document.createElement("div");
        div.className = `task-card ${getUrgencyClass(task.urgency_score)}`;
        
        const defectName = task.defect_type ? task.defect_type.replace('_', ' ').toUpperCase() : "UNKNOWN DEFECT";

        div.innerHTML = `
            <input type="checkbox" class="task-checkbox" value="${task.id}" onchange="checkCheckboxes()">
            <div class="task-details">
                <h4>#${task.id} - ${defectName}</h4>
                <p><strong>Location:</strong> ${task.road_name}</p>
                <p><strong>State:</strong> <span class="badge">${task.workflow_state}</span> | <strong>Priority Score:</strong> ${task.urgency_score}/100</p>
            </div>
        `;
        container.appendChild(div);
    });
}

function renderRepairedTasks(tasks) {
    const container = document.getElementById("repaired-list");
    container.innerHTML = "";

    if (tasks.length === 0) {
        container.innerHTML = "<p>No historical completed tasks found.</p>";
        return;
    }

    tasks.forEach(task => {
        const div = document.createElement("div");
        div.className = `task-card`;
        div.style.borderLeft = "6px solid #bdc3c7"; 
        div.style.opacity = "0.7";

        div.innerHTML = `
            <div class="task-details" style="padding-left: 10px;">
                <h4>#${task.id} - ${task.defect_type.toUpperCase()}</h4>
                <p><strong>Location:</strong> ${task.road_name}</p>
                <p><strong>Resolved On:</strong> ${new Date(task.updated_at).toLocaleString()}</p>
            </div>
            <div class="task-controls">
                <span class="badge" style="background:#2ecc71;">COMPLETED</span>
            </div>
        `;
        container.appendChild(div);
    });
}

function getSelectedTaskIds() {
    const checkboxes = document.querySelectorAll('.task-checkbox:checked');
    return Array.from(checkboxes).map(cb => parseInt(cb.value));
}

function checkCheckboxes() {
    const selectedCount = getSelectedTaskIds().length;
    const actionBar = document.getElementById("bulk-action-bar");
    
    if (selectedCount > 0) {
        actionBar.classList.remove("hidden");
    } else {
        actionBar.classList.add("hidden");
    }
}

async function generateMultiRoute() {
    const taskIds = getSelectedTaskIds();
    if (taskIds.length === 0) return;
    
    // Show loading state
    const resultBox = document.getElementById("routing-result-box");
    resultBox.classList.remove("hidden");
    document.getElementById("ai-reasoning-text").innerHTML = "<i>Z.ai is calculating the optimal traffic route...</i>";
    document.getElementById("maps-link-btn").classList.add("hidden");

    try {
        const response = await fetch(`${API_BASE}/api/contractor/tasks/generate`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ task_ids: taskIds, authority: currentAuthority })
        });
        
        const data = await response.json();
        
        if (data.status === "success") {
            // Update UI with AI reasoning and maps link
            document.getElementById("ai-reasoning-text").innerHTML = `<strong>Z.ai Insight:</strong> "${data.reasoning}"<br><br><span style="font-size:13px; color:#7f8c8d;">Optimized Visit Order: Task IDs [${data.optimized_sequence.join(' → ')}]</span>`;
            
            const mapsBtn = document.getElementById("maps-link-btn");
            mapsBtn.href = data.maps_url;
            mapsBtn.classList.remove("hidden");
            
            // Reload list to show IN_PROGRESS state
            loadTasks(); 
        }
    } catch (error) {
        alert("Failed to generate route.");
        resultBox.classList.add("hidden");
    }
}

async function resolveSelectedTasks() {
    const taskIds = getSelectedTaskIds();
    if (taskIds.length === 0) return;

    if (!confirm(`Confirm that construction is fully completed for these ${taskIds.length} tasks?`)) return;

    try {
        const response = await fetch(`${API_BASE}/api/contractor/tasks/resolve`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ task_ids: taskIds, authority: currentAuthority })
        });
        
        const data = await response.json();
        if (data.status === "success") {
            // Clear the routing box upon successful completion
            document.getElementById("routing-result-box").classList.add("hidden");
            // Reload the lists to move them from Unrepaired to Repaired
            loadTasks(); 
        }
    } catch (error) {
        alert("Failed to resolve tasks.");
    }
}