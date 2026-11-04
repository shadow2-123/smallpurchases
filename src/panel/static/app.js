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

loadExclude().catch(console.error);
refreshLogs();
setInterval(refreshLogs, 5000);

// Календарь: отображаем только подтверждённый ответ сервера.
(() => {
  const el = (id) => document.getElementById('calendar-' + id);
  const now = new Date();
  const today = `${now.getFullYear()}-${String(now.getMonth() + 1).padStart(2, '0')}-${String(now.getDate()).padStart(2, '0')}`;
  let year = now.getFullYear(), month = now.getMonth() + 1;
  let data = null, selected = null, busy = false;
  const names = ['Январь','Февраль','Март','Апрель','Май','Июнь','Июль','Август','Сентябрь','Октябрь','Ноябрь','Декабрь'];
  const key = (day) => `${String(year).padStart(4,'0')}-${String(month).padStart(2,'0')}-${String(day).padStart(2,'0')}`;
  function message(text, error = false) {
    el('status').textContent = text;
    el('status').classList.toggle('error', error);
  }
  function controls() {
    el('prev').disabled = busy || (year === 1 && month === 1);
    el('next').disabled = busy || (year === 9999 && month === 12);
    el('today').disabled = el('refresh').disabled = busy;
    el('confirm').disabled = el('weekends').disabled = busy || !data;
    el('off').disabled = el('save-day').disabled = busy || !data || !selected;
    el('description').disabled = busy || !data || !selected || !el('off').checked;
    el('days').querySelectorAll('button').forEach(b => { b.disabled = busy; });
    document.getElementById('calendar').setAttribute('aria-busy', String(busy));
  }
  function editor() {
    const record = data?.non_working_days.find(d => d.date === selected);
    el('selected').textContent = selected ? selected.split('-').reverse().join('.') : 'Выберите день';
    el('off').checked = Boolean(record);
    el('description').value = record?.description || '';
    controls();
  }
  function render() {
    el('month').textContent = `${names[month - 1]} ${year}`;
    el('ready').textContent = data ? (data.is_ready ? 'Месяц готов' : 'Не готов') : 'Нет данных';
    el('ready').classList.toggle('ready', Boolean(data?.is_ready));
    el('confirm').textContent = data?.is_ready ? 'Снять готовность' : 'Подтвердить месяц';
    el('days').replaceChildren();
    el('summary').textContent = '';
    if (data) {
      // setFullYear корректно обрабатывает в том числе годы 1–99.
      const first = new Date(0); first.setFullYear(year, month - 1, 1); first.setHours(12,0,0,0);
      const last = new Date(first); last.setMonth(month, 0);
      const offset = (first.getDay() + 6) % 7;
      for (let i = 0; i < offset; i++) el('days').append(document.createElement('span'));
      const off = new Map(data.non_working_days.map(d => [d.date, d]));
      for (let day = 1; day <= last.getDate(); day++) {
        const iso = key(day), record = off.get(iso), button = document.createElement('button');
        button.type = 'button'; button.className = 'calendar-day';
        button.classList.toggle('off', Boolean(record));
        button.classList.toggle('today', iso === today);
        button.classList.toggle('selected', iso === selected);
        button.setAttribute('aria-pressed', String(iso === selected));
        button.setAttribute('aria-label', `${iso}: ${record ? 'нерабочий' : 'рабочий'}${record?.description ? ', ' + record.description : ''}`);
        if (iso === today) button.setAttribute('aria-current', 'date');
        button.title = record?.description || (record ? 'Нерабочий день' : 'Рабочий день');
        const number = document.createElement('span'); number.textContent = day; button.append(number);
        if (record) { const label = document.createElement('small'); label.textContent = 'Выходной'; button.append(label); }
        button.onclick = () => { if (!busy) { selected = iso; render(); } };
        el('days').append(button);
      }
      el('summary').textContent = `Нерабочих дней: ${off.size}. ${data.is_ready ? 'Календарь подтверждён.' : 'Проверьте даты и подтвердите месяц.'}`;
    }
    editor();
  }
  async function request(url, options) {
    const response = await fetch(url, options);
    if (!response.ok) throw new Error(`Ошибка ${response.status}. Проверьте API и повторите запрос.`);
    return response.json();
  }
  async function run(action, success) {
    if (busy) return;
    busy = true; controls(); message('Загрузка…');
    try { data = await action(); render(); message(success); }
    catch (error) {
      // После ошибки записи результат неизвестен: перечитываем перед следующей правкой.
      data = null; render(); message(error.message + ' Нажмите «Обновить».', true);
    } finally { busy = false; controls(); }
  }
  function load() {
    data = null; render();
    return run(() => request(`/api/calendar?year=${year}&month=${month}`), 'Календарь загружен.');
  }
  function shift(delta) {
    if (busy) return;
    month += delta;
    if (month === 0) { month = 12; year--; }
    if (month === 13) { month = 1; year++; }
    selected = null; load();
  }
  function put(url, body) {
    return request(url, {method:'PUT', headers:{'Content-Type':'application/json'}, body:JSON.stringify(body)});
  }
  el('prev').onclick = () => shift(-1);
  el('next').onclick = () => shift(1);
  el('refresh').onclick = () => { if (!busy) load(); };
  el('today').onclick = () => {
    if (busy) return;
    year = now.getFullYear(); month = now.getMonth() + 1; selected = today; load();
  };
  el('off').onchange = controls;
  el('day-form').onsubmit = (event) => {
    event.preventDefault();
    if (busy || !data || !selected) return;
    const payload = {is_non_working:el('off').checked, description:el('off').checked ? el('description').value.trim() || null : null};
    run(() => put(`/api/calendar/days/${selected}`, payload), 'День сохранён. Проверьте готовность месяца.');
  };
  el('weekends').onclick = () => {
    if (busy || !data) return;
    run(async () => {
      // Перечитываем месяц, чтобы сохранить актуальные отметки и описания.
      let result = await request(`/api/calendar?year=${year}&month=${month}`);
      const existing = new Set(result.non_working_days.map(day => day.date));
      const current = new Date(0);
      current.setFullYear(year, month - 1, 1);
      current.setHours(12, 0, 0, 0);
      const dates = [];
      while (current.getFullYear() === year && current.getMonth() === month - 1) {
        if (current.getDay() === 0 || current.getDay() === 6) {
          const iso = key(current.getDate());
          if (!existing.has(iso)) dates.push(iso);
        }
        current.setDate(current.getDate() + 1);
      }
      let saved = 0;
      try {
        for (const iso of dates) {
          message(`Отмечаем выходные: ${saved + 1} из ${dates.length}…`);
          result = await put(`/api/calendar/days/${iso}`, {
            is_non_working: true,
            description: 'Выходной',
          });
          saved++;
        }
      } catch (error) {
        throw new Error(`Подтверждено сохранение ${saved} из ${dates.length} дней. ${error.message}`);
      }
      return result;
    }, 'Субботы и воскресенья отмечены. Проверьте рабочие субботы и подтвердите месяц.');
  };
  el('confirm').onclick = () => {
    if (busy || !data) return;
    const ready = !data.is_ready;
    run(() => put(`/api/calendar/months/${year}/${month}`, {is_ready:ready}), ready ? 'Месяц подтверждён.' : 'Готовность снята.');
  };
  selected = today; load();
})();
