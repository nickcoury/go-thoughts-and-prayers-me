/**
 * GoThoughtsAndPrayersMe — Frontend API Client & Renderer
 */

const API_BASE = "https://nickcoury.duckdns.org:8443/thoughts/api";

// ── API Helpers ───────────────────────────────────────────────────

async function api(path, options = {}) {
    const url = `${API_BASE}${path}`;
    const res = await fetch(url, {
        headers: { "Content-Type": "application/json", ...options.headers },
        ...options,
    });
    const data = await res.json();
    if (!res.ok) {
        throw new Error(data.error || `Request failed (${res.status})`);
    }
    return data;
}

const apiGet = (path) => api(path);
const apiPost = (path, body) => api(path, { method: "POST", body: JSON.stringify(body) });

// ── Formatting ────────────────────────────────────────────────────

function fmt(n) {
    if (n >= 1_000_000) return (n / 1_000_000).toFixed(1) + "M";
    if (n >= 1_000) return (n / 1_000).toFixed(1) + "K";
    return n.toString();
}

function timeAgo(iso) {
    const d = new Date(iso + "Z");
    const now = new Date();
    const secs = Math.floor((now - d) / 1000);
    if (secs < 60) return "just now";
    const mins = Math.floor(secs / 60);
    if (mins < 60) return `${mins}m ago`;
    const hrs = Math.floor(mins / 60);
    if (hrs < 24) return `${hrs}h ago`;
    const days = Math.floor(hrs / 24);
    if (days < 30) return `${days}d ago`;
    return d.toLocaleDateString();
}

function initials(name) {
    return name.split(" ").map(w => w[0]).join("").slice(0, 2).toUpperCase() || "?";
}

// ── Toast ─────────────────────────────────────────────────────────

function showToast(msg, type = "success") {
    const t = document.createElement("div");
    t.className = `toast toast-${type}`;
    t.textContent = msg;
    document.body.appendChild(t);
    setTimeout(() => { t.style.opacity = "0"; setTimeout(() => t.remove(), 300); }, 4000);
}

// ── Campaign Card ─────────────────────────────────────────────────

function renderCampaignCard(c) {
    const totalGoal = c.goal_thoughts + c.goal_prayers;
    const totalCurrent = c.current_thoughts + c.current_prayers;
    const pct = totalGoal > 0 ? Math.min((totalCurrent / totalGoal) * 100, 100) : 0;

    const emojis = ["🙏", "💭", "💚", "✨", "💡", "🕊️"];
    const emoji = emojis[Math.abs(hashCode(c.slug)) % emojis.length];

    return `
    <div class="campaign-card">
        <div class="card-image">${emoji}</div>
        <div class="card-body">
            <div class="card-title">
                <a href="campaign.html?slug=${esc(c.slug)}">${esc(c.title)}</a>
            </div>
            <div class="card-organizer">by ${esc(c.organizer_name)}</div>
            <div class="progress-section">
                <div class="progress-stats">
                    <span class="progress-current">${fmt(totalCurrent)} raised</span>
                    <span class="progress-goal">goal ${fmt(totalGoal)}</span>
                </div>
                <div class="progress-bar">
                    <div class="progress-fill" style="width:${pct}%"></div>
                </div>
            </div>
            <div class="card-desc">${esc(c.description).substring(0, 150)}...</div>
        </div>
    </div>`;
}

// ── Campaign Detail ───────────────────────────────────────────────

