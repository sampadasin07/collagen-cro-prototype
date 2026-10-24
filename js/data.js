/* data.js: single source of truth for every price, pack and fixed value.
   Values are from the strategy PDF (prices observed on the live page, 21 Oct 2026).
   Items marked V are unconfirmed and must render as visible placeholders. */
window.WN = {
  PRICES_OBSERVED: '21 Oct 2026',
  PACKS: [
    { tubs: 1, days: 25,  price: 1439, mrp: 1799, onlinePrice: 1367, label: '1 tub · 25 days',  isDefault: true },
    { tubs: 2, days: 50,  price: 2878, mrp: 3598, onlinePrice: 2734, label: '2 tubs · 50 days' },
    { tubs: 3, days: 75,  price: 4318, mrp: 5397, onlinePrice: 4102, label: '3 tubs · 75 days' },
    { tubs: 4, days: 100, price: 5757, mrp: 7196, onlinePrice: 5469, label: '4 tubs · 100 days · Recommended', recommended: true }
  ],
  PER_DAY: 58,              // ₹1,439 ÷ 25 servings ≈ ₹58; identical for every pack (linear pricing)
  RATING: { average: 4.74, count: 571, dist: { 5: 424, 4: 146, 3: 1, 2: 0, 1: 0 } },
  // Real reviews copied from the live product page (screenshot, 21 Oct 2026). Dates not captured: V.
  REVIEWS: [
    { name: 'Vikash M', stars: 4, verified: true, date: null,
      text: "I'm unable to notice any changes, but my friend n my parents are able to notice the change in my skin health", featured: true },
    { name: 'Harpreet singh', stars: 5, verified: true, date: null,
      text: 'Pure Korean Marine Collagen Peptides | Unflavored | Combat Signs of Ageing' },
    { name: 'Pranvi .', stars: 5, verified: true, date: null,
      text: 'Pure Korean Marine Collagen Peptides | Unflavored | Combat Signs of Ageing' },
    { name: 'Siddharth Kaul', stars: 5, verified: true, date: null,
      text: 'Pure Korean Marine Collagen Peptides | Unflavored | Combat Signs of Ageing' },
    { name: '[V] review text unavailable', stars: 3, verified: true, date: null,
      text: '[V] The text for this 3-star review was not available in the captured product-page data.' }
  ],
  VEGAN_URL: 'https://wellbeingnutrition.com/collections/vegan-collagen',
  DECK_URL: 'pssol.pdf'              
};

window.WN.getPack = function (tubs) {
  var n = parseInt(tubs, 10);
  return window.WN.PACKS.find(function (p) { return p.tubs === n; }) || null;
};
window.WN.defaultPack = function () {
  return window.WN.PACKS.find(function (p) { return p.isDefault; });
};
window.WN.rupees = function (n) {
  return '₹' + Number(n).toLocaleString('en-IN');
};

/* Shared order logic used by the product page, checkout and confirmation.
   Prepaid prices apply the same 5% discount to every pack and are rounded to
   the nearest rupee, matching the displayed 1-tub price. */
window.WN.totalFor = function (pack, method) {
  if (method === 'online') {
    if (pack.onlinePrice != null) return { amount: pack.onlinePrice, confirmed: true };
    return { amount: pack.price, confirmed: false };
  }
  return { amount: pack.price, confirmed: true };
};
window.WN.packFromUrl = function () {
  var params = new URLSearchParams(window.location.search);
  var raw = params.get('tubs');
  var pack = raw === null ? null : window.WN.getPack(raw);
  return { pack: pack || window.WN.defaultPack(), invalid: raw !== null && !pack };
};
window.WN.esc = function (s) {
  return String(s).replace(/[&<>"']/g, function (c) {
    return { '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c];
  });
};
