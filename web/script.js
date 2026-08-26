const historyItems = [...document.querySelectorAll("[data-post-date]")];
const articles = [...document.querySelectorAll("[data-article-date]")];
const articlePanel = document.querySelector(".latest-section");

function selectPost(date, updateUrl = true) {
  const selectedItem = historyItems.find((item) => item.dataset.postDate === date);
  const selectedArticle = articles.find((article) => article.dataset.articleDate === date);

  if (!selectedItem || !selectedArticle) return;

  historyItems.forEach((item) => {
    const selected = item === selectedItem;
    item.classList.toggle("is-selected", selected);
    item.setAttribute("aria-pressed", String(selected));
  });

  articles.forEach((article) => {
    const selected = article === selectedArticle;
    article.hidden = !selected;
    article.classList.toggle("is-active", selected);
  });

  articlePanel.setAttribute("aria-label", `Запись за ${selectedItem.textContent.trim()}`);
  if (updateUrl) history.replaceState(null, "", `#post-${date}`);

  if (window.matchMedia("(max-width: 850px)").matches) {
    articlePanel.scrollIntoView({ behavior: "smooth", block: "start" });
  }
}

historyItems.forEach((item) => {
  item.addEventListener("click", () => selectPost(item.dataset.postDate));
});

const dateFromHash = window.location.hash.match(/^#post-(\d{4}-\d{2}-\d{2})$/)?.[1];
if (dateFromHash) selectPost(dateFromHash, false);
