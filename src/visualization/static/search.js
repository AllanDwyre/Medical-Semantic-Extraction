document.addEventListener('DOMContentLoaded', function () {
	const searchInput = document.querySelector('#search-input, input[name="q"]');
	const searchResults = document.getElementById('search-results');

	if (!searchInput || !searchResults) return;

	let searchTimeout;

	searchInput.addEventListener('input', function () {
		clearTimeout(searchTimeout);
		const query = this.value.trim();

		if (query.length < 2) {
			searchResults.innerHTML = '';
			return;
		}

		searchTimeout = setTimeout(() => {
			fetch(`/search?q=${encodeURIComponent(query)}`)
				.then(response => response.json())
				.then(data => {
					searchResults.innerHTML = '';

					if (data.length === 0) {
						searchResults.innerHTML = '<div class="p-2">Aucun résultat trouvé</div>';
						return;
					}

					const pageResults = {};
					data.forEach(item => {
						if (!pageResults[item.id]) {
							pageResults[item.id] = {
								id: item.id,
								title: item.title,
								keywords: []
							};
						}
						pageResults[item.id].keywords.push({
							keyword: item.keyword,
							score: item.score
						});
					});

					Object.values(pageResults).forEach(page => {
						const div = document.createElement('div');
						div.className = 'result-item';
						div.innerHTML = `
							<a href="/page/${page.id}" class="text-decoration-none">
								<strong>${page.title}</strong>
								<div class="small">
									Mots-clés: ${page.keywords.slice(0, 3).map(k =>
										`<span class="badge">${k.keyword}</span>`
									).join(' ')}
									${page.keywords.length > 3 ? `<span class="badge">+${page.keywords.length - 3}</span>` : ''}
								</div>
							</a>
						`;
						searchResults.appendChild(div);
					});
				})
				.catch(error => {
					console.error('Error:', error);
					searchResults.innerHTML = '<div class="p-2 text-danger">Erreur lors de la recherche</div>';
				});
		}, 300);
	});
});
