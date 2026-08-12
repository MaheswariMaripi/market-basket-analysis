// ================================================================
// Basket Insight - frontend logic
// Storefront cards, basket state, recommendations, rule explorer.
// ================================================================

// ---- State -------------------------------------------------------
let basket = [];
const AISLES = window.AISLES || [];

// ---- Product emoji lookup -----------------------------------------
const EMOJI_RULES = [
    [/\bmilk\b/, "🥛"], [/\bmineral water\b/, "💧"], [/\bwater\b/, "💧"],
    [/\bjuice\b/, "🧃"], [/\bsoda\b/, "🥤"], [/\bcola\b/, "🥤"],
    [/\bcoffee\b/, "☕"], [/\btea\b/, "🍵"], [/\benergy drink\b/, "⚡"],
    [/\bbeer\b/, "🍺"], [/\bwine\b/, "🍷"],
    [/\bchocolate\b/, "🍫"], [/\bcandy\b/, "🍬"], [/\bgummy\b/, "🍬"],
    [/\bcookie\b/, "🍪"], [/\bbiscuit\b/, "🍪"], [/\bcrackers\b/, "🍘"],
    [/\bcakes\b/, "🍰"], [/\bcake\b/, "🍰"], [/\bcroissant\b/, "🥐"],
    [/\bbread\b/, "🍞"], [/\bbaguette\b/, "🥖"],
    [/\bcereals\b/, "🥣"], [/\brice\b/, "🍚"],
    [/\bspaghetti\b/, "🍝"], [/\bpasta\b/, "🍝"], [/\bnoodles\b/, "🍜"],
    [/\bflour\b/, "🌾"],
    [/\beggs\b/, "🥚"], [/\bbutter\b/, "🧈"], [/\bcheese\b/, "🧀"],
    [/\bfromage\b/, "🧀"], [/\byogurt\b/, "🥛"], [/\bcream\b/, "🍨"],
    [/\bground beef\b/, "🥩"], [/\bmeat\b/, "🥩"], [/\bbeef\b/, "🥩"],
    [/\bsteak\b/, "🥩"], [/\bchicken\b/, "🍗"], [/\bturkey\b/, "🦃"],
    [/\bpork\b/, "🥓"], [/\bbacon\b/, "🥓"], [/\bham\b/, "🍖"],
    [/\bburger\b/, "🍔"], [/\bsausage\b/, "🌭"], [/\bescalope\b/, "🍖"],
    [/\bfish\b/, "🐟"], [/\bshrimp\b/, "🦐"], [/\btuna\b/, "🐟"],
    [/\bsalmon\b/, "🐟"],
    [/\bfrench fries\b/, "🍟"], [/\bpotato\b/, "🥔"], [/\bchips\b/, "🥔"],
    [/\btomato\b/, "🍅"], [/\bonion\b/, "🧅"], [/\bgarlic\b/, "🧄"],
    [/\bcucumber\b/, "🥒"], [/\bpepper\b/, "🫑"], [/\bmushroom\b/, "🍄"],
    [/\bcarrot\b/, "🥕"], [/\bcorn\b/, "🌽"], [/\bavocado\b/, "🥑"],
    [/\bbroccoli\b/, "🥦"], [/\bcabbage\b/, "🥬"], [/\bsalad\b/, "🥗"],
    [/\bvegetables\b/, "🥦"], [/\bspinach\b/, "🥬"],
    [/\bapple\b/, "🍎"], [/\bbanana\b/, "🍌"], [/\borange\b/, "🍊"],
    [/\blemon\b/, "🍋"], [/\bberry\b/, "🫐"], [/\bstrawberr\b/, "🍓"],
    [/\bgrapes\b/, "🍇"], [/\bwatermelon\b/, "🍉"], [/\bpeach\b/, "🍑"],
    [/\bpear\b/, "🍐"], [/\bpineapple\b/, "🍍"], [/\bfruit\b/, "🍎"],
    [/\bolive oil\b/, "🫒"], [/\bolives\b/, "🫒"],
    [/\bhoney\b/, "🍯"], [/\bjam\b/, "🍓"], [/\bsugar\b/, "🍬"],
    [/\bsoup\b/, "🍲"], [/\bsauce\b/, "🥫"], [/\btomato sauce\b/, "🍝"],
    [/\bherb\b/, "🌿"], [/\bspices\b/, "🧂"], [/\bsalt\b/, "🧂"],
    [/\bice cream\b/, "🍨"], [/\bfrozen\b/, "🧊"],
    [/\bnapkins\b/, "🧻"], [/\bshampoo\b/, "🧴"], [/\bsoap\b/, "🧼"],
    [/\bdetergent\b/, "🧺"], [/\btoilet\b/, "🚽"], [/\bvitamins\b/, "💊"],
    [/\bdishes\b/, "🍽️"], [/\bkitchen\b/, "🍽️"],
];

