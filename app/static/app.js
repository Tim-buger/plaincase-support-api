const form = document.querySelector("#extract-form");
const button = document.querySelector("#run-button");
const emptyState = document.querySelector("#empty-state");
const result = document.querySelector("#result");
const errorBox = document.querySelector("#error");
const validationBadge = document.querySelector("#validation-badge");

const setText = (id, value) => {
  document.querySelector(`#${id}`).textContent = value;
};

form.addEventListener("submit", async (event) => {
  event.preventDefault();
  button.disabled = true;
  button.querySelector("span").textContent = "Processing…";
  errorBox.classList.add("hidden");
  result.classList.add("hidden");
  emptyState.classList.remove("hidden");
  validationBadge.classList.remove("valid");
  validationBadge.textContent = "RUNNING";

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
    setText("cache", meta.cached ? "HIT" : "MISS");
    setText("run-id", `RUN / ${meta.request_id.toUpperCase()}`);
    validationBadge.textContent = "VALIDATED";
    validationBadge.classList.add("valid");
    emptyState.classList.add("hidden");
    result.classList.remove("hidden");
  } catch (error) {
    emptyState.classList.add("hidden");
    errorBox.textContent = error.message;
    errorBox.classList.remove("hidden");
    validationBadge.textContent = "FAILED";
  } finally {
    button.disabled = false;
    button.querySelector("span").textContent = "Run extraction";
  }
});

