/* Product page behaviour: one shared pack selection drives the price block,
   the pack radios, the phone sticky bar and the order passed to checkout. */
(function () {
  var WN = window.WN;
  var $ = function (id) { return document.getElementById(id); };
  var state = { pack: WN.packFromUrl().pack };

  /* Keep the evidence module after the purchase actions and before reviews. */
  var evidence = $('evidence');
  var ctas = $('ctas');
  var reviews = $('reviews');
  var usage = document.querySelector('#evidence .usage');
  var suitability = $('suitability');
  if (evidence && ctas && reviews) {
    reviews.parentNode.insertBefore(evidence, reviews);
  }
  if (usage && suitability) {
    suitability.parentNode.insertBefore(usage, suitability);
  }

  /* ---------- pack selector ---------- */
  function renderPacks() {
    var html = WN.PACKS.map(function (p) {
      var id = 'pack-' + p.tubs;
      return '<div class="pack">' +
        '<input type="radio" name="pack" id="' + id + '" value="' + p.tubs + '">' +
        '<label for="' + id + '">' +
          '<span><span class="pack-name">' + WN.esc(p.label) + '</span>' +
            '<br><span class="pack-day">about ₹' + WN.PER_DAY + ' a day</span>' +
            '<br><span class="tag offer" style="margin-left:0">Save 20%</span></span>' +
          '<span class="pack-price"><b>' + WN.rupees(p.price) + '</b><s>' + WN.rupees(p.mrp) + '</s></span>' +
        '</label></div>';
    }).join('');
    $('pack-options').innerHTML = html;
    $('sticky-select').innerHTML = WN.PACKS.map(function (p) {
      return '<option value="' + p.tubs + '">' + WN.esc(p.label) + '</option>';
    }).join('');
    document.querySelectorAll('input[name="pack"]').forEach(function (r) {
      r.addEventListener('change', function () { setPack(r.value); });
    });
    $('sticky-select').addEventListener('change', function (e) { setPack(e.target.value); });
  }

  function setPack(tubs) {
    var p = WN.getPack(tubs);
    if (!p) return;
    state.pack = p;
    render();
    // Keep the selection in the URL so Back and Refresh restore it.
    var url = new URL(window.location.href);
    url.searchParams.set('tubs', p.tubs);
    history.replaceState(null, '', url);
  }

  function render() {
    var p = state.pack;
    var radio = $('pack-' + p.tubs);
    if (radio) radio.checked = true;
    $('sticky-select').value = String(p.tubs);
    $('price-now').textContent = WN.rupees(p.price);
    $('price-mrp').textContent = WN.rupees(p.mrp);
    $('price-pack').textContent = 'for ' + p.label + ' · inclusive of all taxes';
    var online = WN.totalFor(p, 'online');
    if (online.confirmed) {
      $('price-online').innerHTML = WN.rupees(online.amount) + ' when you pay online';
      $('offer-online').textContent = WN.rupees(online.amount) + ' for ' + p.label.split(' · ')[0];
    } else {
      $('price-online').innerHTML = 'Online price for ' + WN.esc(p.label.split(' · ')[0]) + ': <span class="v">[V] to be confirmed</span>';
      $('offer-online').innerHTML = 'Online price for ' + WN.esc(p.label.split(' · ')[0]) + ': <span class="v">[V] to be confirmed</span>';
    }
    $('sticky-price').textContent = WN.rupees(p.price) + ' · ' + p.label;
    var href = 'checkout.html?tubs=' + p.tubs;
    $('buy-now').href = href;
    $('sticky-buy').href = href;
    $('course-note').hidden = !p.recommended;
    $('per-day').textContent = WN.PER_DAY;
    $('cart-status').textContent = '';
  }

  $('add-to-cart').addEventListener('click', function () {
    var p = state.pack;
    $('cart-status').innerHTML = 'Added ' + WN.esc(p.label) + ' to your cart. <a href="checkout.html?tubs=' + p.tubs + '">Go to checkout</a>';
  });
  $('sticky-add-to-cart').addEventListener('click', function () {
    $('add-to-cart').click();
  });

  /* On desktop, show the quick-buy footer only after the primary CTAs leave view. */
  var stickyBar = $('sticky-bar');
  var ctaVisibility = window.matchMedia('(min-width: 1024px)');
  function syncStickyBar() {
    if (!ctaVisibility.matches) {
      stickyBar.classList.add('is-visible');
      stickyBar.setAttribute('aria-hidden', 'false');
      return;
    }
    var rect = $('ctas').getBoundingClientRect();
    var visible = rect.bottom > 0 && rect.top < window.innerHeight;
    stickyBar.classList.toggle('is-visible', !visible);
    stickyBar.setAttribute('aria-hidden', visible ? 'true' : 'false');
  }
  syncStickyBar();
  window.addEventListener('scroll', syncStickyBar, { passive: true });
  window.addEventListener('resize', syncStickyBar);
  if (ctaVisibility.addEventListener) ctaVisibility.addEventListener('change', syncStickyBar);

  /* ---------- suitability panel: open on laptop, collapsible on phone ---------- */
  var mq = window.matchMedia('(min-width: 1024px)');
  function syncSuitability() { $('suitability').open = mq.matches; }
  syncSuitability();
  if (mq.addEventListener) mq.addEventListener('change', syncSuitability);

  /* ---------- reviews ---------- */
  function starStr(n) { return '★★★★★'.slice(0, n) + '☆☆☆☆☆'.slice(0, 5 - n); }
  function dateHtml(r) { return r.date ? WN.esc(r.date) : '<span class="v">[V] date</span>'; }
  function reviewHtml(r) {
    return '<article class="review"><div class="review-head">' +
      '<span class="stars" aria-label="' + r.stars + ' out of 5 stars">' + starStr(r.stars) + '</span>' +
      (r.verified ? '<span class="badge-verified">Verified</span>' : '') +
      '<b>' + WN.esc(r.name) + '</b><span class="review-date">' + dateHtml(r) + '</span></div>' +
      '<p style="margin:6px 0 0">' + WN.esc(r.text) + '</p></article>';
  }
  function renderReviews(filter) {
    var list = WN.REVIEWS.filter(function (r) { return filter === 'critical' ? r.stars <= 3 : true; });
    // Lowest ratings are not hidden: the default order is newest-as-captured, not best-first.
    $('review-list').innerHTML = list.length ? list.map(reviewHtml).join('') :
      '<p class="empty-state">No critical reviews yet.</p>' +
      '<p class="v-note"><span class="v">[V]</span> The rating summary includes one 3★ rating whose text was not available for this prototype.</p>';
  }
  var R = WN.RATING;
  $('dist').innerHTML = [5, 4, 3, 2, 1].map(function (s) {
    var n = R.dist[s], pct = Math.round((n / R.count) * 100);
    return '<li><span>' + s + '★</span><span class="bar" aria-hidden="true"><i style="width:' + pct + '%"></i></span><span>' + n + '</span></li>';
  }).join('');
  ['avg', 'avg-inline'].forEach(function (id) { $(id).textContent = R.average; });
  ['count', 'count-inline'].forEach(function (id) { $(id).textContent = R.count; });
  var featured = WN.REVIEWS.find(function (r) { return r.featured; });
  $('featured-review').innerHTML = '<div class="review-head"><b>' + R.average + '/5</b><span>from ' + R.count +
    ' ratings</span><a href="#reviews">See all</a></div>' + reviewHtml(featured).replace('class="review"', 'class="review" style="border:0;padding:8px 0 0"');
  document.querySelectorAll('[data-filter]').forEach(function (b) {
    b.addEventListener('click', function () {
      document.querySelectorAll('[data-filter]').forEach(function (x) { x.setAttribute('aria-pressed', String(x === b)); });
      renderReviews(b.dataset.filter);
    });
  });
  renderReviews('all');

  /* ---------- "Show what changed" ---------- */
  var tgl = $('toggle-changes');
  tgl.addEventListener('click', function () {
    var on = tgl.getAttribute('aria-pressed') !== 'true';
    tgl.setAttribute('aria-pressed', String(on));
    tgl.textContent = on ? 'Hide what changed' : 'Show what changed';
    document.body.classList.toggle('show-changes', on);
  });

  renderPacks();
  setPack(state.pack.tubs);
})();
