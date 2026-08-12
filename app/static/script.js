// Market Basket Analysis - frontend logic
// Handles the product selector, basket chips and recommendation calls.

const select = document.getElementById("product-select");
const basketEl = document.getElementById("basket");
const resultsEl = document.getElementById("results");
const recommendBtn = document.getElementById("recommend-btn");

let basket = [];

// ---------------------------------------------------------------------
// Product search (filters the multi-select)
// ---------------------------------------------------------------------
const productSearch = document.getElementById("product-search");
productSearch.addEventListener("input", () => {
    const query = productSearch.value.trim().toLowerCase();
    Array.from(select.options).forEach((option) => {
        option.hidden = query !== "" && !option.value.toLowerCase().includes(query);
    });
});

// ---------------------------------------------------------------------
// Basket helpers
// ---------------------------------------------------------------------
function renderBasket() {
    basketEl.innerHTML = "";

    if (basket.length === 0) {
        basketEl.innerHTML = '<span class="basket-placeholder">No products added yet.</span>';
        return;
    }

    basket.forEach((product) => {
        const chip = document.createElement("span");
        chip.className = "chip";
        chip.textContent = product;

        const remove = document.createElement("button");
        remove.type = "button";
        remove.textContent = "\u00d7"; // ×
        remove.setAttribute("aria-label", "Remove " + product);
        remove.onclick = () => {
            basket = basket.filter((item) => item !== product);
            renderBasket();
        };

        chip.appendChild(remove);
        basketEl.appendChild(chip);
    });
}

function addSelected() {
    const selected = Array.from(select.selectedOptions).map((opt) => opt.value);
    selected.forEach((product) => {
        if (!basket.includes(product)) {
            basket.push(product);
        }
    });
    renderBasket();
}

// ---------------------------------------------------------------------
// Recommendations
// ---------------------------------------------------------------------
async function fetchRecommendations() {
    if (basket.length === 0) {
        showStatus("Please add at least one product to your basket.", "error");
        return;
    }

    recommendBtn.disabled = true;
    recommendBtn.textContent = "Analysing basket...";
    resultsEl.innerHTML = "";

    try {
        const response = await fetch("/api/recommend", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ products: basket }),
        });

        const data = await response.json();

        if (!response.ok) {
            showStatus(data.error || "Something went wrong.", "error");
            return;
        }

        if (data.message) {
            showStatus(data.message, "error");
            return;
        }

        renderRecommendations(data.recommendations);
    } catch (error) {
        showStatus("Could not reach the server. Is the Flask app running?", "error");
    } finally {
        recommendBtn.disabled = false;
        recommendBtn.textContent = "Recommend Products";
    }
}

function renderRecommendations(recommendations) {
    resultsEl.innerHTML = "";

    if (recommendations.length === 0) {
        resultsEl.innerHTML =
            '<p class="results-placeholder">No strong associations found for this basket yet.</p>';
        return;
    }

    recommendations.forEach((rec) => {
        const item = document.createElement("div");
        item.className = "result-item";

        const info = document.createElement("div");
        const name = document.createElement("div");
        name.className = "product-name";
        name.textContent = rec.product;

        const rule = document.createElement("div");
        rule.className = "product-rule";
        rule.textContent = "Because you bought: " + rec.rule;

        info.appendChild(name);
        info.appendChild(rule);

        const metrics = document.createElement("div");
        metrics.className = "result-metrics";
        metrics.innerHTML =
            "<strong>" + Math.round(rec.confidence * 100) + "% confidence</strong>" +
            "lift " + rec.lift;

        item.appendChild(info);
        item.appendChild(metrics);
        resultsEl.appendChild(item);
    });
}

function showStatus(message, type) {
    const existing = document.querySelector(".status");
    if (existing) existing.remove();

    const status = document.createElement("div");
    status.className = "status " + type;
    status.textContent = message;
    resultsEl.appendChild(status);
}

// ---------------------------------------------------------------------
// Event wiring
// ---------------------------------------------------------------------
document.getElementById("add-product").addEventListener("click", addSelected);

document.getElementById("clear-basket").addEventListener("click", () => {
    basket = [];
    renderBasket();
    resultsEl.innerHTML =
        '<p class="results-placeholder">Recommendations will appear here.</p>';
});

recommendBtn.addEventListener("click", fetchRecommendations);

select.addEventListener("dblclick", addSelected);

// Allow pressing Enter in the select to add items quickly.
select.addEventListener("keydown", (event) => {
    if (event.key === "Enter") {
        event.preventDefault();
        addSelected();
    }
});

renderBasket();

