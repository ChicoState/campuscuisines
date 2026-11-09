for (const openButton of document.querySelectorAll("[data-report-dialog-open]")) {
  const dialogId = openButton.getAttribute("aria-controls");
  const reportDialog = dialogId ? document.getElementById(dialogId) : null;

  if (!(reportDialog instanceof HTMLDialogElement)) continue;

  const closeDialog = () => reportDialog.close();
  openButton.addEventListener("click", () => reportDialog.showModal());
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
