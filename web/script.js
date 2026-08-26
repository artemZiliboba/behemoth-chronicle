const activePost = document.querySelector("#active-post");
const historyItems = document.querySelectorAll(".history-item[data-post-id]");

for (const item of historyItems) {
  item.addEventListener("click", () => {
    const template = document.getElementById(item.dataset.postId);

    if (!activePost || !(template instanceof HTMLTemplateElement)) return;

    const footer = activePost.querySelector(".article-footer");
    activePost.replaceChildren(template.content.cloneNode(true));
    if (footer) activePost.append(footer);

    for (const historyItem of historyItems) {
      const isActive = historyItem === item;
      historyItem.classList.toggle("is-active", isActive);
      historyItem.setAttribute("aria-pressed", String(isActive));
    }

    if (window.matchMedia("(max-width: 850px)").matches) {
      activePost.scrollIntoView({ behavior: "smooth", block: "start" });
    }
  });
}