// ---------------------------------------------------------------------
// Rule explorer (filterable table + SVG scatter plot)
// ---------------------------------------------------------------------
const ruleSearch = document.getElementById("rule-search");
const ruleMinConf = document.getElementById("rule-min-conf");
const ruleMinLift = document.getElementById("rule-min-lift");
const ruleSort = document.getElementById("rule-sort");
const ruleApply = document.getElementById("rule-apply");
const rulesTbody = document.getElementById("rules-tbody");
const ruleScatter = document.getElementById("rule-scatter");
const rulesCount = document.getElementById("rules-count");

async function fetchRules() {
    const params = new URLSearchParams({
        product: ruleSearch.value.trim(),
        min_confidence: ruleMinConf.value || "0",
        min_lift: ruleMinLift.value || "0",
        sort_by: ruleSort.value,
        limit: "100",
    });

    try {
        const response = await fetch("/api/rules?" + params.toString());
        const data = await response.json();
        renderRulesTable(data.rules);
        renderRuleScatter(data.rules);
        rulesCount.textContent =
            "Showing " + data.count + " rule" + (data.count === 1 ? "" : "s") + ".";
    } catch (error) {
        rulesTbody.innerHTML =
            '<tr><td colspan="4" class="empty-cell">Could not load rules.</td></tr>';
        ruleScatter.innerHTML = "";
    }
}

function renderRulesTable(rules) {
    if (rules.length === 0) {
        rulesTbody.innerHTML =
            '<tr><td colspan="4" class="empty-cell">No rules match these filters.</td></tr>';
        return;
    }

    rulesTbody.innerHTML = "";
    rules.forEach((rule) => {
        const row = document.createElement("tr");
        row.innerHTML =
            "<td>" + escapeHtml(rule.antecedents.join(", ")) + "</td>" +
            "<td>" + escapeHtml(rule.consequents.join(", ")) + "</td>" +
            "<td>" + (rule.confidence * 100).toFixed(0) + "%</td>" +
            "<td>" + rule.lift.toFixed(2) + "</td>";
        rulesTbody.appendChild(row);
    });
}

function escapeHtml(text) {
    return String(text).replace(/[&<>"']/g, (ch) => ({
        "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;",
    }[ch]));
}

function renderRuleScatter(rules) {
    if (rules.length === 0) {
        ruleScatter.innerHTML =
            '<p class="scatter-empty">No rules to plot.</p>';
        return;
    }

    const W = 360, H = 300, PAD = 38;
    const xs = rules.map((r) => r.support);
    const ys = rules.map((r) => r.confidence);
    const zs = rules.map((r) => r.lift);
    const xMax = Math.max.apply(null, xs) || 1;
    const yMax = Math.max.apply(null, ys) || 1;
    const zMin = Math.min.apply(null, zs);
    const zMax = Math.max.apply(null, zs);

    const px = (v) => PAD + (v / xMax) * (W - 2 * PAD);
    const py = (v) => H - PAD - (v / yMax) * (H - 2 * PAD);

    let circles = "";
    rules.forEach((r) => {
        const hue = 230 * (1 - (zMax > zMin ? (r.lift - zMin) / (zMax - zMin) : 0.5));
        circles += '<circle cx="' + px(r.support).toFixed(1) +
            '" cy="' + py(r.confidence).toFixed(1) +
            '" r="4" fill="hsl(' + hue + ', 80%, 50%)" opacity="0.8">' +
            '<title>' + escapeHtml(r.antecedents.join(", ") + " -> " +
            r.consequents.join(", ") + "  (lift " + r.lift.toFixed(2) + ")") +
            "</title></circle>";
    });

    ruleScatter.innerHTML =
        '<svg viewBox="0 0 ' + W + " " + H + '" class="scatter-svg" role="img">' +
        '<text x="' + (W / 2) + '" y="16" text-anchor="middle" font-weight="bold">' +
        "Support vs Confidence</text>" +
        '<line x1="' + PAD + '" y1="' + (H - PAD) + '" x2="' + (W - PAD) +
        '" y2="' + (H - PAD) + '" stroke="#999"></line>' +
        '<line x1="' + PAD + '" y1="' + PAD + '" x2="' + PAD + '" y2="' +
        (H - PAD) + '" stroke="#999"></line>' +
        '<text x="' + (W / 2) + '" y="' + (H - 8) +
        '" text-anchor="middle" font-size="11">Support</text>' +
        '<text x="14" y="' + (H / 2) +
        '" text-anchor="middle" font-size="11" transform="rotate(-90 14 ' +
        (H / 2) + ')">Confidence</text>' +
        '<text x="' + (W - PAD) + '" y="' + (H - 14) + '" text-anchor="end" ' +
        'font-size="10" fill="#666">' + xMax.toFixed(3) + "</text>" +
        circles +
        "</svg>";
}

ruleApply.addEventListener("click", fetchRules);
ruleSearch.addEventListener("keydown", (event) => {
    if (event.key === "Enter") {
        event.preventDefault();
        fetchRules();
    }
});

fetchRules();
