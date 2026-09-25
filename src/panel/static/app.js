async function getJson(url, options) {
  const res = await fetch(url, options);
  if (!res.ok) throw new Error(url + " " + res.status);
  return res.json();
}

async function loadExclude() {
  const data = await getJson("/api/exclude");
  document.getElementById("words").value = data.words.join("\n");
}

async function saveExclude() {
  const words = document.getElementById("words").value.split("\n");
  const data = await getJson("/api/exclude", {
    method: "PUT",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ words }),
  });
  document.getElementById("status").textContent =
    "сохранено: " + data.words.length;
}

async function loadLog(name) {
  const data = await getJson("/api/logs/" + name);
  document.getElementById(name).textContent = data.text || "(пусто)";
}

function refreshLogs() {
  loadLog("parse").catch(console.error);
  loadLog("notify").catch(console.error);
}

document.getElementById("save").onclick = () =>
  saveExclude().catch((e) => (document.getElementById("status").textContent = e));
document.getElementById("parse-log").onclick = refreshLogs;
document.getElementById("notify-log").onclick = refreshLogs;

document.getElementById("reload").onclick = () =>
  loadExclude()
    .then(() => {
      document.getElementById("status").textContent = "загружено";
    })
    .catch((e) => {
      document.getElementById("status").textContent = e;
    });

document.getElementById("reset-ignored").onclick = async () => {
  try {
    await getJson("/api/reset-ignored", { method: "POST" });
    document.getElementById("status").textContent =
      "игнор сброшен, уйдут на ближайшей рассылке";
  } catch (e) {
    document.getElementById("status").textContent = e;
  }
};

loadExclude().catch(console.error);
refreshLogs();
setInterval(refreshLogs, 5000);