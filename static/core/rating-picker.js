document.querySelectorAll("[data-rating-picker]").forEach((picker) => {
  const value = picker.parentElement?.querySelector("[data-rating-picker-value]");
  const inputs = picker.querySelectorAll("input[type='radio']");
  const stars = picker.querySelectorAll("[data-rating-star]");

  function updateRating() {
    const selected = picker.querySelector("input[type='radio']:checked");
    const rating = Number(selected?.value ?? 0);

    stars.forEach((star, index) => {
      star.classList.toggle("rating-picker__star--filled", index < rating);
    });

    if (selected && value) {
      value.textContent = selected.closest("label")?.textContent?.trim() ?? "";
    }
  }

  inputs.forEach((input) => input.addEventListener("change", updateRating));
  updateRating();
});