function emojiFor(product) {
    const name = product.toLowerCase();
    for (const [re, emoji] of EMOJI_RULES) {
        if (re.test(name)) return emoji;
    }
    return "🛒";
}

// ---- Theme --------------------------------------------------------
const themeBtn = document.getElementById("theme-toggle");
function applyTheme(theme) {
    document.documentElement.dataset.theme = theme;
    themeBtn.textContent = theme === "dark" ? "🌙" : "☀️";
    try { localStorage.setItem("theme", theme); } catch (_) { /* no-op */ }
}
const savedTheme = (() => { try { return localStorage.getItem("theme"); } catch (_) { return null; } })();
applyTheme(savedTheme === "light" ? "light" : "dark");
themeBtn.addEventListener("click", () => {
    const next = document.documentElement.dataset.theme === "dark" ? "light" : "dark";
    applyTheme(next);
});

// ---- Navigation ---------------------------------------------------
document.querySelectorAll(".nav-btn").forEach((btn) => {
    btn.addEventListener("click", () => {
        document.querySelectorAll(".nav-btn").forEach((b) => b.classList.remove("active"));
        document.querySelectorAll(".view").forEach((v) => v.classList.remove("active"));
        btn.classList.add("active");
        const view = document.getElementById("view-" + btn.dataset.view);
        if (view) view.classList.add("active");
        window.scrollTo({ top: 0 });
    });
});
document.querySelectorAll("[data-goto]").forEach((link) => {
    link.addEventListener("click", (e) => {
        e.preventDefault();
        document.querySelector(`.nav-btn[data-view="${link.dataset.goto}"]`).click();
    });
});

// ---- Toast --------------------------------------------------------
const toast = document.getElementById("toast");
let toastTimer = null;
function showToast(message) {
    toast.textContent = message;
    toast.hidden = false;
    clearTimeout(toastTimer);
    toastTimer = setTimeout(() => { toast.hidden = true; }, 1800);
}

// ---- Storefront ---------------------------------------------------
const aislesEl = document.getElementById("aisles");
const searchInput = document.getElementById("product-search");

function renderStorefront(filter) {
    const query = (filter || "").trim().toLowerCase();
    aislesEl.innerHTML = "";

    const visibleAisles = AISLES
        .map((aisle) => ({
            ...aisle,
            products: aisle.products.filter((p) => !query || p.toLowerCase().includes(query)),
        }))
        .filter((aisle) => aisle.products.length > 0);

    if (visibleAisles.length === 0) {
        aislesEl.innerHTML = '<p class="empty-state">No products match your search.</p>';
        return;
    }

    visibleAisles.forEach((aisle) => {
        const section = document.createElement("div");
        section.className = "aisle";
        section.innerHTML =
            '<h3>' + emojiFor(aisle.name) + " " + escapeHtml(aisle.name) +
            ' <span class="aisle-count">' + aisle.products.length + " products</span></h3>";

        const grid = document.createElement("div");
        grid.className = "product-grid";

        aisle.products.forEach((product) => {
            grid.appendChild(buildProductCard(product));
        });

        section.appendChild(grid);
        aislesEl.appendChild(section);
    });
}

function buildProductCard(product) {
    const card = document.createElement("button");
    card.type = "button";
    card.className = "product-card";
    card.dataset.product = product;
    card.innerHTML =
        '<span class="emoji">' + emojiFor(product) + "</span>" +
        '<span class="name">' + escapeHtml(product) + "</span>";

    card.addEventListener("click", () => toggleProduct(product));
    return card;
}

function toggleProduct(product) {
    const index = basket.indexOf(product);
    if (index >= 0) {
        basket.splice(index, 1);
        showToast("Removed " + product);
    } else {
        basket.push(product);
        showToast("Added " + product + " 🛒");
    }
    refreshBasketUI();
}

searchInput.addEventListener("input", () => renderStorefront(searchInput.value));

// ---- Basket -------------------------------------------------------
const basketList = document.getElementById("basket-list");
const basketEmpty = document.getElementById("basket-empty");
const basketCount = document.getElementById("basket-count");
const recommendBtn = document.getElementById("recommend-btn");
const clearBtn = document.getElementById("clear-basket");

function refreshBasketUI() {
    // badge + recommend button state
    basketCount.hidden = basket.length === 0;
    basketCount.textContent = basket.length;
    recommendBtn.disabled = basket.length === 0;

    // highlight cards in the storefront
    document.querySelectorAll(".product-card").forEach((card) => {
        card.classList.toggle("in-basket", basket.includes(card.dataset.product));
    });

    // basket list
    if (basket.length === 0) {
        basketList.innerHTML = "";
        basketEmpty.style.display = "";
        return;
    }
    basketEmpty.style.display = "none";
    basketList.innerHTML = "";
    basket.forEach((product) => {
        const chip = document.createElement("span");
        chip.className = "chip";
        chip.textContent = emojiFor(product) + " " + product;

        const remove = document.createElement("button");
        remove.type = "button";
        remove.textContent = "\u00d7";
        remove.setAttribute("aria-label", "Remove " + product);
        remove.onclick = () => {
            basket = basket.filter((item) => item !== product);
            refreshBasketUI();
        };
        chip.appendChild(remove);
        basketList.appendChild(chip);
    });
}

