document.getElementById("fill").addEventListener("click", () => {
  const status = document.getElementById("status");
  status.textContent = "Filling...";

  chrome.tabs.query({ active: true, currentWindow: true }, (tabs) => {
    chrome.tabs.sendMessage(tabs[0].id, { action: "autofill" }, (response) => {
      if (chrome.runtime.lastError) {
        status.textContent = "Error — try refreshing the page.";
        return;
      }
      const n = response?.filled ?? 0;
      status.textContent = n > 0 ? `Filled ${n} field${n !== 1 ? "s" : ""}. Solve CAPTCHA & submit!` : "No fields found.";
    });
  });
});
