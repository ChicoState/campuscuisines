const announcementDialog = document.querySelector("[data-announcement-dialog]");
const announcementOpenButton = document.querySelector("[data-announcement-open]");
const announcementCloseButton = document.querySelector("[data-announcement-close]");

if (announcementDialog && announcementOpenButton && announcementCloseButton) {
  announcementOpenButton.addEventListener("click", () => {
    if (!announcementDialog.open) {
      announcementDialog.showModal();
    }
  });

  announcementCloseButton.addEventListener("click", () => {
    announcementDialog.close();
  });

  announcementDialog.addEventListener("click", (event) => {
    if (event.target === announcementDialog) {
      announcementDialog.close();
    }
  });

  announcementDialog.addEventListener("close", () => {
    announcementOpenButton.focus();
  });
}
