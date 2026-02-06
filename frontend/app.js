"use strict";

// Base URL for the backend API
const API_URL = "http://localhost:8000";

// Simple in-memory counters for UI stats
let docsCount = 0;
let chunksCount = 0;
let questionsCount = 0;

// Attach event listeners once DOM is available
document.addEventListener("DOMContentLoaded", () => {
  const fileInput = document.getElementById("fileInput");
  if (fileInput) {
    fileInput.addEventListener("change", uploadFile);
  }

  // Initialize stats on load
  syncStats();
});

// -----------------------------
// Helper functions for the UI
// -----------------------------

function setStatusBadge(text) {
  const el = document.getElementById("statStatus");
  if (el) el.textContent = text;
}

function syncStats() {
  const d = document.getElementById("statDocs");
  const c = document.getElementById("statChunks");
  const q = document.getElementById("statQuestions");

  if (d) d.textContent = String(docsCount);
  if (c) c.textContent = String(chunksCount);
  if (q) q.textContent = String(questionsCount);
}

// Scrolls smoothly to the app section and focuses the question input
function scrollToApp() {
  const app = document.getElementById("app");
  if (!app) return;

  app.scrollIntoView({ behavior: "smooth", block: "start" });
  setTimeout(() => document.getElementById("questionInput")?.focus(), 350);
}

// Opens the file chooser
function triggerUpload() {
  document.getElementById("fileInput")?.click();
}

// -----------------------------
// Upload handling
// -----------------------------

async function uploadFile(event) {
  const file = event.target.files[0];
  if (!file) return;

  const formData = new FormData();
  formData.append("file", file);

  const status = document.getElementById("status");
  const docList = document.getElementById("docList");
  if (!status || !docList) return;

  status.textContent = "Uploading...";
  status.className = "status";
  status.style.display = "block";
  setStatusBadge("Uploading");

  try {
    const response = await fetch(`${API_URL}/upload`, {
      method: "POST",
      body: formData,
    });

    const data = await response.json();

    if (response.ok) {
      status.textContent = `✓ ${data.filename} uploaded successfully! (${data.chunks} chunks processed)`;
      status.className = "status success";

      // Update document list UI
      docList.classList.remove("empty");
      const current = docList.innerHTML.trim();
      const docLine = `<div>${data.filename} · <span style="color:#60a5fa">${data.chunks} chunks</span></div>`;
      if (!current || current.startsWith("No documents")) {
        docList.innerHTML = docLine;
      } else {
        docList.innerHTML = current + docLine;
      }

      docsCount += 1;
      chunksCount += Number(data.chunks || 0);
      syncStats();
      setStatusBadge("Ready");
      document.getElementById("questionInput")?.focus();
    } else {
      status.textContent = `✗ Error: ${data.detail}`;
      status.className = "status error";
      setStatusBadge("Error");
    }
  } catch (error) {
    status.textContent = `✗ Error: ${error.message}`;
    status.className = "status error";
    setStatusBadge("Offline");
  }
}

// -----------------------------
// Question / answer handling
// -----------------------------

async function askQuestion() {
  const questionInput = document.getElementById("questionInput");
  if (!questionInput) return;

  const question = questionInput.value.trim();
  if (!question) return;

  const chatBox = document.getElementById("chatBox");
  const askBtn = document.getElementById("askBtn");
  if (!chatBox || !askBtn) return;

  // Add question to chat
  const questionDiv = document.createElement("div");
  questionDiv.className = "message question";
  questionDiv.textContent = question;
  chatBox.appendChild(questionDiv);

  // Clear input
  questionInput.value = "";

  // Show loading
  const loadingDiv = document.createElement("div");
  loadingDiv.className = "loading";
  loadingDiv.textContent = "Thinking...";
  chatBox.appendChild(loadingDiv);
  setStatusBadge("Thinking");

  // Disable button
  askBtn.disabled = true;

  try {
    const response = await fetch(`${API_URL}/ask`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({ question }),
    });

    const data = await response.json();

    // Remove loading
    chatBox.removeChild(loadingDiv);

    // Check if response has error (even if status is 200, backend might return error in answer)
    if (!response.ok) {
      const errorMsg = data.detail || data.error || `Server error (${response.status})`;
      const errorDiv = document.createElement("div");
      errorDiv.className = "message answer";
      errorDiv.innerHTML = `
        <div style="color: #fecaca; font-weight: 600;">⚠️ Error ${response.status}</div>
        <div style="margin-top: 8px; white-space: pre-wrap; font-size: 13px;">${errorMsg}</div>
        ${
          data.sources && data.sources.length > 0
            ? `
              <div class="sources">
                  Sources: ${data.sources
                    .map((s) => `${s.source} (chunk ${s.chunk})`)
                    .join(", ")}
              </div>
          `
            : ""
        }
      `;
      chatBox.appendChild(errorDiv);
      setStatusBadge("Error");
    } else {
      // Add answer to chat
      const answerDiv = document.createElement("div");
      answerDiv.className = "message answer";
      answerDiv.innerHTML = `
        <div>${data.answer}</div>
        ${
          data.sources && data.sources.length > 0
            ? `
              <div class="sources">
                  Sources: ${data.sources
                    .map((s) => `${s.source} (chunk ${s.chunk})`)
                    .join(", ")}
              </div>
          `
            : ""
        }
      `;
      chatBox.appendChild(answerDiv);

      // Scroll to bottom
      chatBox.scrollTop = chatBox.scrollHeight;

      questionsCount += 1;
      syncStats();
      setStatusBadge("Ready");
    }
  } catch (error) {
    chatBox.removeChild(loadingDiv);
    const errorDiv = document.createElement("div");
    errorDiv.className = "message answer";
    errorDiv.innerHTML = `
      <div style="color: #fecaca; font-weight: 600;">⚠️ Connection Error</div>
      <div style="margin-top: 8px; font-size: 13px;">${error.message}</div>
      <div style="margin-top: 8px; font-size: 12px; color: rgba(148,163,184,0.8);">
          Make sure the backend server is running on port 8000.
      </div>
    `;
    chatBox.appendChild(errorDiv);
    setStatusBadge("Offline");
  }

  // Re-enable button
  askBtn.disabled = false;
}

// Clear all documents + reset UI
async function clearDatabase() {
  if (!confirm("Are you sure you want to clear all documents?")) return;

  try {
    const response = await fetch(`${API_URL}/clear`, {
      method: "DELETE",
    });

    const data = await response.json();
    alert(data.message);

    // Clear chat
    const chatBox = document.getElementById("chatBox");
    if (chatBox) {
      chatBox.innerHTML = "";
    }

    // Reset document list
    const docList = document.getElementById("docList");
    if (docList) {
      docList.classList.add("empty");
      docList.textContent = "No documents yet. Upload a PDF to get started.";
    }

    docsCount = 0;
    chunksCount = 0;
    questionsCount = 0;
    syncStats();
    setStatusBadge("Ready");
  } catch (error) {
    alert(`Error: ${error.message}`);
    setStatusBadge("Error");
  }
}

// Handle pressing Enter in the question input
function handleKeyPress(event) {
  if (event.key === "Enter") {
    askQuestion();
  }
}

