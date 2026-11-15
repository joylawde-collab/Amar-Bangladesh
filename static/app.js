const search = document.getElementById("search");
if (search) {
  search.addEventListener("input", () => {
    const term = search.value.trim().toLocaleLowerCase();
    document.querySelectorAll(".service-card").forEach(card => {
      card.hidden = !card.dataset.search.toLocaleLowerCase().includes(term);
    });
  });
}
