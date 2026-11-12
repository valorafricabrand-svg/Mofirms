const groupFields = document.querySelector("#groupFields");
const registrationType = document.querySelectorAll('input[name="registration_type"]');
const partnerSections = {
  supplier: document.querySelector("#supplierFields"),
  buyer: document.querySelector("#buyerFields"),
  service_provider: document.querySelector("#serviceFields"),
};
const sharedOfferFields = document.querySelector("#sharedOfferFields");
const partnerRoles = document.querySelectorAll('input[name="roles"]');
const documentRows = document.querySelector("#documentRows");
const addDocumentButton = document.querySelector("#addDocument");
const prototype = document.querySelector("#emptyDocumentRow");
const totalForms = document.querySelector("#id_documents-TOTAL_FORMS");
const maxDocuments = documentRows ? Number(documentRows.dataset.max) : 0;
const documentPrefix = documentRows?.dataset.prefix;

function updateGroupFields() {
  // No registration_type radios on this page (e.g. registration step 2, where
  // the server already rendered groupFields correctly) — leave it as is.
  if (!groupFields || registrationType.length === 0) return;
  const isGroup = document.querySelector('input[name="registration_type"]:checked')?.value === "group";
  groupFields.hidden = !isGroup;
  groupFields.disabled = !isGroup;
}

function updatePartnerSections() {
  if (!partnerSections.supplier) return;
  const selectedRoles = new Set(
    [...partnerRoles].filter((input) => input.checked).map((input) => input.value),
  );
  Object.entries(partnerSections).forEach(([role, section]) => {
    const active = selectedRoles.has(role);
    section.hidden = !active;
    section.disabled = !active;
  });
  const hasOffer = selectedRoles.has("supplier") || selectedRoles.has("service_provider");
  sharedOfferFields.hidden = !hasOffer;
  sharedOfferFields.disabled = !hasOffer;
}

function renumberDocumentRows() {
  if (!documentRows) return;
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
  if (!documentRows) return;
  if (documentRows.querySelectorAll(".document-row").length >= maxDocuments) return;
  const index = documentRows.querySelectorAll(".document-row").length;
  const row = document.createElement("div");
  row.innerHTML = prototype.innerHTML.replaceAll("__prefix__", String(index));
  documentRows.append(row.firstElementChild);
  renumberDocumentRows();
}

registrationType.forEach((radio) => radio.addEventListener("change", updateGroupFields));
partnerRoles.forEach((checkbox) => checkbox.addEventListener("change", updatePartnerSections));
addDocumentButton?.addEventListener("click", addDocumentRow);
documentRows?.addEventListener("click", (event) => {
  if (!event.target.classList.contains("remove-document")) return;
  event.target.closest(".document-row").remove();
  renumberDocumentRows();
});

updateGroupFields();
updatePartnerSections();
if (documentRows && documentRows.querySelectorAll(".document-row").length === 0) {
  addDocumentRow();
}
renumberDocumentRows();
