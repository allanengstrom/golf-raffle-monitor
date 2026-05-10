const INFO = {
  firstName: "Allan",
  lastName: "Engstrom",
  fullName: "Allan Engstrom",
  email: "makoallan@icloud.com",
  phone: "5713732274",
  phoneFormatted: "(571) 373-2274",
  address: "207 Armour Street",
  city: "Davidson",
  state: "NC",
  zip: "28036",
  dobMonth: "04",
  dobDay: "07",
  dobYear: "2005",
  dobFull: "04/07/2005",
};

function setNativeValue(el, value) {
  const nativeSetter = Object.getOwnPropertyDescriptor(
    el.tagName === "SELECT" ? window.HTMLSelectElement.prototype : window.HTMLInputElement.prototype,
    "value"
  )?.set;
  if (nativeSetter) {
    nativeSetter.call(el, value);
    el.dispatchEvent(new Event("input", { bubbles: true }));
    el.dispatchEvent(new Event("change", { bubbles: true }));
  } else {
    el.value = value;
    el.dispatchEvent(new Event("input", { bubbles: true }));
    el.dispatchEvent(new Event("change", { bubbles: true }));
  }
}

function matchesAny(str, terms) {
  const s = str.toLowerCase();
  return terms.some((t) => s.includes(t));
}

function fillField(el) {
  const hint = [
    el.name || "",
    el.id || "",
    el.placeholder || "",
    el.getAttribute("aria-label") || "",
    el.className || "",
  ]
    .join(" ")
    .toLowerCase();

  if (el.tagName === "SELECT") {
    if (matchesAny(hint, ["state", "province"])) {
      const opt = [...el.options].find((o) =>
        o.value.toUpperCase() === "NC" || o.text.toLowerCase().includes("north carolina")
      );
      if (opt) setNativeValue(el, opt.value);
    }
    return;
  }

  if (el.type === "hidden" || el.type === "submit" || el.type === "button") return;

  if (el.type === "email" || matchesAny(hint, ["email", "e-mail"])) {
    setNativeValue(el, INFO.email);
  } else if (matchesAny(hint, ["firstname", "first_name", "first name", "fname", "given"])) {
    setNativeValue(el, INFO.firstName);
  } else if (matchesAny(hint, ["lastname", "last_name", "last name", "lname", "family", "surname"])) {
    setNativeValue(el, INFO.lastName);
  } else if (matchesAny(hint, ["fullname", "full_name", "full name", "yourname", "your name"]) ||
             (matchesAny(hint, ["name"]) && !matchesAny(hint, ["user", "display", "nick", "brand", "product", "company"]))) {
    setNativeValue(el, INFO.fullName);
  } else if (el.type === "tel" || matchesAny(hint, ["phone", "mobile", "cell", "telephone"])) {
    setNativeValue(el, INFO.phoneFormatted);
  } else if (matchesAny(hint, ["address", "street", "addr"])) {
    setNativeValue(el, INFO.address);
  } else if (matchesAny(hint, ["city", "town"])) {
    setNativeValue(el, INFO.city);
  } else if (matchesAny(hint, ["state", "province", "region"])) {
    setNativeValue(el, INFO.state);
  } else if (matchesAny(hint, ["zip", "postal", "postcode"])) {
    setNativeValue(el, INFO.zip);
  } else if (matchesAny(hint, ["dob", "birthdate", "birthday", "birth_date", "date_of_birth", "dateofbirth"])) {
    setNativeValue(el, INFO.dobFull);
  } else if (matchesAny(hint, ["birth_month", "birthmonth", "dobmonth", "dob_month"])) {
    setNativeValue(el, INFO.dobMonth);
  } else if (matchesAny(hint, ["birth_day", "birthday", "dobday", "dob_day"]) && el.maxLength <= 2) {
    setNativeValue(el, INFO.dobDay);
  } else if (matchesAny(hint, ["birth_year", "birthyear", "dobyear", "dob_year"])) {
    setNativeValue(el, INFO.dobYear);
  }
}

function autofill() {
  const fields = document.querySelectorAll("input, select, textarea");
  let filled = 0;
  fields.forEach((el) => {
    const before = el.value;
    fillField(el);
    if (el.value !== before) filled++;
  });
  return filled;
}

chrome.runtime.onMessage.addListener((msg, _sender, sendResponse) => {
  if (msg.action === "autofill") {
    const count = autofill();
    sendResponse({ filled: count });
  }
});
