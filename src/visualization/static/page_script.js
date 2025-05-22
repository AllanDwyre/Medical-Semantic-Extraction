document.addEventListener("DOMContentLoaded", function () {
	// Navigation ← →
	const index = parseInt(document.body.dataset.currentIndex);
	document.addEventListener("keydown", function (event) {
		if (event.key === "ArrowRight")
		{
			window.location.href = "/page/" + (index + 1);
		} else if (event.key === "ArrowLeft" && index > 1)
		{
			window.location.href = "/page/" + (index - 1);
		}
	});

	const terms = document.querySelectorAll('.highlight-term');

	let currentRelationIds = [];

	terms.forEach(term => {
		term.addEventListener('click', function () {
			// Get the clicked element's data-relation-id and split into an array
			const relationIdAttr = this.getAttribute('data-relation-id');
			const clickedIds = relationIdAttr.split('_');

			// Check if current selection is the same as the clicked one
			const isSameSelection = JSON.stringify(currentRelationIds) === JSON.stringify(clickedIds);

			// Clear all existing highlights based on currentRelationIds
			if (currentRelationIds.length > 0) {
			document.querySelectorAll('.highlight-term').forEach(el => {
				const elIds = el.getAttribute('data-relation-id').split('_');
				if (elIds.some(id => currentRelationIds.includes(id))) {
				el.classList.remove('highlighted');
				}
			});
			}

			// Update selection (clear if same, set to clicked if different)
			currentRelationIds = isSameSelection ? [] : clickedIds;

			// Apply highlight if it’s a new selection
			if (!isSameSelection) {
			document.querySelectorAll('.highlight-term').forEach(el => {
				const elIds = el.getAttribute('data-relation-id').split('_');
				if (elIds.some(id => currentRelationIds.includes(id))) {
				el.classList.add('highlighted');
				}
			});
			}
		});
	});

});