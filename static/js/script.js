// Add and remove records without reloading the page.
// Add:    the buttons stay disabled until every field has a value; values are trimmed;
//         the server checks the rules and sends back the new row, which is added to the table.
// Remove: the row is deleted on the server and taken out of the table.

(function () {
  var form = document.getElementById("f");
  var message = document.getElementById("msg");
  var list = document.getElementById("record-list");

  function say(text, ok) {
    if (!message) return;
    message.textContent = text;
    message.className = ok ? "ok" : "";
  }

  function csrfToken() {
    var input = document.querySelector("input[name=csrfmiddlewaretoken]");
    return input ? input.value : "";
  }

  function post(url, body) {
    return fetch(url, {
      method: "POST", body: body || null,
      headers: { "X-Requested-With": "XMLHttpRequest", "X-CSRFToken": csrfToken() }
    }).then(function (res) {
      return res.json().then(function (data) { return data; }, function () {
        return { ok: false, errors: ["Something went wrong. Refresh the page and try again."] };
      });
    }, function () {
      return { ok: false, errors: ["Could not reach the server. Check your connection."] };
    });
  }

  // "No records yet." row
  function syncEmptyRow() {
    if (!list) return;
    var rows = list.querySelectorAll("tr:not(.empty-row)");
    var empty = list.querySelector(".empty-row");
    if (rows.length === 0 && !empty) {
      var columns = list.closest("table").querySelectorAll("thead th").length;
      var tr = document.createElement("tr");
      tr.className = "empty-row";
      tr.innerHTML = '<td colspan="' + columns + '">No records yet.</td>';
      list.append(tr);
    } else if (rows.length > 0 && empty) {
      empty.remove();
    }
  }

  // ---------- ADD ----------
  if (form && form.dataset.ajax) {
    var fields = Array.prototype.slice.call(form.querySelectorAll(
      "input:not([type=hidden]):not([disabled]), select:not([disabled]), textarea:not([disabled])"));
    var buttons = form.querySelectorAll("button[type=submit]");

    function checkInput() {
      var allFilled = fields.every(function (f) { return f.value.trim().length > 0; });
      buttons.forEach(function (b) { b.disabled = !allFilled; });
    }

    fields.forEach(function (f) {
      f.addEventListener("input", checkInput);
      f.addEventListener("change", checkInput);
    });

    form.addEventListener("submit", function (e) {
      e.preventDefault();
      var clicked = e.submitter;
      if (!clicked || clicked.disabled) return;

      var data = new FormData(form);
      fields.forEach(function (f) { if (f.tagName !== "SELECT") data.set(f.name, f.value.trim()); });
      data.set("action", clicked.value);

      buttons.forEach(function (b) { b.disabled = true; });   // stop double clicks
      post(window.location.pathname, data).then(function (result) {
        if (!result.ok) { say(result.errors.join(" ")); checkInput(); return; }

        if (result.row) {
          var holder = document.createElement("tbody");
          holder.innerHTML = result.row.trim();
          list.append(holder.firstElementChild);
          syncEmptyRow();
          fields.forEach(function (f) { f.value = ""; });      // clear the form
          fields[0].focus();
        }
        say(result.message, true);
        checkInput();
      });
    });

    checkInput();   // start with the buttons disabled (or enabled when the form is pre-filled)
  }

  // ---------- REMOVE ----------
  document.addEventListener("click", function (e) {
    var link = e.target.closest("a.js-remove");
    if (!link) return;
    e.preventDefault();
    if (!confirm("Remove this record? Records linked to it will be removed too.")) return;

    post(link.href).then(function (result) {
      if (!result.ok) { say(result.errors.join(" ")); return; }
      link.closest("tr").remove();
      syncEmptyRow();
      say(result.message, true);
    });
  });

  // ---------- pages without the AJAX form (edit page, login ...) ----------
  if (form && !form.dataset.ajax) {
    form.addEventListener("submit", function (e) {
      var fields = form.querySelectorAll("input:not([type=hidden]):not([disabled]), select:not([disabled]), textarea:not([disabled])");
      for (var i = 0; i < fields.length; i++) {
        if (fields[i].value.trim() === "") {
          e.preventDefault();
          var label = fields[i].closest("label");
          say("Fill in: " + (label ? label.childNodes[0].textContent.trim() : fields[i].name));
          fields[i].focus();
          return;
        }
      }
    });
  }

  // Alert after a successful action that reloaded the page (saved, updated, logged in ...)
  if (window.okMessages && okMessages.length > 0) { alert(okMessages.join("\n")); }
})();
