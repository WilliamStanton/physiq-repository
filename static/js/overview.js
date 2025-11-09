function initOverview() {
  const nutritionCard = document.querySelector('.overview-nutrition-card');
  if (!nutritionCard) return;

  const label = document.getElementById('mealModalLabel');
  const details = document.getElementById('meal-details');
  const viewPlanBtn = nutritionCard.querySelector('.overview-nutrition-link');

  if (viewPlanBtn) {
    viewPlanBtn.addEventListener('click', (e) => {
      e.stopPropagation();
      e.preventDefault();
      goToTab('nutrition');
    });
  }

  nutritionCard.addEventListener('click', () => {
    const jsonScript = document.getElementById(nutritionCard.dataset.mealsId);
    if (!jsonScript) return;

    const meals = JSON.parse(jsonScript.textContent.trim());
    label.textContent = `${nutritionCard.dataset.day} — ${nutritionCard.dataset.calories} kcal`;

    details.innerHTML = meals.map(meal => {
      const macros = meal.items.reduce((tot, item) => ({
        protein: tot.protein + (item.protein_g || 0),
        carbs: tot.carbs + (item.carbs_g || 0),
        fat: tot.fat + (item.fat_g || 0)
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
              <div class="small text-light opacity-75">${item.portion || ''}</div>
            </div>
          `).join('')}
        </div>
      `;
    }).join('');

    // ✅ Now open modal manually
    const modal = new bootstrap.Modal(document.getElementById('mealModal'));
    modal.show();
  });
}
