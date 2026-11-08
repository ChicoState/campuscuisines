const loginDialog = document.getElementById("account-login-dialog");

if (loginDialog && typeof loginDialog.showModal === "function") {
  const loginForm = loginDialog.querySelector("[data-login-url]");
  if (loginForm instanceof HTMLFormElement) {
    loginForm.action = loginForm.dataset.loginUrl;
  }

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

  document.addEventListener("click", (event) => {
    if (!loginDialog.open) return;
    if (
      event.target instanceof Element &&
      event.target.closest("[data-account-login-trigger]")
    ) {
      return;
    }

    const bounds = loginDialog.getBoundingClientRect();
    const clickedOutside =
      event.clientX < bounds.left ||
      event.clientX > bounds.right ||
      event.clientY < bounds.top ||
      event.clientY > bounds.bottom;

    if (clickedOutside) loginDialog.close();
  });
}
