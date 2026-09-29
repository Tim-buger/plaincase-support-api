const form = document.querySelector("#extract-form");
const button = document.querySelector("#run-button");
const emptyState = document.querySelector("#empty-state");
const result = document.querySelector("#result");
const errorBox = document.querySelector("#error");
const validationBadge = document.querySelector("#validation-badge");
const activityAnalysis = document.querySelector("#activity-analysis");

const tickets = [
  {
    number: "#PC-1847",
    title: "Checkout API timing out",
    name: "Marta Ruiz",
    email: "marta@willowandpine.co",
    initials: "MR",
    time: "Today, 10:42",
    message:
      "Our production API has been timing out for 40 minutes and all customer checkouts are blocked. This happened again after yesterday's deployment. Please help ASAP.",
  },
  {
    number: "#PC-1846",
    title: "Duplicate invoice charge",
    name: "Darren Okafor",
    email: "darren@northstarlabs.io",
    initials: "DO",
    time: "Today, 10:36",
    message:
      "We were charged twice for invoice #INV-8421 after upgrading our plan. Please review the duplicate payment and let me know when the refund will be issued.",
  },
  {
    number: "#PC-1845",
    title: "Cannot invite a teammate",
    name: "Keiko Tanaka",
    email: "keiko@studiokinu.jp",
    initials: "KT",
    time: "Today, 10:30",
    message:
      "The invite link expires immediately after I send it to a new teammate. This is not urgent, but could you help us restore access this week?",
  },
];

const setText = (id, value) => {
  document.querySelector(`#${id}`).textContent = value;
};

document.querySelectorAll(".ticket").forEach((ticketButton, index) => {
  ticketButton.addEventListener("click", () => {
    const ticket = tickets[index];
    document.querySelectorAll(".ticket").forEach((item) => item.classList.remove("active"));
    ticketButton.classList.add("active");
    setText("ticket-number", ticket.number);
    setText("ticket-title", ticket.title);
    setText("customer-avatar", ticket.initials);
    setText("customer-name", ticket.name);
    setText("customer-email", ticket.email);
    setText("ticket-time", ticket.time);
    document.querySelector("#message").value = ticket.message;
    result.classList.add("hidden");
    errorBox.classList.add("hidden");
    activityAnalysis.classList.add("hidden");
    emptyState.classList.remove("hidden");
    validationBadge.classList.remove("valid");
    validationBadge.textContent = "Not analyzed";
  });
});

const searchInput = document.querySelector(".search-field input");
searchInput.addEventListener("input", () => {
  const query = searchInput.value.trim().toLowerCase();
  document.querySelectorAll(".ticket").forEach((ticketButton) => {
    ticketButton.classList.toggle("hidden", !ticketButton.textContent.toLowerCase().includes(query));
  });
});

document.querySelector(".icon-button").addEventListener("click", () => {
  searchInput.value = "";
  document.querySelectorAll(".ticket").forEach((ticketButton) => {
    ticketButton.classList.remove("hidden");
  });
  searchInput.focus();
});

form.addEventListener("submit", async (event) => {
  event.preventDefault();
  button.disabled = true;
  button.querySelector("span").textContent = "Analyzing…";
  errorBox.classList.add("hidden");
  result.classList.add("hidden");
  emptyState.classList.remove("hidden");
  validationBadge.classList.remove("valid");
  validationBadge.textContent = "Analyzing";

  const idempotencyKey = crypto.randomUUID();
  try {
    const response = await fetch("/api/v1/extract/support-ticket", {
      method: "POST",
      headers: { "Content-Type": "application/json", "Idempotency-Key": idempotencyKey },
      body: JSON.stringify({
        text: document.querySelector("#message").value,
        provider: document.querySelector("#provider").value,
      }),
    });
    const payload = await response.json();
    if (!response.ok) throw new Error(payload.detail?.message || "Extraction failed");

    const { data, meta } = payload;
    setText("priority", data.priority);
    setText("category", data.category);
    setText("summary", data.summary);
    setText("next-action", data.next_action);
    setText("sentiment", data.sentiment);
    setText("human-review", data.requires_human ? "required" : "not required");
    setText("tags", data.tags.join(" · "));
    setText("latency", `${meta.latency_ms} ms`);
    setText("attempts", meta.attempts);
    setText("model", meta.model);
    setText("cache", meta.cached ? "hit" : "miss");
    setText("run-id", meta.request_id);
    validationBadge.textContent = "Validated";
    validationBadge.classList.add("valid");
    emptyState.classList.add("hidden");
    result.classList.remove("hidden");
    activityAnalysis.classList.remove("hidden");
  } catch (error) {
    emptyState.classList.add("hidden");
    errorBox.textContent = error.message;
    errorBox.classList.remove("hidden");
    validationBadge.textContent = "Analysis failed";
  } finally {
    button.disabled = false;
    button.querySelector("span").textContent = "Analyze request";
  }
});
