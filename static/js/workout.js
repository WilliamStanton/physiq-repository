function initWorkout() {
    // Initialize prompt bubbles
    const promptBubbles = document.querySelectorAll('.bubble-prompt');
    
    promptBubbles.forEach(bubble => {
        bubble.addEventListener('click', function() {
            const promptText = this.textContent.trim();
            
            // Find the notes input in the modal
            const goalInput = document.getElementById('goal-input');
            
            if (goalInput) {
                // Fill the input with the prompt text
                goalInput.value = promptText;
                
                // Open the modal using Bootstrap 5
                const modalElement = document.getElementById('modifyPlanModal');
                const modal = new bootstrap.Modal(modalElement);
                modal.show();
                
                // Focus on the input after modal opens
                modalElement.addEventListener('shown.bs.modal', function() {
                    goalInput.focus();
                }, { once: true });
            } else {
                console.error('Could not find notes input in modal');
            }
        });
    });
}

// Make sure this runs when workout view is loaded
if (typeof window.initWorkout === 'undefined') {
    window.initWorkout = initWorkout;
}