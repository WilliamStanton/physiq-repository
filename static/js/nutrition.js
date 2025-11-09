function initNutrition() {
  const label = document.getElementById('mealModalLabel');
  const details = document.getElementById('meal-details');
  if (!label || !details) return;

  // ✅ We now bind to the entire day-card instead of the old button
  document.querySelectorAll('.day-card').forEach(card => {
    card.addEventListener('click', () => {
      const jsonScript = document.getElementById(card.dataset.mealsId);
      const meals = JSON.parse(jsonScript.textContent.trim());

      label.textContent = `${card.dataset.day} — ${card.dataset.calories} kcal`;

      details.innerHTML = meals.map(meal => {
        const macros = meal.items.reduce((tot, item) => ({
          protein: tot.protein + item.protein_g,
          carbs: tot.carbs + item.carbs_g,
          fat: tot.fat + item.fat_g
        }), { protein: 0, carbs: 0, fat: 0 });

        return `
          <div class="mb-4">
            <h6 class="fw-bold">${meal.name} — ${meal.meal_total_calories} kcal</h6>
            <div class="small text-light opacity-75 mb-2">
              Protein: ${macros.protein}g • Carbs: ${macros.carbs}g • Fat: ${macros.fat}g
            </div>
            ${meal.items.map(item => `
              <div class="border-start border-secondary ps-3 mb-2">
                <strong>${item.food}</strong> — ${item.calories} kcal
                <div class="small text-light opacity-75">${item.portion}</div>
              </div>
            `).join('')}
          </div>
        `;
      }).join('') +
      (card.dataset.notes ? `<p class="fst-italic small text-light opacity-75">${card.dataset.notes}</p>` : '');
    });
  });

  // regenerate
  const regenerateBtn = document.getElementById('generate-mealplan-btn');
  if (regenerateBtn) {
    regenerateBtn.addEventListener('click', () => {
      if (typeof window.showLoader === "function") showLoader("Generating new meal plan...");

      fetch('/dashboard/nutrition/', {
        method: 'POST',
        headers: { 'X-CSRFToken': getCookie('csrftoken') },
      })
      .then(r => r.text())
      .then(html => {
        document.getElementById('content-area').innerHTML = html;
        initNutrition();
      })
      .finally(() => {
        if (typeof window.hideLoader === "function") hideLoader();
      });
    });
  }

  // compute weekly averages
  try {
    const dayScripts = document.querySelectorAll('[id^="meals-"]');
    let totalProtein = 0, totalCarbs = 0, totalFat = 0, totalDays = dayScripts.length;

    dayScripts.forEach(script => {
      const meals = JSON.parse(script.textContent.trim());
      meals.forEach(meal => {
        meal.items.forEach(i => {
          totalProtein += i.protein_g;
          totalCarbs += i.carbs_g;
          totalFat += i.fat_g;
        });
      });
    });
  } catch(e) {}
}
