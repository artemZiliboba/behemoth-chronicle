const activePost = document.querySelector("#active-post");
const editionDate = document.querySelector("#edition-date");
const historyItems = document.querySelectorAll(".history-item[data-post-id]");

for (const item of historyItems) {
  item.addEventListener("click", () => {
    const template = document.getElementById(item.dataset.postId);

    if (!activePost || !(template instanceof HTMLTemplateElement)) return;

    activePost.replaceChildren(template.content.cloneNode(true));
    if (editionDate) {
      const label = item.dataset.latest === "true" ? "<b>Сегодня.</b> " : "";
      editionDate.innerHTML = `${label}${item.dataset.date}`;
    }

    for (const historyItem of historyItems) {
      const isActive = historyItem === item;
      historyItem.classList.toggle("is-active", isActive);
      historyItem.setAttribute("aria-pressed", String(isActive));
    }

    if (window.matchMedia("(max-width: 860px)").matches) {
      activePost.scrollIntoView({ behavior: "smooth", block: "start" });
    }
  });
}
