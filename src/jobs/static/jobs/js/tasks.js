const STATUS_STYLES = {
    PENDING: "bg-warning text-dark",
    SUCCESS: "bg-success",
    FAILED: "bg-danger",
};

function statusBadge(status) {
    const cls = STATUS_STYLES[status] || "bg-secondary";
    return `<span class="badge status-badge ${cls}">${status}</span>`;
}

function formatDate(iso) {
    if (!iso) return "—";
    const d = new Date(iso);
    return d.toLocaleString();
}

function taskCard(task) {
    return `
        <div class="col-md-6 col-lg-4" data-task-id="${task.id}">
            <div class="card task-card h-100 shadow-sm">
                <div class="card-body d-flex flex-column">
                    <div class="d-flex justify-content-between align-items-start mb-2">
                        <h5 class="card-title mb-0">${escapeHtml(task.title)}</h5>
                        ${statusBadge(task.status)}
                    </div>
                    <p class="card-text text-muted small flex-grow-1">
                        ${escapeHtml(task.description || "No description")}
                    </p>
                    <div class="text-muted small mb-3">
                        Created: ${formatDate(task.created_at)}<br>
                        Finished: ${formatDate(task.finished_at)}
                    </div>
                    <div class="d-flex gap-2 flex-wrap">
                        ${task.status === "PENDING" ? `
                            <button class="btn btn-sm btn-success" data-action="complete">✓ Complete</button>
                            <button class="btn btn-sm btn-danger" data-action="fail">✗ Fail</button>
                        ` : ""}
                        <button class="btn btn-sm btn-outline-secondary" data-action="delete">Delete</button>
                    </div>
                </div>
            </div>
        </div>
    `;
}

function escapeHtml(str) {
    const div = document.createElement("div");
    div.textContent = str;
    return div.innerHTML;
}

async function loadTasks() {
    if (!requireAuth()) return;

    const container = document.getElementById("tasks-container");
    const emptyBox = document.getElementById("empty-box");
    container.innerHTML = `<div class="col-12 text-center text-muted py-5">Loading...</div>`;

    try {
        const tasks = await apiJSON("/api/tasks/");
        container.innerHTML = "";

        if (!tasks || tasks.length === 0) {
            emptyBox.classList.remove("d-none");
            return;
        }

        emptyBox.classList.add("d-none");
        tasks.forEach((t) => container.insertAdjacentHTML("beforeend", taskCard(t)));
        attachHandlers();
    } catch (err) {
        container.innerHTML = `<div class="col-12"><div class="alert alert-danger">${err.message}</div></div>`;
    }
}

function attachHandlers() {
    document.querySelectorAll("[data-task-id]").forEach((card) => {
        const id = card.dataset.taskId;
        card.querySelectorAll("[data-action]").forEach((btn) => {
            btn.addEventListener("click", async () => {
                const action = btn.dataset.action;
                try {
                    if (action === "complete") {
                        await apiJSON(`/api/tasks/${id}/complete/`, { method: "POST" });
                    } else if (action === "fail") {
                        await apiJSON(`/api/tasks/${id}/fail/`, { method: "POST" });
                    } else if (action === "delete") {
                        if (!confirm("Delete this task?")) return;
                        await apiFetch(`/api/tasks/${id}/`, { method: "DELETE" });
                    }
                    await loadTasks();
                } catch (err) {
                    alert(err.message);
                }
            });
        });
    });
}

async function createTask(event) {
    event.preventDefault();
    if (!requireAuth()) return;

    const errorBox = document.getElementById("error-box");
    errorBox.classList.add("d-none");

    const title = document.getElementById("title").value.trim();
    const description = document.getElementById("description").value.trim();

    try {
        await apiJSON("/api/tasks/", {
            method: "POST",
            body: JSON.stringify({ title, description }),
        });
        window.location.href = "/tasks-ui/";
    } catch (err) {
        errorBox.textContent = err.message;
        errorBox.classList.remove("d-none");
    }
}