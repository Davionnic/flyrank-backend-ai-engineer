(function () {
  var form = document.getElementById("contact-form");
  var success = document.getElementById("form-success");
  var errorEl = document.getElementById("form-error");
  var copyBtn = document.getElementById("copy-body");
  if (!form) return;

  var TO = "gallodave.cs@gmail.com";
  var SUBJECT = "Junior backend / AI-adjacent role";

  function val(id) {
    var el = document.getElementById(id);
    return el ? String(el.value || "").trim() : "";
  }

  function buildBody() {
    return [
      "Name: " + val("name"),
      "Email: " + val("email"),
      "Company / context: " + (val("company") || "(none)"),
      "",
      "Message:",
      val("message"),
      "",
      "---",
      "Sent from personal site contact form (mailto)."
    ].join("\n");
  }

  function validate() {
    var name = val("name");
    var email = val("email");
    var message = val("message");
    if (!name) return "Name is required.";
    if (!email || !/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email)) return "A valid email is required.";
    if (!message || message.length < 10) return "Message must be at least 10 characters.";
    return "";
  }

  form.addEventListener("submit", function (e) {
    e.preventDefault();
    if (errorEl) errorEl.textContent = "";
    var err = validate();
    if (err) {
      if (errorEl) errorEl.textContent = err;
      return;
    }
    var body = buildBody();
    var href =
      "mailto:" +
      encodeURIComponent(TO).replace(/%40/g, "@") +
      "?subject=" +
      encodeURIComponent(SUBJECT) +
      "&body=" +
      encodeURIComponent(body);
    // encodeURIComponent on full address encodes @; keep mailto address readable
    href = "mailto:" + TO + "?subject=" + encodeURIComponent(SUBJECT) + "&body=" + encodeURIComponent(body);

    window.location.href = href;
    form.classList.add("hidden");
    if (success) {
      success.classList.add("show");
      success.dataset.body = body;
    }
  });

  if (copyBtn) {
    copyBtn.addEventListener("click", function () {
      var body = (success && success.dataset.body) || buildBody();
      if (navigator.clipboard && navigator.clipboard.writeText) {
        navigator.clipboard.writeText(body).then(function () {
          copyBtn.textContent = "Copied";
          setTimeout(function () { copyBtn.textContent = "Copy message body"; }, 1500);
        }).catch(function () {
          fallbackCopy(body);
        });
      } else {
        fallbackCopy(body);
      }
    });
  }

  function fallbackCopy(text) {
    var ta = document.createElement("textarea");
    ta.value = text;
    document.body.appendChild(ta);
    ta.select();
    try { document.execCommand("copy"); copyBtn.textContent = "Copied"; }
    catch (e) { copyBtn.textContent = "Select & copy manually below"; }
    document.body.removeChild(ta);
    setTimeout(function () { copyBtn.textContent = "Copy message body"; }, 1500);
  }
})();
