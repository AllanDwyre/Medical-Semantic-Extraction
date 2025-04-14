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

	// Context Viewer
	const keywordItems = document.querySelectorAll('.keyword-item');

	function highlightKeyword(keyword) {
		// Désélectionner tous les mots
		document.querySelectorAll('.highlight[data-selected="1"]').forEach(el => {
			el.setAttribute('data-selected', '0');
		});

		// Sélectionner ceux qui correspondent
		const matches = document.querySelectorAll('.highlight');
		matches.forEach(el => {
			if (el.textContent.toLowerCase() === keyword.toLowerCase())
			{
				el.setAttribute('data-selected', '1');
			}
		});

		const first = document.querySelector('.highlight[data-selected="1"]');
		if (first) first.scrollIntoView({ behavior: 'smooth', block: 'center' });
	}

	keywordItems.forEach(item => {
		item.addEventListener("click", () => {
			const keyword = item.dataset.keyword;
			highlightKeyword(keyword);
		});
	});

	document.querySelectorAll('.highlight').forEach(el => {
		el.addEventListener("click", () => {
			const keyword = el.textContent;
			highlightKeyword(keyword);
		});
	});

});