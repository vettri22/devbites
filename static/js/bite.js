// DevBites - bite detail page interactions

document.addEventListener("DOMContentLoaded", () => {
  const completeBtn = document.getElementById("completeBtn");
  const uncompleteBtn = document.getElementById("uncompleteBtn");

  if (completeBtn) {
    completeBtn.addEventListener("click", async () => {
      const biteId = completeBtn.dataset.biteId;
      completeBtn.disabled = true;
      completeBtn.textContent = "Saving...";
      try {
        const result = await postForm(`/bites/${biteId}/complete`);
        if (result.success) {
          completeBtn.textContent = "Completed";
          completeBtn.classList.remove("btn-success");
          completeBtn.classList.add("btn-outline");
          if (uncompleteBtn) uncompleteBtn.style.display = "";
          showToast(`+10 XP earned! Now Level ${result.level}, ${result.streak} day streak 🔥`);
        }
      } catch (e) {
        completeBtn.disabled = false;
        completeBtn.textContent = "Mark Complete";
      }
    });
  }

  if (uncompleteBtn) {
    uncompleteBtn.addEventListener("click", async () => {
      const biteId = uncompleteBtn.dataset.biteId;
      uncompleteBtn.disabled = true;
      try {
        const result = await postForm(`/bites/${biteId}/uncomplete`);
        if (result.success) {
          uncompleteBtn.style.display = "none";
          uncompleteBtn.disabled = false;
          if (completeBtn) {
            completeBtn.disabled = false;
            completeBtn.textContent = "Mark Complete";
            completeBtn.classList.remove("btn-outline");
            completeBtn.classList.add("btn-success");
          }
          showToast("Marked as incomplete. You can redo this lesson anytime.");
        }
      } catch (e) {
        uncompleteBtn.disabled = false;
      }
    });
  }

  document.querySelectorAll(".quiz-question").forEach((qEl) => {
    qEl.querySelectorAll(".quiz-option").forEach((opt) => {
      opt.addEventListener("click", () => {
        qEl.querySelectorAll(".quiz-option").forEach((o) => o.classList.remove("selected"));
        opt.classList.add("selected");
        qEl.dataset.selected = opt.dataset.option;
      });
    });
  });

  const quizForm = document.getElementById("quizForm");
  if (quizForm) {
    quizForm.addEventListener("submit", async (e) => {
      e.preventDefault();
      const answers = {};
      document.querySelectorAll(".quiz-question").forEach((qEl) => {
        const qid = qEl.dataset.questionId;
        if (qEl.dataset.selected) answers[qid] = qEl.dataset.selected;
      });

      const result = await postJSON(`/bites/${window.BITE_ID}/quiz`, { answers });
      const resultEl = document.getElementById("quizResult");

      if (result.success) {
        const xpNote = result.xp_awarded
          ? ""
          : " (XP already earned on a previous attempt)";
        resultEl.innerHTML = `You scored <strong>${result.score}/${result.total}</strong>. Total XP: ${result.xp}${xpNote}`;
        result.results.forEach((r) => {
          const qEl = document.querySelector(`.quiz-question[data-question-id="${r.question_id}"]`);
          if (!qEl) return;
          qEl.querySelectorAll(".quiz-option").forEach((opt) => {
            if (opt.dataset.option === r.correct_option) opt.classList.add("correct");
            else if (opt.classList.contains("selected") && !r.correct) opt.classList.add("incorrect");
          });
          const expEl = qEl.querySelector(".explanation");
          if (expEl && r.explanation) {
            expEl.textContent = "💡 " + r.explanation;
            expEl.style.display = "block";
          }
        });
        quizForm.querySelector("button[type=submit]").disabled = true;
      }
    });
  }
});

function showToast(message) {
  const toast = document.createElement("div");
  toast.textContent = message;
  toast.style.position = "fixed";
  toast.style.bottom = "24px";
  toast.style.right = "24px";
  toast.style.background = "#0f172a";
  toast.style.color = "#fff";
  toast.style.padding = "14px 20px";
  toast.style.borderRadius = "10px";
  toast.style.boxShadow = "0 8px 24px rgba(0,0,0,0.2)";
  toast.style.zIndex = "1000";
  document.body.appendChild(toast);
  setTimeout(() => {
    toast.style.transition = "opacity 0.4s";
    toast.style.opacity = "0";
    setTimeout(() => toast.remove(), 400);
  }, 4000);
}
