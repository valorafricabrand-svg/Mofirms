const groupFields = document.querySelector("#groupFields");
const registrationType = document.querySelectorAll('input[name="registration_type"]');
const documentRows = document.querySelector("#documentRows");
const addDocumentButton = document.querySelector("#addDocument");
const prototype = document.querySelector("#emptyDocumentRow");
const totalForms = document.querySelector("#id_documents-TOTAL_FORMS");
const maxDocuments = Number(documentRows.dataset.max);
const documentPrefix = documentRows.dataset.prefix;

function updateGroupFields() {
  const isGroup = document.querySelector('input[name="registration_type"]:checked')?.value === "group";
  groupFields.hidden = !isGroup;
  groupFields.disabled = !isGroup;
}

function renumberDocumentRows() {
  const rows = [...documentRows.querySelectorAll(".document-row")];
  rows.forEach((row, index) => {
    row.querySelectorAll("[name], [id], label[for]").forEach((element) => {
      for (const attribute of ["name", "id", "for"]) {
        const value = element.getAttribute(attribute);
        if (value) {
          element.setAttribute(
            attribute,
            value.replace(new RegExp(`${documentPrefix}-(?:\\d+|__prefix__)`), `${documentPrefix}-${index}`),
          );
        }
      }
    });
  });
  totalForms.value = String(rows.length);
  addDocumentButton.disabled = rows.length >= maxDocuments;
}

function addDocumentRow() {
  if (documentRows.querySelectorAll(".document-row").length >= maxDocuments) return;
  const index = documentRows.querySelectorAll(".document-row").length;
  const row = document.createElement("div");
  row.innerHTML = prototype.innerHTML.replaceAll("__prefix__", String(index));
  documentRows.append(row.firstElementChild);
  renumberDocumentRows();
}

registrationType.forEach((radio) => radio.addEventListener("change", updateGroupFields));
addDocumentButton.addEventListener("click", addDocumentRow);
documentRows.addEventListener("click", (event) => {
  if (!event.target.classList.contains("remove-document")) return;
  event.target.closest(".document-row").remove();
  renumberDocumentRows();
});

updateGroupFields();
if (documentRows.querySelectorAll(".document-row").length === 0) addDocumentRow();
renumberDocumentRows();
