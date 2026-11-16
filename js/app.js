(() => {
  "use strict";
  const CFG = window.SSS_CONFIG || {};
  const HEROES = window.HEROES || [];
  const byId = Object.fromEntries(HEROES.map((h) => [h.id, h]));
  const DEMO = !(CFG.supabaseUrl && CFG.supabaseAnonKey && window.supabase);
  const $ = (id) => document.getElementById(id);

  const state = { user: null, isAdmin: false, locksOpen: true, picks: new Map(), filter: "", freshId: null };
  const REDUCED = window.matchMedia && matchMedia("(prefers-reduced-motion: reduce)").matches;

  // ---------- tiny DOM helper (always textContent, never innerHTML, for user input) ----------
  function el(tag, props = {}, ...children) {
    const node = document.createElement(tag);
    for (const [k, v] of Object.entries(props)) {
      if (k === "class") node.className = v;
      else if (k.startsWith("on")) node.addEventListener(k.slice(2), v);
      else if (v !== null && v !== undefined && v !== false) node.setAttribute(k, v === true ? "" : v);
    }
    for (const c of children) if (c !== null && c !== undefined) node.append(c);
    return node;
  }
  const DISCORD_ICON = () => {
    const s = document.createElementNS("http://www.w3.org/2000/svg", "svg");
    s.setAttribute("viewBox", "0 0 24 24"); s.setAttribute("aria-hidden", "true");
    const p = document.createElementNS("http://www.w3.org/2000/svg", "path");
    p.setAttribute("fill", "currentColor");
    p.setAttribute("d", "M19.6 5.3A17.4 17.4 0 0 0 15.3 4l-.5 1a16 16 0 0 0-5.600 0l-.5-1a17.400 17.400 0 0 0-4.300 1.300C1.700 9.400.900 13.400 1.300 17.300a17.500 17.500 0 0 0 5.300 2.700l1.100-1.800c-.6-.2-1.200-.5-1.700-.8l.4-.3a12.500 12.500 0 0 0 11.200 0l.4.3c-.5.3-1.100.6-1.700.8l1.100 1.800a17.400 17.400 0 0 0 5.300-2.700c.5-4.500-.8-8.500-3.100-12ZM8.700 14.800c-1 0-1.900-1-1.900-2.100s.8-2.100 1.900-2.100 1.900 1 1.900 2.100-.8 2.100-1.900 2.100Zm6.600 0c-1 0-1.900-1-1.900-2.100s.8-2.100 1.900-2.100 1.900 1 1.900 2.100-.8 2.100-1.900 2.100Z");
    s.append(p); return s;
  };

  let toastTimer;
  function toast(msg, isError) {
    const t = $("toast");
    t.textContent = msg; t.className = "toast" + (isError ? " error" : ""); t.hidden = false;
    clearTimeout(toastTimer); toastTimer = setTimeout(() => (t.hidden = true), 5000);
  }

  // ---------- backends ----------
  // Both expose: init(onChange), signIn(), signOut(), loadPicks(), lock(heroId, name), remove(heroId)
  function demoBackend() {
    const KEY = "sss-demo";
    const read = () => { try { return JSON.parse(localStorage.getItem(KEY)) || {}; } catch { return {}; } };
    const write = (d) => { try { localStorage.setItem(KEY, JSON.stringify(d)); } catch { /* ignore */ } };
    let mem = Object.assign({ user: null, picks: [
      { hero_id: "kano", user_id: "demo-1", player_name: "Sample Player", discord_name: "sample.player" },
      { hero_id: "ira-crimson-haze", user_id: "demo-2", player_name: "Another Player", discord_name: "another_player" },
    ] }, read());
    let onChange = () => {};
    const save = () => { write(mem); onChange(); };
    return {
      async init(cb) { onChange = cb; state.user = mem.user; state.isAdmin = !!mem.user; },
      async signIn() { mem.user = { id: "demo-me", name: "Demo Player", handle: "demo.player", avatar: null }; state.user = mem.user; state.isAdmin = true; save(); },
      async signOut() { mem.user = null; state.user = null; state.isAdmin = false; save(); },
      async loadPicks() { return mem.picks; },
      async lock(heroId, name) {
        if (mem.picks.some((p) => p.hero_id === heroId)) throw { code: "23505", message: "picks_pkey" };
        if (mem.picks.some((p) => p.user_id === "demo-me")) throw { code: "23505", message: "picks_user_id_key" };
        await new Promise((r) => setTimeout(r, 350));
        mem.picks.push({ hero_id: heroId, user_id: "demo-me", player_name: name, discord_name: "demo.player" }); save();
      },
      async remove(heroId) { mem.picks = mem.picks.filter((p) => p.hero_id !== heroId); save(); },
    };
  }

  function supabaseBackend() {
    const sb = window.supabase.createClient(CFG.supabaseUrl, CFG.supabaseAnonKey);
    let onChange = () => {};
    async function applySession(session) {
      const u = session && session.user;
      if (!u) { state.user = null; state.isAdmin = false; return; }
      const m = u.user_metadata || {};
      state.user = {
        id: u.id,
        name: (m.custom_claims && m.custom_claims.global_name) || m.full_name || m.name || "Discord user",
        handle: m.full_name || m.name || "",
        avatar: m.avatar_url || null,
      };
      const { data } = await sb.rpc("is_admin");
      state.isAdmin = data === true;
    }
    return {
      async init(cb) {
        onChange = cb;
        const { data } = await sb.auth.getSession();
        await applySession(data.session);
        sb.auth.onAuthStateChange((_evt, session) => {
          // Defer: Supabase calls must not run inside this callback.
          setTimeout(async () => { await applySession(session); onChange(); }, 0);
        });
        sb.channel("picks").on("postgres_changes", { event: "*", schema: "public", table: "picks" }, () => onChange()).subscribe();
        setInterval(() => { if (!document.hidden) onChange(); }, 30000);
        document.addEventListener("visibilitychange", () => { if (!document.hidden) onChange(); });
        const s = await sb.from("settings").select("locks_open").maybeSingle();
        if (s.data) state.locksOpen = s.data.locks_open;
      },
      async signIn() {
        const { error } = await sb.auth.signInWithOAuth({
          provider: "discord",
          options: { scopes: "identify", redirectTo: location.origin + location.pathname },
        });
        if (error) throw error;
      },
      async signOut() { await sb.auth.signOut(); },
      async loadPicks() {
        const { data, error } = await sb.from("picks").select("hero_id,user_id,player_name,discord_name,created_at").order("created_at");
        if (error) throw error;
        return data;
      },
      async lock(heroId, name) {
        const { error } = await sb.from("picks").insert({ hero_id: heroId, player_name: name });
        if (error) throw error;
      },
      async remove(heroId) {
        const { error } = await sb.from("picks").delete().eq("hero_id", heroId);
        if (error) throw error;
      },
    };
  }

  const api = DEMO ? demoBackend() : supabaseBackend();

  // ---------- rendering ----------
  function myPick() {
    if (!state.user) return null;
    for (const p of state.picks.values()) if (p.user_id === state.user.id) return p;
    return null;
  }

  function avatar(h) {
    const wrap = el("span", { class: "avatar" });
    const initials = el("span", { class: "initials" }, h.name.replace(/[^A-Za-z ]/g, "").split(" ").map((w) => w[0]).slice(0, 2).join(""));
    // 1st choice: the young hero's own card art; 2nd: the fabtcg.com hero icon; 3rd: initials.
    const sources = [[h.art, "card-art"], [h.icon, ""]].filter((x) => x[0]);
    const img = el("img", { alt: "", loading: "lazy", referrerpolicy: "no-referrer" });
    let i = 0;
    const next = () => {
      if (i >= sources.length) { img.replaceWith(initials); return; }
      img.className = sources[i][1]; img.src = sources[i][0]; i++;
    };
    img.addEventListener("error", next);
    next();
    wrap.append(img);
    return wrap;
  }

  function heroTile(h, pick) {
    const [first, ...rest] = h.name.split(", ");
    const kids = [avatar(h), el("span", { class: "hero-name" }, first), el("span", { class: "hero-class" }, rest.length ? rest.join(", ") : h.cls)];
    let node;
    if (h.benched) {
      node = el("div", { class: "hero benched", title: `Benched until ${h.benched}` }, ...kids, el("span", { class: "player" }, "Benched"));
    } else if (pick) {
      const mine = state.user && pick.user_id === state.user.id;
      node = el("div", { class: "hero locked" + (mine ? " mine" : "") + (state.freshId === h.id ? " fresh" : ""), id: "pick-" + h.id }, ...kids, el("span", { class: "player" }, pick.player_name));
      if (pick.discord_name) node.append(el("span", { class: "tag" }, "@" + pick.discord_name));
      if (state.isAdmin) node.append(el("button", { class: "remove", type: "button", onclick: () => removePick(h, pick) }, "Remove"));
    } else {
      node = el("button", { class: "hero", type: "button", "aria-label": `${h.name}, ${h.cls}. Available.`, onclick: () => openDialog(h) }, ...kids);
    }
    node.style.setProperty("--c", h.colour);
    return node;
  }

  function render() {
    const q = state.filter.trim().toLowerCase();
    const match = (h) => !q || (h.name + " " + h.cls).toLowerCase().includes(q);
    const avail = [], locked = [], benched = [];
    for (const h of HEROES) {
      const pick = state.picks.get(h.id);
      if (h.benched) benched.push(heroTile(h));
      else if (pick) locked.push([pick.created_at || "", heroTile(h, pick)]);
      else if (match(h)) avail.push(heroTile(h));
    }
    $("grid-available").replaceChildren(...avail);
    locked.sort((a, b) => (a[0] < b[0] ? -1 : a[0] > b[0] ? 1 : 0));
    $("grid-locked").replaceChildren(...locked.map((x) => x[1]));
    $("grid-benched").replaceChildren(...benched);
    const total = HEROES.filter((h) => !h.benched).length;
    $("empty-available").hidden = avail.length > 0;
    $("empty-locked").hidden = locked.length > 0;
    $("counts").replaceChildren(el("b", {}, String(total - state.picks.size)), " available · ", el("b", {}, String(state.picks.size)), " locked in");
    const mine = myPick();
    $("thanks").hidden = !mine;
    $("choose-btn").hidden = !!mine;
    renderAccount();
  }

  function renderAccount() {
    const box = $("account");
    const kids = [];
    const mine = myPick();
    if (!state.user) {
      kids.push(el("p", {}, DEMO ? el("span", { class: "demo-flag" }, "Demo mode") : null,
        "Log in with Discord to lock in your hero. We only read your Discord name and avatar."));
      kids.push(el("button", { class: "btn discord", type: "button", onclick: signIn }, DISCORD_ICON(), "Log in with Discord"));
    } else {
      const who = el("div", { class: "who" });
      if (state.user.avatar) who.append(el("img", { src: state.user.avatar, alt: "" }));
      const text = el("div");
      if (mine) {
        const h = byId[mine.hero_id];
        text.append(el("p", {}, el("strong", {}, "Thank you for choosing! "), "You locked in ", el("strong", {}, h ? h.name : mine.hero_id), " as ", el("strong", {}, mine.player_name), "."),
          el("p", { class: "small" }, "Locked is locked. Need a change? Ask an organiser."));
      } else {
        text.append(el("p", {}, DEMO ? el("span", { class: "demo-flag" }, "Demo mode") : null, "Welcome, ", el("strong", {}, state.user.name), "!"),
          el("p", { class: "small" }, state.locksOpen ? "Choose an available hero below to lock it in." : "Hero locks are closed."));
      }
      who.append(text);
      kids.push(who, el("button", { class: "btn ghost", type: "button", onclick: () => api.signOut().then(refresh) }, "Log out"));
    }
    box.replaceChildren(...kids);
  }

  // ---------- actions ----------
  async function signIn() {
    try { await api.signIn(); await refresh(); } catch (e) { toast("Discord login failed: " + (e.message || e), true); }
  }

  function setStage(h) {
    const stage = $("dlg-stage"), cut = $("dlg-cutout");
    stage.hidden = !h; stage.classList.remove("locked");
    $("dlg-stamp").hidden = true; $("dlg-sparkles").replaceChildren();
    if (!h) return;
    stage.style.setProperty("--c", h.colour);
    // fabtcg.com hero-selector cut-out: small version first, then full size, then the round icon.
    const sources = [h.cutout, h.cutoutFull, h.icon].filter(Boolean);
    let i = 0;
    cut.referrerPolicy = "no-referrer"; cut.alt = h.name;
    cut.onerror = () => { if (i < sources.length) cut.src = sources[i++]; };
    cut.removeAttribute("src"); cut.src = sources[i++];
    cut.style.animation = "none"; void cut.offsetWidth; cut.style.animation = "";   // replay the break-out each time
  }

  function sparkle() {
    const box = $("dlg-sparkles"), colours = ["#fff", "#dab45f", "#ffe9a8", "#ff6b6b", "#9be28a"];
    const bits = [];
    for (let n = 0; n < 26; n++) {
      const ang = (Math.PI * 2 * n) / 26 + Math.random() * 0.4, dist = 90 + Math.random() * 170;
      const b = document.createElement("i");
      b.style.setProperty("--x", Math.cos(ang) * dist + "px");
      b.style.setProperty("--y", Math.sin(ang) * dist * 0.75 + "px");
      b.style.setProperty("--s", 8 + Math.random() * 20 + "px");
      b.style.setProperty("--k", colours[n % colours.length]);
      b.style.setProperty("--d", 0.28 + Math.random() * 0.25 + "s");
      b.style.setProperty("--t", 0.9 + Math.random() * 0.7 + "s");
      bits.push(b);
    }
    box.replaceChildren(...bits);
  }

  // The "locked in" moment: slam the name label onto the hero, sparkle, then hand over to the top section.
  function celebrate(h, name) {
    return new Promise((done) => {
      const stamp = $("dlg-stamp");
      stamp.replaceChildren(el("small", {}, "Locked in"), name);
      stamp.hidden = false;
      $("dlg-stage").classList.add("locked");
      sparkle();
      $("dlg-action").replaceChildren(el("p", { class: "locked-msg" }, `${h.name.split(",")[0]} is yours!`));
      setTimeout(done, REDUCED ? 1200 : 2700);
    });
  }

  function openDialog(h) {
    const dlg = $("pick-dialog");
    setStage(h);
    $("dlg-name").textContent = h.name;
    $("dlg-class").textContent = h.cls + " · Young hero";
    $("dlg-stats").textContent = `Life ${h.life} · Intellect ${h.int}`;
    $("pick-form").onsubmit = (ev) => ev.preventDefault();
    const action = $("dlg-action");
    const mine = myPick();
    if (!state.user) {
      action.replaceChildren(el("p", { class: "note" }, "Log in with Discord to lock in this hero."),
        el("button", { class: "btn discord", type: "button", onclick: signIn }, DISCORD_ICON(), "Log in with Discord"));
    } else if (mine) {
      action.replaceChildren(el("p", { class: "note" }, `You already locked in ${byId[mine.hero_id] ? byId[mine.hero_id].name : "a hero"}. Each player gets one hero.`));
    } else if (!state.locksOpen) {
      action.replaceChildren(el("p", { class: "note" }, "Hero locks are closed."));
    } else {
      const input = el("input", { id: "player-name", name: "player", required: true, minlength: 2, maxlength: 32, autocomplete: "name", value: state.user.name.slice(0, 32) });
      const btn = el("button", { class: "btn", type: "submit" }, "Lock in " + h.name.split(",")[0]);
      action.replaceChildren(
        el("label", { class: "field" }, el("span", {}, "Your name"), input),
        el("p", { class: "warn" }, "Locked is locked: you can't change your hero afterwards. Your name and Discord tag are shown publicly next to it."),
        btn);
      $("pick-form").onsubmit = async (ev) => {
        ev.preventDefault();
        if (btn.disabled) return;
        const name = input.value.trim().replace(/\s+/g, " ");
        if (name.length < 2) { input.focus(); return; }
        btn.disabled = true;
        try {
          await api.lock(h.id, name);
        } catch (e) {
          const msg = String((e && e.message) || "");
          if (e && e.code === "23505") toast(msg.includes("user_id") ? "You have already locked in a hero." : `Too slow! ${h.name} was just locked by someone else.`, true);
          else if (e && e.code === "42501") toast("That hero can't be locked right now (locks closed or hero benched).", true);
          else toast("Could not lock hero: " + msg, true);
          dlg.close();
          await refresh();
          return;
        }
        await celebrate(h, name);
        dlg.close();
        state.freshId = h.id;
        await refresh();
        const tile = $("pick-" + h.id);
        (tile || $("locked")).scrollIntoView({ behavior: REDUCED ? "auto" : "smooth", block: "center" });
        toast("Thank you for choosing! See you at the Shuffle.");
        setTimeout(() => { state.freshId = null; }, 4000);
      };
    }
    dlg.showModal();
  }

  async function removePick(h, pick) {
    // Two-step confirm without a blocking browser dialog.
    const dlg = $("pick-dialog");
    setStage(null);
    $("dlg-name").textContent = h.name;
    $("dlg-class").textContent = "Organiser action";
    $("dlg-stats").textContent = "";
    $("pick-form").onsubmit = (ev) => ev.preventDefault();
    $("dlg-action").replaceChildren(
      el("p", { class: "warn" }, `Remove ${pick.player_name}'s lock on ${h.name}? The hero becomes available again and they can pick a new one.`),
      el("button", { class: "btn danger", type: "button", onclick: async () => {
        try { await api.remove(h.id); toast("Lock removed."); } catch (e) { toast("Could not remove: " + (e.message || e), true); }
        dlg.close(); await refresh();
      } }, "Remove lock"));
    dlg.showModal();
  }

  let refreshing = false;
  async function refresh() {
    if (refreshing) return;
    refreshing = true;
    try {
      const rows = await api.loadPicks();
      state.picks = new Map(rows.filter((p) => byId[p.hero_id]).map((p) => [p.hero_id, p]));
    } catch (e) {
      toast("Could not load hero locks: " + (e.message || e), true);
    } finally { refreshing = false; }
    render();
  }

  // ---------- boot ----------
  $("event-date").textContent = CFG.eventDate || "the day";
  $("banner-line").textContent = CFG.bannerLine || "";
  $("banner-line").hidden = !CFG.bannerLine;
  $("venue").textContent = CFG.venue || "the armory";
  $("search").addEventListener("input", (e) => { state.filter = e.target.value; render(); });
  $("dlg-close").addEventListener("click", () => $("pick-dialog").close());
  $("pick-dialog").addEventListener("click", (e) => { if (e.target === e.currentTarget) e.currentTarget.close(); });
  $("choose-btn").addEventListener("click", (e) => { e.preventDefault(); $("available").scrollIntoView({ behavior: REDUCED ? "auto" : "smooth" }); });
  render();
  api.init(refresh).then(refresh).catch((e) => { toast("Could not connect: " + (e.message || e), true); });
})();
