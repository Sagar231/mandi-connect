/* MandiConnect API helper — JWT-aware AJAX over jQuery. */
(function (window) {
  const API = "/api";
  const store = {
    get access() { return localStorage.getItem("mc_access"); },
    set access(v) { v ? localStorage.setItem("mc_access", v) : localStorage.removeItem("mc_access"); },
    get refresh() { return localStorage.getItem("mc_refresh"); },
    set refresh(v) { v ? localStorage.setItem("mc_refresh", v) : localStorage.removeItem("mc_refresh"); },
    get user() { try { return JSON.parse(localStorage.getItem("mc_user")); } catch (e) { return null; } },
    set user(v) { v ? localStorage.setItem("mc_user", JSON.stringify(v)) : localStorage.removeItem("mc_user"); },
  };

  function authHeader() {
    return store.access ? { Authorization: "Bearer " + store.access } : {};
  }

  function request(method, path, data, opts) {
    opts = opts || {};
    return $.ajax({
      url: API + path,
      method: method,
      contentType: "application/json",
      data: data ? JSON.stringify(data) : undefined,
      headers: authHeader(),
    }).catch(function (xhr) {
      if (xhr.status === 401 && store.refresh && !opts._retried) {
        return refreshToken().then(function () {
          return request(method, path, data, Object.assign({}, opts, { _retried: true }));
        });
      }
      return Promise.reject(xhr);
    });
  }

  function refreshToken() {
    return $.ajax({
      url: API + "/auth/token/refresh/",
      method: "POST",
      contentType: "application/json",
      data: JSON.stringify({ refresh: store.refresh }),
    }).then(function (res) {
      store.access = res.access;
      if (res.refresh) store.refresh = res.refresh;
    }).catch(function () { logout(); });
  }

  function login(email, password) {
    return $.ajax({
      url: API + "/auth/login/",
      method: "POST",
      contentType: "application/json",
      data: JSON.stringify({ email: email, password: password }),
    }).then(function (res) {
      store.access = res.access;
      store.refresh = res.refresh;
      store.user = res.user;
      return res;
    });
  }

  function logout() {
    if (store.refresh) {
      request("POST", "/auth/logout/", { refresh: store.refresh }).always(clear);
    } else { clear(); }
  }
  function clear() { store.access = null; store.refresh = null; store.user = null; }

  function isAuthed() { return !!store.access; }

  function errText(xhr) {
    try {
      const j = xhr.responseJSON;
      if (!j) return "Request failed (" + xhr.status + ")";
      if (typeof j === "string") return j;
      if (j.detail) return j.detail;
      return Object.entries(j).map(function (kv) { return kv[0] + ": " + kv[1]; }).join("\n");
    } catch (e) { return "Request failed"; }
  }

  window.MC = {
    request, get: (p) => request("GET", p), post: (p, d) => request("POST", p, d),
    put: (p, d) => request("PUT", p, d), patch: (p, d) => request("PATCH", p, d),
    del: (p) => request("DELETE", p),
    login, logout, isAuthed, store, errText, API,
  };
})(window);
