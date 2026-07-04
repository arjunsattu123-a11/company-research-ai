const chatWindow = document.getElementById("chatWindow");
const chatForm = document.getElementById("chatForm");
const queryInput = document.getElementById("queryInput");
const sendBtn = document.getElementById("sendBtn");
const modelSelect = document.getElementById("modelSelect");

const settingsToggle = document.getElementById("settingsToggle");
const settingsPanel = document.getElementById("settingsPanel");
const saveDiscordBtn = document.getElementById("saveDiscord");
const discordStatus = document.getElementById("discordStatus");

settingsToggle.addEventListener("click", () => {
  settingsPanel.classList.toggle("hidden");
});

saveDiscordBtn.addEventListener("click", async () => {
  const bot_token = document.getElementById("discordToken").value.trim();
  const channel_id = document.getElementById("discordChannel").value.trim();

  const resp = await fetch("/api/discord-config", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ bot_token, channel_id }),
  });

  if (resp.ok) {
    discordStatus.textContent = "✓ Discord configuration saved.";
  } else {
    discordStatus.textContent = "Failed to save configuration.";
  }
});

function addMessage(text, cls = "bot") {
  const div = document.createElement("div");
  div.className = `message ${cls}`;
  div.textContent = text;
  chatWindow.appendChild(div);
  chatWindow.scrollTop = chatWindow.scrollHeight;
  return div;
}

function renderReportCard(research, pagesCrawled, discordResult) {
  const card = document.createElement("div");
  card.className = "report-card";

  const products = (research.products_services || [])
    .map((p) => `<li>${p}</li>`).join("");
  const pains = (research.pain_points || [])
    .map((p) => `<li>${p}</li>`).join("");
  const competitorRows = (research.competitors || [])
    .map((c) => `<tr><td>${c.name || "N/A"}</td><td>${c.website || "N/A"}</td></tr>`)
    .join("");

  card.innerHTML = `
    <h3>${research.company_name || "Company"}</h3>
    <div class="row"><span class="label">Website:</span>${research.website || "N/A"}</div>
    <div class="row"><span class="label">Phone:</span>${research.phone || "N/A"}</div>
    <div class="row"><span class="label">Address:</span>${research.address || "N/A"}</div>
    <div class="row"><span class="label">Summary:</span>${research.summary || ""}</div>

    ${products ? `<div class="row label">Products / Services:</div><ul>${products}</ul>` : ""}
    ${pains ? `<div class="row label">AI-Generated Pain Points:</div><ul>${pains}</ul>` : ""}

    ${competitorRows ? `
      <div class="row label">Competitors:</div>
      <table>
        <tr><th>Name</th><th>Website</th></tr>
        ${competitorRows}
      </table>` : ""}

    <div class="row" style="margin-top:10px; color:#6c7280; font-size:12px;">
      Pages crawled: ${pagesCrawled.length}
      ${discordResult && discordResult.sent ? " · Sent to Discord ✓" : ""}
    </div>

    <a class="download-btn" href="/api/download/${research.pdf_filename}" target="_blank">
      ⬇ Download PDF Report
    </a>
  `;

  chatWindow.appendChild(card);
  chatWindow.scrollTop = chatWindow.scrollHeight;
}

chatForm.addEventListener("submit", async (e) => {
  e.preventDefault();
  const query = queryInput.value.trim();
  if (!query) return;

  addMessage(query, "user");
  queryInput.value = "";
  sendBtn.disabled = true;

  const progressSteps = [
    "🔎 Searching for the official website...",
    "🕸 Crawling important pages...",
    "🧠 Analyzing with AI...",
    "📄 Generating PDF report...",
  ];
  const progressEl = addMessage(progressSteps[0], "progress");

  let stepIndex = 0;
  const interval = setInterval(() => {
    stepIndex = (stepIndex + 1) % progressSteps.length;
    progressEl.textContent = progressSteps[stepIndex];
  }, 2500);

  try {
    const sendToDiscord = document.getElementById("sendToDiscord").checked;
    const applicant_name = document.getElementById("applicantName").value.trim();
    const applicant_email = document.getElementById("applicantEmail").value.trim();

    const resp = await fetch("/api/research", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        query,
        model: modelSelect.value,
        applicant_name,
        applicant_email,
        send_to_discord: sendToDiscord,
      }),
    });

    clearInterval(interval);
    progressEl.remove();

    const data = await resp.json();

    if (!resp.ok) {
      addMessage(`⚠ ${data.error || "Something went wrong."}`, "bot");
      return;
    }

    addMessage(`Here's what I found for ${data.research.company_name}:`, "bot");
    renderReportCard(data.research, data.pages_crawled, data.discord);
  } catch (err) {
    clearInterval(interval);
    progressEl.remove();
    addMessage("⚠ Network or server error. Please try again.", "bot");
  } finally {
    sendBtn.disabled = false;
  }
});
