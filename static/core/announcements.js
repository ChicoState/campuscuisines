(() => {
  const dialog = document.querySelector("[data-announcement-dialog]");
  const trigger = document.querySelector("[data-announcement-open]");
  const closeButton = document.querySelector("[data-announcement-close]");

  if (!dialog || !trigger || !closeButton) return;

  const closeDialog = () => {
    dialog.close();
    trigger.focus();
  };

  trigger.addEventListener("click", () => dialog.showModal());
  closeButton.addEventListener("click", closeDialog);
  dialog.addEventListener("click", (event) => {
    if (event.target === dialog) closeDialog();
  });
})();
