/* Mock checkout: reads the pack from ?tubs=, shows prices from data.js,
   validates fields inline, and passes the order to confirmation.html. */
(function () {
  var WN = window.WN;
  var $ = function (id) { return document.getElementById(id); };
  var parsed = WN.packFromUrl();
  var pack = parsed.pack;
  if (parsed.invalid) $('invalid-note').hidden = false;
  $('back-link').href = 'index.html?tubs=' + pack.tubs;

  var online = WN.totalFor(pack, 'online');
  $('price-cod').textContent = WN.rupees(pack.price);
  $('price-online-opt').innerHTML = online.confirmed ? WN.rupees(online.amount) :
    WN.rupees(pack.price) + ' <span class="v">[V]</span>';
  $('sum-pack').textContent = pack.label;
  $('sum-price').textContent = WN.rupees(pack.price);
  $('sum-mrp').textContent = WN.rupees(pack.mrp);

  function method() { return document.querySelector('input[name="pay"]:checked').value; }
  function updateTotal() {
    var m = method(), t = WN.totalFor(pack, m);
    $('sum-method').textContent = m === 'cod' ? 'Cash on delivery' : 'Pay online';
    $('sum-total').textContent = WN.rupees(t.amount);
    $('sum-note').hidden = t.confirmed;
    if (!t.confirmed) $('sum-note').innerHTML = '<span class="v">[V]</span> The online price for ' + WN.esc(pack.label.split(' · ')[0]) + ' is not confirmed, so the pack price is shown.';
  }
  document.querySelectorAll('input[name="pay"]').forEach(function (r) { r.addEventListener('change', updateTotal); });
  updateTotal();

  var rules = {
    name: function (v) { return v.trim() ? '' : 'Please enter your name.'; },
    phone: function (v) { return /^[0-9]{10}$/.test(v.trim()) ? '' : 'Please enter a 10-digit mobile number.'; },
    address: function (v) { return v.trim() ? '' : 'Please enter your delivery address.'; }
  };
  function check(id) {
    var el = $(id), msg = rules[id](el.value);
    $(id + '-err').textContent = msg;
    el.setAttribute('aria-invalid', msg ? 'true' : 'false');
    return !msg;
  }
  Object.keys(rules).forEach(function (id) {
    $(id).addEventListener('blur', function () { if ($(id).value) check(id); });
    $(id).addEventListener('input', function () { if ($(id).getAttribute('aria-invalid') === 'true') check(id); });
  });

  $('checkout-form').addEventListener('submit', function (e) {
    e.preventDefault();
    var ok = Object.keys(rules).map(check).every(Boolean);
    if (!ok) {
      var first = Object.keys(rules).find(function (id) { return $(id).getAttribute('aria-invalid') === 'true'; });
      $(first).focus();
      return;
    }
    // Only the order details travel to the confirmation page; personal details are not stored or sent.
    window.location.href = 'confirmation.html?tubs=' + pack.tubs + '&pay=' + method();
  });

  var tgl = $('toggle-changes');
  tgl.addEventListener('click', function () {
    var on = tgl.getAttribute('aria-pressed') !== 'true';
    tgl.setAttribute('aria-pressed', String(on));
    tgl.textContent = on ? 'Hide what changed' : 'Show what changed';
    document.body.classList.toggle('show-changes', on);
  });
})();
