
function getSelectedTokens() {
	const selected = {
		sujet: [],
		objet: [],
		pattern: []
	};

	const allTokens = document.querySelectorAll('.token');

	allTokens.forEach((tokenElement, index) => {
		const state = tokenElement.getAttribute('data-state');
		const text = tokenElement.textContent.trim();

		if (state !== 'none') {
			selected[state].push({
				element: tokenElement,
				text: text,
				position: parseInt(tokenElement.getAttribute("data-pos")),
			});
		}
	});

	return selected;
}

async function analyzeSelectedPatterns() {
	const selected = getSelectedTokens();

	if (!selected.sujet.length || !selected.pattern.length || !selected.objet.length) {
		alert("Veuillez sélectionner un sujet, un verbe et un objet.");
		return;
	}

	const pos = [
		selected.sujet[0].position,
		selected.pattern[0].position,
		selected.objet[0].position
	].join(',');

	const text = document.getElementById('text').innerText
	console.log(text);
	console.log(pos);
	console.log(`/search_pattern?pos=${pos}&text=${encodeURIComponent(text)}`);
	
	
	try {
		const response = await fetch(`/search_pattern?pos=${pos}&text=${encodeURIComponent(text)}`);
		const data = await response.json();

		displayResults(data)
	} catch (error) {
		console.error('Erreur lors de la requête:', error);
	}
}


function displayResults(paths) {
	const resultsDiv = document.getElementById('pattern-results');
	if (!resultsDiv) return;
  
	resultsDiv.innerHTML = `
	  <h3>🔍 Analyse des Chemins de Dépendance</h3>
	  <div class="paths-container">
		${Object.entries(paths).map(([key, path]) => `
		  <div class="path-block">
			<div class="rule-item">
				<strong>${key}:</strong> ${path}<br>
			</div>
		  </div>
		`).join('')}
	  </div>
	`;
  }
  