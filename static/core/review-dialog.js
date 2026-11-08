const reviewDialog = document.querySelector("#review-dialog");

if (reviewDialog instanceof HTMLDialogElement) {
  const openButton = document.querySelector("[data-review-dialog-open]");
  const closeButton = reviewDialog.querySelector("[data-review-dialog-close]");

  openButton?.addEventListener("click", () => reviewDialog.showModal());
  closeButton?.addEventListener("click", () => reviewDialog.close());
  reviewDialog.addEventListener("click", (event) => {
    if (event.target === reviewDialog) reviewDialog.close();
  });

  if (reviewDialog.hasAttribute("data-open-on-load")) reviewDialog.showModal();
}