function renderCampaignDetail(c) {
    const totalGoal = c.goal_thoughts + c.goal_prayers;
    const totalCurrent = c.current_thoughts + c.current_prayers;
    const pct = totalGoal > 0 ? Math.min((totalCurrent / totalGoal) * 100, 100) : 0;

    document.getElementById("campaign-detail").innerHTML = `
        <div class="campaign-header">
            <h1>${esc(c.title)}</h1>
            <div class="campaign-meta">
                <span>👤 ${esc(c.organizer_name)}</span>
                <span>📅 ${new Date(c.created_at + "Z").toLocaleDateString("en-US", {year:"numeric", month:"long", day:"numeric"})}</span>
            </div>

            <div class="big-progress">
                <div class="progress-stats">
                    <div class="progress-stat-item">
                        <div class="progress-stat-value">${fmt(c.current_thoughts)}</div>
                        <div class="progress-stat-label">Thoughts</div>
                    </div>
                    <div class="progress-stat-item">
                        <div class="progress-stat-value">${fmt(c.current_prayers)}</div>
                        <div class="progress-stat-label">Prayers</div>
                    </div>
                </div>
                <div class="progress-bar">
                    <div class="progress-fill" style="width:${pct}%"></div>
                </div>
                <div style="text-align:center;margin-top:6px;font-size:.85rem;color:var(--text-muted)">
                    ${fmt(totalCurrent)} of ${fmt(totalGoal)} goal &middot; ${Math.round(pct)}% complete
                </div>
            </div>

            <div class="campaign-description">${esc(c.description)}</div>
        </div>`;

    // Donation form
    document.getElementById("donate-form-container").innerHTML = `
        <div class="donate-section">
            <h2>Send Your Support</h2>
            <form id="donate-form" onsubmit="handleDonate(event, '${esc(c.slug)}')">
                <div class="hp-field">
                    <input type="text" name="website" tabindex="-1" autocomplete="off">
                </div>
                <div class="form-group">
                    <label for="donor_name">Your Name</label>
                    <input type="text" id="donor_name" name="donor_name" maxlength="80" placeholder="Anonymous" autocomplete="name">
                </div>
                <div class="form-row">
                    <div class="form-group">
                        <label for="thoughts">💭 Thoughts</label>
                        <input type="number" id="thoughts" name="thoughts" min="0" max="1000000" value="1" required>
                        <div class="form-hint">Each thought is a moment of genuine consideration</div>
                    </div>
                    <div class="form-group">
                        <label for="prayers">🙏 Prayers</label>
                        <input type="number" id="prayers" name="prayers" min="0" max="1000000" value="0" required>
                        <div class="form-hint">Prayers are directed to the appropriate deity or universal force</div>
                    </div>
                </div>
                <div class="form-group">
                    <label for="message">Message of Support</label>
                    <textarea id="message" name="message" maxlength="1000" placeholder="Share a few words of encouragement..."></textarea>
                </div>
                <button type="submit" class="btn btn-primary btn-lg" style="width:100%">
                    💚 Send Thoughts &amp; Prayers
                </button>
            </form>
        </div>`;

    // Donations list
    const donations = c.donations || [];
    let donationsHTML = "";
    if (donations.length > 0) {
        donationsHTML = donations.map(d => `
            <div class="donation-item">
                <div class="donation-avatar">${initials(d.donor_name)}</div>
                <div class="donation-content">
                    <div class="donation-header">
                        <span class="donation-name">${esc(d.donor_name)}</span>
                        <span class="donation-amount">
                            ${d.thoughts > 0 ? `💭 ${fmt(d.thoughts)}` : ""}
                            ${d.thoughts > 0 && d.prayers > 0 ? " &middot; " : ""}
                            ${d.prayers > 0 ? `🙏 ${fmt(d.prayers)}` : ""}
                        </span>
                    </div>
                    <div class="donation-time">${timeAgo(d.created_at)}</div>
                    ${d.message ? `<div class="donation-message">${esc(d.message)}</div>` : ""}
                </div>
            </div>
        `).join("");
    } else {
        donationsHTML = `<div class="empty-state">
            <div class="empty-icon">💭</div>
            <h3>No support yet</h3>
            <p>Be the first to send thoughts and prayers.</p>
        </div>`;
    }

    document.getElementById("donations-list").innerHTML = `
        <div class="donations-section">
            <h2>Recent Support (${donations.length})</h2>
            ${donationsHTML}
        </div>`;
}

// ── Donate Handler ────────────────────────────────────────────────

async function handleDonate(e, slug) {
    e.preventDefault();
    const form = e.target;
    const btn = form.querySelector("button[type=submit]");
    const origText = btn.textContent;
    btn.disabled = true;
    btn.textContent = "Sending...";

    try {
        const data = {
            donor_name: form.donor_name.value.trim() || "Anonymous",
            thoughts: parseInt(form.thoughts.value) || 0,
            prayers: parseInt(form.prayers.value) || 0,
            message: form.message.value.trim(),
            website: form.website?.value || "", // honeypot
        };

        const updated = await apiPost(`/campaigns/${slug}/donate`, data);
        showToast("Your thoughts and prayers have been received. Thank you. 💚");
        renderCampaignDetail(updated);
        form.thoughts.value = 1;
        form.prayers.value = 0;
        form.message.value = "";
    } catch (err) {
        showToast(err.message || "Something went wrong.", "error");
    } finally {
        btn.disabled = false;
        btn.textContent = origText;
    }
}

// ── Create Campaign Handler ───────────────────────────────────────

async function handleCreate(e) {
    e.preventDefault();
    const form = e.target;
    const btn = form.querySelector("button[type=submit]");
    const origText = btn.textContent;
    btn.disabled = true;
    btn.textContent = "Creating...";

    try {
        const data = {
            title: form.title.value.trim(),
            description: form.description.value.trim(),
            organizer_name: form.organizer_name.value.trim() || "Anonymous",
            goal_thoughts: parseInt(form.goal_thoughts.value) || 0,
            goal_prayers: parseInt(form.goal_prayers.value) || 0,
            website: form.website?.value || "",
        };

        const campaign = await apiPost("/campaigns", data);
        window.location.href = `campaign.html?slug=${campaign.slug}`;
    } catch (err) {
        showToast(err.message || "Something went wrong.", "error");
        btn.disabled = false;
        btn.textContent = origText;
    }
}

// ── Utility ───────────────────────────────────────────────────────

function esc(s) {
    if (!s) return "";
    const div = document.createElement("div");
    div.textContent = s;
    return div.innerHTML;
}

function hashCode(s) {
    let h = 0;
    for (let i = 0; i < s.length; i++) {
        h = ((h << 5) - h + s.charCodeAt(i)) | 0;
    }
    return h;
}

function getParam(name) {
    return new URLSearchParams(window.location.search).get(name);
}
