for (const openButton of document.querySelectorAll("[data-report-dialog-open]")) {
  const dialogId = openButton.getAttribute("aria-controls");
  const reportDialog = dialogId ? document.getElementById(dialogId) : null;

  if (!(reportDialog instanceof HTMLDialogElement)) continue;

  const closeDialog = () => reportDialog.close();
  openButton.addEventListener("click", () => reportDialog.showModal());
  const typeOptions = reportDialog.querySelectorAll(
    'input[name="report_type"]',
  );
  typeOptions.forEach((option) => {
    option.addEventListener("change", () => {
      typeOptions.forEach((candidate) => {
        candidate.closest(".report-form__type-option")?.classList.toggle(
          "report-form__type-option--selected",
          candidate.checked,
        );
      });
    });
  });
  const reasonOptions = reportDialog.querySelectorAll('input[name="reason"]');
  const customReasonContainer = reportDialog.querySelector(
    "[data-report-custom-reason-container]",
  );
  const customReason = reportDialog.querySelector("[data-report-custom-reason]");
  const updateCustomReasonVisibility = () => {
    const otherReason = reportDialog.querySelector('[data-report-other]');
    const showCustomReason = otherReason instanceof HTMLInputElement && otherReason.checked;
    if (customReasonContainer) customReasonContainer.hidden = !showCustomReason;
    if (customReason instanceof HTMLInputElement) {
      customReason.disabled = !showCustomReason;
      customReason.required = showCustomReason;
    }
  };
  reasonOptions.forEach((option) => {
    option.addEventListener("change", updateCustomReasonVisibility);
  });
  updateCustomReasonVisibility();
  reportDialog
    .querySelector("[data-report-dialog-close]")
    ?.addEventListener("click", closeDialog);
  reportDialog
    .querySelector("[data-report-dialog-cancel]")
    ?.addEventListener("click", closeDialog);
  reportDialog.addEventListener("click", (event) => {
    if (event.target === reportDialog) closeDialog();
  });
}