clearBtn.addEventListener("click", () => {
    basket = [];
    refreshBasketUI();
    const results = document.getElementById("results");
    results.innerHTML = '<p class="empty-state">Your recommendations will appear here.</p>';
});

// ---- Recommendations ----------------------------------------------
const resultsEl = document.getElementById("results");

async function fetchRecommendations() {
    if (basket.length === 0) return;

    recommendBtn.disabled = true;
    recommendBtn.textContent = "Analysing basket...";
    resultsEl.innerHTML = '<p class="empty-state">Analysing 898 rules...</p>';

    try {
        const response = await fetch("/api/recommend", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ products: basket }),
        });
        const data = await response.json();

        if (!response.ok) {
            showStatus(data.error || "Something went wrong.");
            return;
        }
        if (data.message) {
            showStatus(data.message);
            return;
        }
        renderRecommendations(data.recommendations);
    } catch (error) {
        showStatus("Could not reach the server. Is the Flask app running?");
    } finally {
        recommendBtn.disabled = false;
        recommendBtn.textContent = "✨ Get Recommendations";
    }
}

function renderRecommendations(recommendations) {
    resultsEl.innerHTML = "";
    if (recommendations.length === 0) {
        resultsEl.innerHTML = '<p class="empty-state">No strong associations found for this basket yet.</p>';
        return;
    }

    recommendations.forEach((rec) => {
        const card = document.createElement("div");
        card.className = "rec-card";
        card.innerHTML =
            '<span class="rec-emoji">' + emojiFor(rec.product) + "</span>" +
            '<div class="rec-name">' + escapeHtml(rec.product) + "</div>" +
            '<div class="rec-rule">because you bought: ' + escapeHtml(rec.rule) + "</div>" +
            '<div class="conf-bar"><div class="fill" style="width:' +
            Math.round(rec.confidence * 100) + '%"></div></div>' +
            '<div class="rec-metrics">' +
            "<strong>" + Math.round(rec.confidence * 100) + "% confidence</strong>" +
            "<span>lift " + rec.lift + "</span></div>";
        resultsEl.appendChild(card);
    });
}

function showStatus(message) {
    resultsEl.innerHTML = '<p class="status error">' + escapeHtml(message) + "</p>";
}

recommendBtn.addEventListener("click", fetchRecommendations);

// ---- Rule explorer ------------------------------------------------
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
        rulesTbody.innerHTML = '<tr><td colspan="4" class="empty-cell">Could not load rules.</td></tr>';
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

function renderRuleScatter(rules) {
    if (rules.length === 0) {
        ruleScatter.innerHTML = '<p class="scatter-empty">No rules to plot.</p>';
        return;
    }

    const W = 380, H = 320, PAD = 40;
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
        const t = zMax > zMin ? (r.lift - zMin) / (zMax - zMin) : 0.5;
        const hue = 230 * (1 - t);
        circles += '<circle cx="' + px(r.support).toFixed(1) +
            '" cy="' + py(r.confidence).toFixed(1) +
            '" r="4" fill="hsl(' + hue + ', 80%, 55%)" opacity="0.85">' +
            "<title>" + escapeHtml(r.antecedents.join(", ") + " -> " +
            r.consequents.join(", ") + "  (lift " + r.lift.toFixed(2) + ")") +
            "</title></circle>";
    });

    ruleScatter.innerHTML =
        '<svg viewBox="0 0 ' + W + " " + H + '" class="scatter-svg" role="img">' +
        '<text x="' + (W / 2) + '" y="18" text-anchor="middle" font-weight="bold">' +
        "Support vs Confidence</text>" +
        '<line x1="' + PAD + '" y1="' + (H - PAD) + '" x2="' + (W - PAD) +
        '" y2="' + (H - PAD) + '" stroke="#888"></line>' +
        '<line x1="' + PAD + '" y1="' + PAD + '" x2="' + PAD + '" y2="' +
        (H - PAD) + '" stroke="#888"></line>' +
        '<text x="' + (W / 2) + '" y="' + (H - 8) +
        '" text-anchor="middle" font-size="11">Support</text>' +
        '<text x="14" y="' + (H / 2) +
        '" text-anchor="middle" font-size="11" transform="rotate(-90 14 ' +
        (H / 2) + ')">Confidence</text>' +
        '<text x="' + (W - PAD) + '" y="' + (H - 14) + '" text-anchor="end" ' +
        'font-size="10">' + xMax.toFixed(3) + "</text>" +
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

// ---- Helpers & init ----------------------------------------------
function escapeHtml(text) {
    return String(text).replace(/[&<>"']/g, (ch) => ({
        "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;",
    }[ch]));
}

renderStorefront("");
fetchRules();
refreshBasketUI();
