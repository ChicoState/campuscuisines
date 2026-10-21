(() => {
  const dropdowns = document.querySelectorAll(".tag-dropdown");

  dropdowns.forEach((dropdown) => {
    const summary = dropdown.querySelector("[data-tags-summary]");
    const checkboxes = dropdown.querySelectorAll('input[name="tags"]');

    if (!summary) return;

    const updateSummary = () => {
      const selectedCount = [...checkboxes].filter(
        (checkbox) => checkbox.checked,
      ).length;
      const label = `${selectedCount} tag${selectedCount === 1 ? "" : "s"} selected`;
      summary.textContent = label;
      summary.dataset.tagsSummary = label;
    };

    checkboxes.forEach((checkbox) => {
      checkbox.addEventListener("change", updateSummary);
    });
    updateSummary();
  });
})();
