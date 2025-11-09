function initProfileWizard() {
  let currentStep = 1;
  const steps = document.querySelectorAll(".step");

  function showStep(step) {
    steps.forEach(s => s.classList.add("d-none"));
    const target = document.querySelector(`.step[data-step="${step}"]`);
    if (target) target.classList.remove("d-none");
    currentStep = step;
  }

  document.querySelectorAll(".next-step").forEach(btn => {
    btn.addEventListener("click", () => showStep(currentStep + 1));
  });
  document.querySelectorAll(".prev-step").forEach(btn => {
    btn.addEventListener("click", () => showStep(currentStep - 1));
  });

  const cards = document.querySelectorAll(".goal-card");
  cards.forEach(card => {
    card.addEventListener("click", () => {
      const input = card.querySelector('input[type="radio"]');
      if (input) {
        input.checked = true;
        cards.forEach(c => c.classList.remove("selected"));
        card.classList.add("selected");
      }
    });
  });

  const preChecked = document.querySelector('.goal-card input[type="radio"]:checked');
  if (preChecked) {
    preChecked.closest('.goal-card')?.classList.add('selected');
  }
}

/* ---- Schedule Grid ---- */
function initScheduleGrid() {
  const grid = document.getElementById("schedule-grid");
  const scheduleInput = document.querySelector("input[name='schedule']");
  if (!grid || !scheduleInput) return;

  const days = ["Monday", "Tuesday", "Wed.", "Thursday", "Friday", "Saturday"];
  const hours = [8, 10, 12, 14, 16, 18]; // time blocks, every 2 hours
  const schedule = {};

  // 🔹 Add top row of time labels
  const topLabel = document.createElement("div");
  topLabel.classList.add("day-label");
  topLabel.textContent = ""; // blank top-left corner
  grid.appendChild(topLabel);

  hours.forEach(hour => {
    const timeLabel = document.createElement("div");
    timeLabel.classList.add("time-header");
    const ampm = hour < 12 ? "AM" : "PM";
    const displayHour = hour > 12 ? hour - 12 : hour;
    timeLabel.textContent = `${displayHour} ${ampm}`;
    grid.appendChild(timeLabel);
  });

  // 🔹 Add day rows + clickable cells
  days.forEach(day => {
    const dayLabel = document.createElement("div");
    dayLabel.classList.add("day-label");
    dayLabel.textContent = day;
    grid.appendChild(dayLabel);

    hours.forEach(hour => {
      const cell = document.createElement("div");
      cell.classList.add("time-slot");
      cell.dataset.day = day.toLowerCase();
      cell.dataset.hour = hour;
      cell.title = `${day} ${hour}:00 - ${hour + 2}:00`;

      cell.addEventListener("click", () => {
        cell.classList.toggle("busy");
        const d = cell.dataset.day;
        const h = `${hour}-${hour + 2}`;
        if (!schedule[d]) schedule[d] = [];
        if (cell.classList.contains("busy")) {
          schedule[d].push(h);
        } else {
          schedule[d] = schedule[d].filter(t => t !== h);
          if (schedule[d].length === 0) delete schedule[d];
        }
        scheduleInput.value = JSON.stringify(schedule);
      });

      grid.appendChild(cell);
    });
  });

  // 🔹 Preload any existing data
  try {
    const existing = JSON.parse(scheduleInput.value || "{}");
    for (const [day, blocks] of Object.entries(existing)) {
      blocks.forEach(h => {
        const start = h.split("-")[0];
        const cell = grid.querySelector(
          `.time-slot[data-day="${day}"][data-hour="${start}"]`
        );
        if (cell) cell.classList.add("busy");
      });
    }
  } catch {}
}

document.addEventListener("DOMContentLoaded", () => {
  initProfileWizard();
  initScheduleGrid();
});