/* ============================================================================
   הר-אל פתרונות מימון חכמים — סקריפט האתר
   ========================================================================== */
(function () {
  'use strict';

  /* ----- הגדרות ----------------------------------------------------------
     שלושת הקבועים הבאים נלקחו מדף הנחיתה הקיים של הר-אל.
     GOOGLE_SHEET_ENDPOINT — הליד נשמר בגיליון הגוגל של החברה.
     WHATSAPP_NUMBER      — אם ימולא (למשל 972501234567) כפתורי הוואטסאפ
                            יפנו לשיחה אישית במקום לקבוצה.
  --------------------------------------------------------------------- */
  var GOOGLE_SHEET_ENDPOINT = 'https://script.google.com/macros/s/AKfycbzcymIiOkEdPvAphqr1f-WCLOtPuGn4A2ioR0koczRD1_1mGZeIPNhKBbtDVSQryTOoVQ/exec';
  var WHATSAPP_NUMBER = '';
  var WHATSAPP_GROUP = 'https://chat.whatsapp.com/CWus7C38efWAlNnL59mqu9?s=cl&p=a&ilr=0&amv=0';

  var waLink = WHATSAPP_NUMBER
    ? 'https://wa.me/' + WHATSAPP_NUMBER.replace(/\D/g, '')
    : WHATSAPP_GROUP;

  document.querySelectorAll('a.btn-wa, a.wa-float').forEach(function (a) {
    a.href = waLink;
    a.target = '_blank';
    a.rel = 'noopener';
  });

  /* ----- תפריט מובייל ---------------------------------------------------- */
  (function () {
    var burger = document.querySelector('.burger');
    var drawer = document.getElementById('drawer');
    if (!burger || !drawer) return;

    function setOpen(open) {
      burger.setAttribute('aria-expanded', open ? 'true' : 'false');
      drawer.classList.toggle('open', open);
      document.body.style.overflow = open ? 'hidden' : '';
    }
    burger.addEventListener('click', function () {
      setOpen(burger.getAttribute('aria-expanded') !== 'true');
    });
    drawer.addEventListener('click', function (e) {
      if (e.target.closest('a')) setOpen(false);
    });
    document.addEventListener('keydown', function (e) {
      if (e.key === 'Escape') setOpen(false);
    });
    document.addEventListener('click', function (e) {
      if (burger.getAttribute('aria-expanded') !== 'true') return;
      if (!drawer.contains(e.target) && !burger.contains(e.target)) setOpen(false);
    });
    window.addEventListener('resize', function () {
      if (window.innerWidth >= 1000) setOpen(false);
    });
  })();

  /* ----- חשיפה בגלילה ---------------------------------------------------- */
  (function () {
    var els = document.querySelectorAll('.reveal');
    if (!els.length) return;
    if (!('IntersectionObserver' in window)) {
      els.forEach(function (e) { e.classList.add('in'); });
      return;
    }
    var io = new IntersectionObserver(function (entries) {
      entries.forEach(function (en) {
        if (en.isIntersecting) { en.target.classList.add('in'); io.unobserve(en.target); }
      });
    }, { threshold: 0.08, rootMargin: '0px 0px -40px 0px' });
    els.forEach(function (e) { io.observe(e); });
  })();

  /* ----- טופס יצירת קשר -------------------------------------------------- */
  document.querySelectorAll('form.lead-form').forEach(function (form) {
    var card = form.closest('.form-card');
    var btn = form.querySelector('button[type="submit"]');
    var btnText = btn ? btn.textContent : '';

    function field(name) { return form.elements[name] || null; }
    function mark(el, bad) {
      var wrap = el.closest('.field');
      if (wrap) wrap.classList.toggle('err', bad);
      return !bad;
    }
    var phoneOk = function (v) { return /^0\d{8,9}$/.test(v.replace(/\D/g, '')); };
    var mailOk = function (v) { return /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(v.trim()); };

    form.querySelectorAll('input, select, textarea').forEach(function (el) {
      ['input', 'change'].forEach(function (ev) {
        el.addEventListener(ev, function () {
          var wrap = el.closest('.field');
          if (wrap) wrap.classList.remove('err');
        });
      });
    });

    form.addEventListener('submit', function (e) {
      e.preventDefault();

      var honey = field('company');
      if (honey && honey.value) return;              // מלכודת בוטים

      var ok = true;
      var name = field('fullname'), phone = field('phone');
      var email = field('email'), topic = field('topic'), consent = field('consent');

      if (name) ok = mark(name, name.value.trim().length < 2) && ok;
      if (phone) ok = mark(phone, !phoneOk(phone.value)) && ok;
      if (email && (email.required || email.value.trim())) ok = mark(email, !mailOk(email.value)) && ok;
      if (topic) ok = mark(topic, !topic.value) && ok;
      if (consent) ok = mark(consent, !consent.checked) && ok;

      if (!ok) {
        var bad = form.querySelector('.field.err :is(input,select,textarea)');
        if (bad) bad.focus();
        return;
      }

      if (btn) { btn.disabled = true; btn.textContent = 'שולח…'; }

      var data = { source: form.dataset.source || document.title, timestamp: new Date().toLocaleString('he-IL') };
      ['fullname', 'phone', 'email', 'topic', 'amount', 'message'].forEach(function (k) {
        var el = field(k);
        if (el && el.value) data[k] = el.value.trim();
      });

      var done = function () {
        if (!card) return;
        card.classList.add('done');
        card.scrollIntoView({ behavior: 'smooth', block: 'center' });
      };

      if (GOOGLE_SHEET_ENDPOINT) {
        fetch(GOOGLE_SHEET_ENDPOINT, {
          method: 'POST',
          mode: 'no-cors',
          headers: { 'Content-Type': 'application/x-www-form-urlencoded;charset=UTF-8' },
          body: new URLSearchParams(data).toString()
        }).then(done, done);
      } else {
        done();
      }
    });
  });

  /* ----- שנה נוכחית בפוטר ------------------------------------------------ */
  document.querySelectorAll('.year').forEach(function (el) {
    el.textContent = new Date().getFullYear();
  });
})();
