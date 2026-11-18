const questionRows = document.querySelector("#researchQuestionRows");
const questionPrototype = document.querySelector("#emptyResearchQuestionRow");
const questionTotal = document.querySelector("#id_questions-TOTAL_FORMS");
const addQuestionButton = document.querySelector("#addResearchQuestion");
const questionLimit = questionRows ? Number(questionRows.dataset.max) : 0;
const questionPrefix = questionRows?.dataset.prefix;

function renumberQuestions() {
  if (!questionRows) return;
  const rows = [...questionRows.querySelectorAll(".research-question-row")];
  rows.forEach((row, index) => {
    row.querySelectorAll("[name], [id], label[for]").forEach((element) => {
      for (const attribute of ["name", "id", "for"]) {
        const value = element.getAttribute(attribute);
        if (value) {
          element.setAttribute(
            attribute,
            value.replace(
              new RegExp(`${questionPrefix}-(?:\\d+|__prefix__)`),
              `${questionPrefix}-${index}`,
            ),
          );
        }
      }
    });
  });
  questionTotal.value = String(rows.length);
  addQuestionButton.disabled = rows.length >= questionLimit;
}

function addQuestionRow() {
  if (!questionRows || questionRows.querySelectorAll(".research-question-row").length >= questionLimit) {
    return;
  }
  const index = questionRows.querySelectorAll(".research-question-row").length;
  const row = document.createElement("div");
  row.innerHTML = questionPrototype.innerHTML.replaceAll("__prefix__", String(index));
  questionRows.append(row.firstElementChild);
  renumberQuestions();
}

addQuestionButton?.addEventListener("click", addQuestionRow);
questionRows?.addEventListener("click", (event) => {
  if (!event.target.classList.contains("remove-document")) return;
  event.target.closest(".research-question-row").remove();
  renumberQuestions();
});
renumberQuestions();

document.querySelectorAll(".multiselect").forEach((details) => {
  const summaryText = details.querySelector(".multiselect-summary-text");
  const placeholder = summaryText.dataset.placeholder;
  const countTemplate = summaryText.dataset.countTemplate;
  const checkboxes = [...details.querySelectorAll('input[type="checkbox"]')];
  function updateSummary() {
    const selected = checkboxes.filter((c) => c.checked).map((c) => c.closest(".choice").textContent.trim());
    if (selected.length === 0) summaryText.textContent = placeholder;
    else if (selected.length <= 2) summaryText.textContent = selected.join(", ");
    else summaryText.textContent = countTemplate.replace("{count}", String(selected.length));
  }
  checkboxes.forEach((c) => c.addEventListener("change", updateSummary));
  updateSummary();
});
