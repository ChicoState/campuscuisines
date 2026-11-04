const loginDialog = document.getElementById("account-login-dialog");

if (loginDialog && typeof loginDialog.showModal === "function") {
  for (const trigger of document.querySelectorAll("[data-account-login-trigger]")) {
    trigger.addEventListener("click", (event) => {
      if (
        event.defaultPrevented ||
        event.button !== 0 ||
        event.metaKey ||
        event.ctrlKey ||
        event.shiftKey ||
        event.altKey
      ) {
        return;
      }

      event.preventDefault();
      loginDialog.showModal();
    });
  }
}
