const contentArea = document.getElementById('content-area');
const sidebarLinks = document.querySelectorAll('#sidebar a');
const loader = document.getElementById('loader-overlay');

function showLoader(message = "Your coach AI is preparing your plan...") {
    loader.querySelector("p").textContent = message;
    loader.classList.remove("d-none");
    requestAnimationFrame(() => loader.style.opacity = "1");
}

function hideLoader() {
    loader.style.opacity = "0";
    setTimeout(() => loader.classList.add("d-none"), 400);
}

sidebarLinks.forEach(link => {
    link.addEventListener('click', e => {
        e.preventDefault();

        const clickedLink = e.currentTarget;
        const viewName = clickedLink.getAttribute('data-view');

        sidebarLinks.forEach(l => l.classList.remove('active'));
        clickedLink.classList.add('active');

        // 🔥 Hide the content immediately
        contentArea.classList.add("d-none");
        showLoader("Loading your dashboard...");

        fetch(`/dashboard${viewName}`)
            .then(r => {
                if (!r.ok) throw new Error('Failed to load content');
                return r.text();
            })
            .then(data => {
                contentArea.innerHTML = data;

                if (viewName === "/chat") {
                    initChat();
                    initPromptBubbles();
                }
                else if (viewName === "/nutrition") {
                    initNutrition();
                }
                else if (viewName === "/workout") {
                    workoutModifyHandler();
                    initWorkout();
                }
                else if (viewName === "/progress") {
                    initProgress();
                } else if (viewName === "/overview") {
                    initOverview();
                } else if (viewName === "/photo-locker" || viewName === "/community-feed") {
                      initPhotoPreview();
                  }
            })
            .catch(error => {
                contentArea.innerHTML = `
                    <div class="alert alert-danger text-center mt-5">
                        Failed to load this section. Please try again later.
                    </div>`;
                console.error(error);
            })
            .finally(() => {
                hideLoader();
                // ✅ Show content only after loader is done
                contentArea.classList.remove("d-none");
            });
    });
});

function getCookie(name) {
    let cookieValue = null;
    if (document.cookie && document.cookie !== '') {
        const cookies = document.cookie.split(';');
        for (let i = 0; i < cookies.length; i++) {
            const cookie = cookies[i].trim();
            if (cookie.substring(0, name.length + 1) === (name + '=')) {
                cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                break;
            }
        }
    }
    return cookieValue;
}

function workoutModifyHandler() {
  const submitBtn = document.querySelector("#submit-modify-plan");
  if (!submitBtn) return;

  submitBtn.onclick = async () => {
    const payload = {
      goal: document.getElementById("goal-input").value.trim(),
      schedule: document.getElementById("schedule-input").value.trim(),
      notes: document.getElementById("notes-input").value.trim(),
    };

    bootstrap.Modal.getInstance(document.querySelector("#modifyPlanModal")).hide();

    // Optional loader if you're using one
    window.showLoader?.("Updating workout plan...");

    const res = await fetch("/dashboard/workout/", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        "X-CSRFToken": getCookie("csrftoken"),
      },
      body: JSON.stringify(payload)
    });

    const html = await res.text();
    document.getElementById("content-area").innerHTML = html;

    // Re-bind button to new DOM
    workoutModifyHandler();

    window.hideLoader?.();
  };
}

function goToTab(viewName) {
    // Normalize (allow "workout" or "/workout")
    const target = viewName.startsWith("/") ? viewName : `/${viewName}`;

    const link = document.querySelector(`#sidebar a[data-view="${target}"]`);
    if (link) link.click();
}


document.addEventListener("DOMContentLoaded", () => {
    const params = new URLSearchParams(window.location.search);
    const tab = params.get("tab");

    if (tab) {
        goToTab(tab);
        history.replaceState(null, "", "/dashboard/");
    } else {
        goToTab("overview");
    }
});
goToTab("overview");