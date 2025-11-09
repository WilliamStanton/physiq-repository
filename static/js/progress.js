function getCookie(name) {
    let cookieValue = null;
    if (document.cookie && document.cookie !== '') {
        const cookies = document.cookie.split(';');
        for (let cookie of cookies) {
            cookie = cookie.trim();
            if (cookie.startsWith(name + '=')) {
                cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                break;
            }
        }
    }
    return cookieValue;
}

/* ---------------------------
   UPDATE STREAK DISPLAY
----------------------------*/
function updateStreakDisplay(streaks) {
    const cards = document.querySelectorAll('.streak-card');
    if (cards.length < 3) return;

    const sets = [
        { current: streaks.workout_current, best: streaks.workout_best },
        { current: streaks.nutrition_current, best: streaks.nutrition_best },
        { current: streaks.overall_current, best: streaks.overall_best }
    ];

    sets.forEach((st, i) => {
        const card = cards[i];

        const val = card.querySelector(".streak-value");
        val.innerHTML = "";
        val.append(
            document.createTextNode(st.current + " "),
            (() => {
                const s = document.createElement("span");
                s.className = "streak-unit";
                s.textContent = "days";
                return s;
            })()
        );

        card.querySelector(".streak-best").textContent = "Best: " + st.best;
    });
}

/* ---------------------------
   UI ELEMENT UPDATES
----------------------------*/
function updateIndicator(dateStr, type, status) {
    const col = document.querySelector(`.day-column[data-date="${dateStr}"]`);
    if (!col) return;

    const indicator = col.querySelector(`.${type}-indicator`);
    indicator.dataset.status = status;

    const icon = indicator.querySelector(".status-icon");

    // Remove all icon classes first
    icon.className = "status-icon bi";

    // Apply new icon based on type and status
    if (type === "workout") {
        switch (status) {
            case "done":
                icon.classList.add("bi-check-circle-fill", "text-success");
                break;
            case "rest":
                icon.classList.add("bi-circle", "text-secondary");
                break;
            case "missed":
            default:
                icon.classList.add("bi-x-circle-fill", "text-danger");
                break;
        }
    } else if (type === "nutrition") {
        switch (status) {
            case "hit":
                icon.classList.add("bi-droplet-fill", "text-success");
                break;
            case "none":
                icon.classList.add("bi-circle", "text-secondary");
                break;
            case "missed":
            default:
                icon.classList.add("bi-droplet-half", "text-danger");
                break;
        }
    }

    // Subtle feedback pulse
    icon.classList.add("pulse");
    setTimeout(() => icon.classList.remove("pulse"), 300);
}

/* ---------------------------
   API CALLS
----------------------------*/
function saveProgress(dateStr, workoutStatus, nutritionStatus) {
    fetch('/api/progress/update/', {
        method: 'POST',
        headers: {
            "Content-Type": "application/json",
            "X-CSRFToken": getCookie("csrftoken"),
        },
        body: JSON.stringify({
            date: dateStr,
            workout_status: workoutStatus,
            nutrition_status: nutritionStatus,
        }),
    })
    .then(r => r.json())
    .then(data => {
        if (!data.success) return;

        updateIndicator(dateStr, "workout", data.workout_status);
        updateIndicator(dateStr, "nutrition", data.nutrition_status);
        updateStreakDisplay(data.streaks);
    });
}

function saveNote(dateStr, notes) {
    fetch('/api/progress/note/', {
        method: 'POST',
        headers: {
            "Content-Type": "application/json",
            "X-CSRFToken": getCookie("csrftoken"),
        },
        body: JSON.stringify({ date: dateStr, notes }),
    })
    .then(r => r.json())
    .then(data => {
        if (!data.success) return;
        updateNoteButton(dateStr, data.notes);
    });
}

/* ---------------------------
   INITIALIZATION
----------------------------*/
function initProgress() {

    /* Workout click cycle */
    document.querySelectorAll(".workout-indicator").forEach(ind => {
        ind.onclick = function () {
            const col = this.closest(".day-column");
            const dateStr = col.dataset.date;

            const cycle = { "done": "rest", "rest": "missed", "missed": "done" };
            const newStatus = cycle[this.dataset.status];

            const nutrition = col.querySelector(".nutrition-indicator").dataset.status;

            saveProgress(dateStr, newStatus, nutrition);
        };
    });

    /* Nutrition click cycle */
    document.querySelectorAll(".nutrition-indicator").forEach(ind => {
        ind.onclick = function () {
            const col = this.closest(".day-column");
            const dateStr = col.dataset.date;

            const cycle = { "hit": "none", "none": "missed", "missed": "hit" };
            const newStatus = cycle[this.dataset.status];

            const workout = col.querySelector(".workout-indicator").dataset.status;

            saveProgress(dateStr, workout, newStatus);
        };
    });

    /* Notes modal */
    document.querySelectorAll(".note-btn").forEach(btn => {
        btn.onclick = function () {
            const dateStr = this.dataset.date;
            const notes = this.dataset.notes;
            const col = this.closest(".day-column");

            document.getElementById("edit-date").value = dateStr;
            document.getElementById("day-notes").value = notes;

            /* Safe radio selection */
            const workout = col.querySelector(".workout-indicator").dataset.status;
            const nutrition = col.querySelector(".nutrition-indicator").dataset.status;

            const wr = document.getElementById(`workout-${workout}`);
            const nr = document.getElementById(`nutrition-${nutrition}`);

            if (wr) wr.checked = true;
            if (nr) nr.checked = true;

            /* Modal */
            const modalEl = document.getElementById("editDayModal");
            const modal = new bootstrap.Modal(modalEl, { backdrop: true });
            modal.show();
        };
    });

    /* Save modal */
    document.getElementById("save-day-btn").onclick = function () {
        const dateStr = document.getElementById("edit-date").value;
        const notes = document.getElementById("day-notes").value;

        const workout = document.querySelector("input[name='workout-status']:checked")?.value || "missed";
        const nutrition = document.querySelector("input[name='nutrition-status']:checked")?.value || "none";

        saveProgress(dateStr, workout, nutrition);
        saveNote(dateStr, notes);

        bootstrap.Modal.getInstance(document.getElementById("editDayModal")).hide();
    };
}

/* Auto init */
if (!window.initProgress) {
    window.initProgress = initProgress;
}
document.addEventListener("DOMContentLoaded", initProgress);
