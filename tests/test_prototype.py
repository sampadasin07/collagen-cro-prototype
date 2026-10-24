import asyncio, re, json, sys
from playwright.async_api import async_playwright
BASE = 'http://127.0.0.1:8765/'
results = []
def rec(name, ok, detail=''):
    results.append((name, bool(ok), detail)); print(('PASS' if ok else 'FAIL'), name, detail)

PROHIBITED = ['13237', 'allergen-free', 'MDPI', '4x', '1.5x', '5x better', '4–8 weeks', '4-8 weeks', '8–12 weeks', '8-12 weeks',
              '12 weeks', 'Clinically Proven', 'Backed by 20+', 'Out of Stock', 'out of stock', 'Spin', 'subscribe', 'Subscribe',
              'sachet', 'Amazon', 'Nykaa', 'pincode', 'Pincode', 'countdown', '%', 'conversion']

async def main():
    async with async_playwright() as p:
        b = await p.chromium.launch()
        errors = []
        async def page_at(w, h=900, url='index.html'):
            ctx = await b.new_context(viewport={'width': w, 'height': h}, has_touch=w < 1024)
            pg = await ctx.new_page()
            pg.on('console', lambda m: errors.append(f'{m.type}: {m.text}') if m.type in ('error','warning') else None)
            pg.on('pageerror', lambda e: errors.append(f'pageerror: {e}'))
            await pg.goto(BASE + url); await pg.wait_for_load_state('networkidle')
            return ctx, pg

        # ---------- Prohibited text on the shop pages ----------
        for url in ['index.html', 'checkout.html', 'confirmation.html']:
            ctx, pg = await page_at(1280, url=url)
            txt = await pg.evaluate("document.body.innerText")
            html = await pg.content()
            hits = [w for w in PROHIBITED if w in txt and not (w == '%' and False)]
            # '%' allowed only in "20% off", "Save 20%", "Extra 5% off" and "10% OFF"
            if '%' in hits:
                stray = re.sub(r'(20% off|Save 20%|Extra 5% off|10% OFF)', '', txt)
                if '%' not in stray: hits.remove('%')
            # 'conversion' allowed nowhere on shop pages
            rec(f'C2 prohibited text absent: {url}', not hits, ','.join(hits))
            await ctx.close()

        # ---------- Product page, laptop ----------
        ctx, pg = await page_at(1280)
        rec('Default pack is 1 tub', await pg.is_checked('#pack-1'))
        rec('Headline ₹1,439 / MRP ₹1,799', (await pg.text_content('#price-now')) == '₹1,439' and (await pg.text_content('#price-mrp')) == '₹1,799')
        rec('Online line for 1 tub', (await pg.text_content('#price-online')).strip() == '₹1,367 when you pay online')
        rec('Free shipping shown', 'Free shipping on this order' in await pg.text_content('.price-block'))
        rec('Per-day line', 'Every pack works out to about ₹58 a day.' in await pg.text_content('.per-day'))
        labels = await pg.eval_on_selector_all('.pack-name', 'els => els.map(e => e.textContent)')
        rec('Pack labels exact', labels == ['1 tub · 25 days','2 tubs · 50 days','3 tubs · 75 days','4 tubs · 100 days · Recommended'], str(labels))
        rec('Every pack shows cost per day', (await pg.eval_on_selector_all('.pack-day', 'e=>e.map(x=>x.textContent)')) == ['about ₹58 a day'] * 4)
        rec('COD price is identified', 'COD price' in await pg.text_content('.price-block'))
        expected = {1:('₹1,439','₹1,799'),2:('₹2,878','₹3,598'),3:('₹4,318','₹5,397'),4:('₹5,757','₹7,196')}
        for t,(pr,mrp) in expected.items():
            await pg.click(f'label[for=pack-{t}]')
            ok = (await pg.text_content('#price-now')) == pr and (await pg.text_content('#price-mrp')) == mrp
            ok &= (await pg.get_attribute('#buy-now','href')) == f'checkout.html?tubs={t}'
            ok &= (await pg.input_value('#sticky-select')) == str(t)
            ok &= f'tubs={t}' in pg.url
            online = await pg.text_content('#price-online')
            expected_online = {1: '₹1,367', 2: '₹2,734', 3: '₹4,102', 4: '₹5,469'}[t]
            ok &= expected_online in online
            rec(f'Select pack {t}: price, MRP, sticky, URL, online line', ok, online.strip())
        rec('Recommended is part of the 4-tub label', '4 tubs · 100 days · Recommended' in await pg.text_content('label[for=pack-4]'))
        rec('Course note marked [V] when 4 tubs', await pg.is_visible('#course-note') and '[V]' in await pg.text_content('#course-note'))
        # keyboard radio
        await pg.click('label[for=pack-1]'); await pg.focus('#pack-1'); await pg.keyboard.press('ArrowDown')
        rec('Keyboard ArrowDown moves to 2 tubs', await pg.is_checked('#pack-2') and (await pg.text_content('#price-now')) == '₹2,878')
        # offers details
        rec('Offers block closed by default', not await pg.eval_on_selector('#offers', 'e=>e.open'))
        await pg.click('#offers summary')
        ot = await pg.text_content('#offers')
        rec('Offers block opens; contains 10% OFF, member price, prepaid, [V] stacking', await pg.eval_on_selector('#offers','e=>e.open') and all(s in ot for s in ['Get 10% OFF','Member price','Extra 5% off','[V]']))
        rec('Suitability open on laptop', await pg.eval_on_selector('#suitability', 'e=>e.open'))
        st = await pg.text_content('#suitability')
        rec('Suitability text complete', all(s in st for s in ['Made from fish','allergic to fish or shellfish','Consult your doctor first','Best before:','[V] MM/YYYY','Replacement if damaged or incorrect (report within 48 hours)','See our vegan collagen']))
        rec('No fish species named', not re.search(r'\b(salmon|tilapia|pollock)\b', (await pg.text_content('#suitability')).lower()))
        # evidence below benefits
        pos = await pg.evaluate("(()=>{const a=document.querySelector('#ctas').getBoundingClientRect().bottom+scrollY;const b=document.querySelector('#evidence').getBoundingClientRect().top+scrollY;const c=document.querySelector('#reviews').getBoundingClientRect().top+scrollY;return {gap:b-a,beforeReviews:b<c}})()")
        rec('Evidence module follows purchase actions and precedes reviews', pos['gap'] >= 0 and pos['beforeReviews'], str(pos))
        ev = await pg.text_content('#evidence')
        rec('Product facts heading stays with evidence', 'Product facts & testing' in ev)
        usage = await pg.text_content('.usage')
        rec('Usage line exact', usage.strip().endswith('One 8 g scoop daily, minimum 3–4 months.'))
        order = await pg.evaluate("""(()=>{const sel=['#offers','.usage','#suitability']; return sel.map(s=>document.querySelector(s).getBoundingClientRect().top+scrollY)})()""")
        rec('Usage line follows offers and precedes suitability', order == sorted(order), str(order))
        rec('Quick facts present', all(s in ev for s in ['8 g','25','Type I & III','Unflavoured','How to mix']))
        rec('Ingredient vs product sections', 'Research on marine collagen peptides (ingredient studies)' in ev and 'Tested on this product' in ev)
        rec('Correct publishers', 'Journal of Cosmetic Dermatology (Wiley)' in ev and 'Journal of Medicinal Food (Mary Ann Liebert)' in ev)
        rec('Exactly one nutrition panel, values [V]', (await pg.eval_on_selector_all('table.nutrition','e=>e.length')) == 1 and 'to be confirmed against the approved label' in ev)
        tl = (await pg.evaluate('document.body.innerText'))
        rec('Only one timeline string on page', tl.count('3–4 months') >= 1 and not re.search(r'\b\d+\s*[–-]\s*\d+\s*weeks', tl))
        # reviews
        rt = await pg.text_content('#reviews')
        rec('Rating 4.74 / 571 / distribution', '4.74' in rt and '571' in rt and [await pg.eval_on_selector_all('#dist li span:last-child','e=>e.map(x=>x.textContent)')][0] == ['424','146','1','0','0'])
        rec('Every review shows a date or [V] date', (await pg.eval_on_selector_all('#review-list .review','e=>e.length')) == (await pg.eval_on_selector_all('#review-list .review-date','e=>e.filter(x=>x.textContent.trim()).length')))
        rec('Default filter is All', (await pg.get_attribute('[data-filter=all]','aria-pressed')) == 'true')
        await pg.click('[data-filter=critical]')
        rec('Critical filter shows only ≤3★ reviews', (await pg.eval_on_selector_all('#review-list .review-head .stars', 'e=>e.map(x=>x.getAttribute("aria-label"))')) == ['3 out of 5 stars'])
        await pg.click('[data-filter=all]')
        rec('All filter restores every captured review', (await pg.eval_on_selector_all('#review-list .review','e=>e.length')) == 5)
        rec('Featured review near buy box', 'Vikash M' in await pg.text_content('#featured-review'))
        rec('No exit pop-up (no dialogs/modals in DOM)', (await pg.eval_on_selector_all('dialog, [role=dialog], .modal, .popup','e=>e.length')) == 0)
        # what changed
        rec('Markers hidden by default', not await pg.is_visible('details.chg'))
        await pg.focus('#toggle-changes'); await pg.keyboard.press('Enter')
        vis = await pg.eval_on_selector_all('details.chg', 'e=>e.filter(x=>x.offsetParent!==null).length')
        rec('Toggle by keyboard shows 6 markers on product page', vis == 6 and (await pg.get_attribute('#toggle-changes','aria-pressed')) == 'true', str(vis))
        await pg.click('details.chg >> nth=0 >> summary')
        rec('Marker opens note with friction', 'Friction addressed' in await pg.text_content('details.chg >> nth=0'))
        await pg.click('label[for=pack-3]')
        rec('Purchase flow still works with markers on', (await pg.get_attribute('#buy-now','href')) == 'checkout.html?tubs=3')
        # add to cart
        await pg.click('#add-to-cart')
        rec('Add to cart status + checkout link', 'Go to checkout' in await pg.text_content('#cart-status'))
        # Buy it now -> checkout
        await pg.click('#buy-now'); await pg.wait_for_load_state('networkidle')
        rec('Buy it now goes straight to checkout with pack 3', pg.url.endswith('checkout.html?tubs=3') and '3 tubs · 75 days' in await pg.text_content('#sum-pack'))
        await pg.go_back(); await pg.wait_for_load_state('networkidle')
        rec('Back keeps selection (3 tubs)', await pg.is_checked('#pack-3') and (await pg.text_content('#price-now')) == '₹4,318')
        await pg.reload(); await pg.wait_for_load_state('networkidle')
        rec('Refresh keeps selection (3 tubs)', await pg.is_checked('#pack-3'))
        await ctx.close()

        # ---------- Checkout ----------
        for t in [1,2,3,4]:
            ctx, pg = await page_at(1280, url=f'checkout.html?tubs={t}')
            pr = expected[t][0]
            ok = (await pg.text_content('#sum-price')) == pr and (await pg.text_content('#sum-total')) == pr and (await pg.text_content('#price-cod')) == pr
            await pg.check('input[value=online]')
            tot = await pg.text_content('#sum-total')
            ok &= (tot == '₹1,367') if t == 1 else (tot != pr and not await pg.is_visible('#sum-note'))
            online_expected = {1: '₹1,367', 2: '₹2,734', 3: '₹4,102', 4: '₹5,469'}[t]
            ok &= tot == online_expected
            rec(f'Checkout pack {t}: COD {pr}, online {online_expected}', ok)
            await ctx.close()
        ctx, pg = await page_at(1280, url='checkout.html?tubs=4')
        rec('Notice text exact', (await pg.text_content('.notice')).strip() == 'Prototype: no payment is taken.')
        rec('Consent boxes unticked', not await pg.is_checked('#consent-updates') and not await pg.is_checked('#consent-offers'))
        rec('Consent labels exact', [s.strip() for s in await pg.eval_on_selector_all('#consent-updates, #consent-offers','e=>e.map(x=>x.parentElement.textContent)')] == ['Send me order updates','Send me offers'])
        await pg.check('#consent-updates')
        rec('Consent boxes independent', await pg.is_checked('#consent-updates') and not await pg.is_checked('#consent-offers'))
        await pg.uncheck('#consent-updates')
        rec('No warning after unticking', 'will not receive' not in (await pg.evaluate('document.body.innerText')).lower())
        await pg.click('button[type=submit]')
        errs = await pg.eval_on_selector_all('.error','e=>e.map(x=>x.textContent).filter(Boolean)')
        rec('Empty submit shows 3 inline errors, stays on page', len(errs) == 3 and 'checkout.html' in pg.url, str(errs))
        await pg.fill('#name','Test User'); await pg.fill('#phone','98765432'); await pg.fill('#address','1 Test Road')
        await pg.click('button[type=submit]')
        rec('9-digit phone rejected', 'checkout.html' in pg.url and '10-digit' in await pg.text_content('#phone-err'))
        await pg.fill('#phone','9876543210'); await pg.check('input[value=online]')
        await pg.click('button[type=submit]'); await pg.wait_for_load_state('networkidle')
        ct = await pg.evaluate('document.body.innerText')
        rec('Confirmation restates pack, method, total', 'confirmation.html?tubs=4&pay=online' in pg.url and '4 tubs · 100 days' in ct and 'Pay online' in ct and '₹5,469' in ct and '[V]' not in ct)
        rec('No personal data in confirmation URL', 'Test' not in pg.url and '9876' not in pg.url)
        await ctx.close()
        ctx, pg = await page_at(1280, url='confirmation.html?tubs=1&pay=online')
        rec('Confirmation 1 tub online = ₹1,367', (await pg.text_content('#c-total')) == '₹1,367')
        await ctx.close()
        ctx, pg = await page_at(1280, url='checkout.html?tubs=9')
        rec('Invalid ?tubs handled: default pack + note', (await pg.text_content('#sum-pack')) == '1 tub · 25 days' and await pg.is_visible('#invalid-note'))
        await pg.reload(); await pg.wait_for_load_state('networkidle')
        await ctx.close()
        ctx, pg = await page_at(1280, url='checkout.html?tubs=2')
        await pg.reload(); await pg.wait_for_load_state('networkidle')
        rec('Checkout refresh keeps pack', (await pg.text_content('#sum-pack')) == '2 tubs · 50 days')
        await pg.click('#toggle-changes')
        rec('Checkout consent marker visible when toggled', await pg.is_visible('details.chg'))
        await ctx.close()

        # ---------- Responsive ----------
        for w in [360, 390, 414, 1024, 1440]:
            ctx, pg = await page_at(w)
            for url in ['index.html','checkout.html?tubs=2','confirmation.html?tubs=2&pay=cod','about.html']:
                await pg.goto(BASE+url); await pg.wait_for_load_state('networkidle')
                sw = await pg.evaluate('document.documentElement.scrollWidth'); cw = await pg.evaluate('document.documentElement.clientWidth')
                rec(f'No horizontal scroll @{w} {url}', sw <= cw, f'{sw}>{cw}' if sw > cw else '')
            await pg.goto(BASE+'index.html'); await pg.wait_for_load_state('networkidle')
            small = await pg.evaluate("""[...document.querySelectorAll('button, a.btn, .pack label, select, details.panel>summary')].filter(e=>e.offsetParent!==null && e.getBoundingClientRect().height<44).map(e=>e.textContent.trim().slice(0,30))""")
            rec(f'Interactive targets ≥44px @{w}', not small, str(small))
            fs = await pg.evaluate("parseFloat(getComputedStyle(document.body).fontSize)")
            rec(f'Body text 16px @{w}', fs >= 16)
            sticky = await pg.is_visible('#sticky-bar')
            if w >= 1024:
                cta_visible = await pg.evaluate("""(()=>{const r=document.querySelector('#ctas').getBoundingClientRect(); return r.bottom > 0 && r.top < window.innerHeight})()""")
                rec(f'Desktop sticky matches CTA visibility @{w}', sticky == (not cta_visible))
                await pg.evaluate("document.querySelector('#ctas').scrollIntoView({block:'center'})")
                await pg.wait_for_timeout(100)
                rec(f'Desktop sticky hides while CTAs are visible @{w}', not await pg.is_visible('#sticky-bar'))
                await pg.evaluate('window.scrollTo(0, document.body.scrollHeight)')
                await pg.wait_for_timeout(100)
                rec(f'Desktop sticky bar appears after CTAs leave view @{w}', await pg.is_visible('#sticky-bar'))
                await pg.evaluate('window.scrollTo(0, 0)')
                await pg.wait_for_timeout(100)
            else:
                rec(f'Sticky bar shown @{w}', sticky)
            susp = await pg.eval_on_selector('#suitability','e=>e.open')
            rec(f'Suitability {"open" if w>=1024 else "collapsed"} @{w}', susp == (w >= 1024))
            if w < 1024:
                order = await pg.evaluate("""(()=>{const sel=['.gallery','h1','.rating-line','.benefits','.price-block','#offers','.usage','#suitability','.packs','#ctas','#evidence','#reviews','#faq'];
                  return sel.map(s=>document.querySelector(s).getBoundingClientRect().top+scrollY)})()""")
                rec(f'Mobile order gallery→title→rating→advantages→price→offers→usage→suitability→packs→CTAs→evidence→reviews→FAQ @{w}', order == sorted(order))
                # sticky select drives state
                await pg.select_option('#sticky-select','4')
                rec(f'Sticky select updates main selector @{w}', await pg.is_checked('#pack-4') and (await pg.text_content('#price-now')) == '₹5,757')
                await pg.click('#sticky-add-to-cart')
                rec(f'Sticky Add to cart uses selected pack @{w}', '4 tubs · 100 days' in await pg.text_content('#cart-status'))
                # footer reachable above sticky bar
                await pg.evaluate('window.scrollTo(0, document.body.scrollHeight)')
                ok = await pg.evaluate("""(()=>{const f=document.querySelector('.site-footer a').getBoundingClientRect();const s=document.getElementById('sticky-bar').getBoundingClientRect();return f.bottom<=s.top})()""")
                rec(f'Sticky bar does not cover last content @{w}', ok)
            else:
                lay = await pg.evaluate("""(()=>{const g=document.querySelector('.gallery').getBoundingClientRect(), b=document.querySelector('.buybox').getBoundingClientRect();return g.left<b.left && Math.abs(g.top-b.top)<60})()""")
                rec(f'Two columns: gallery left, buy box right @{w}', lay)
            await pg.screenshot(path=f'/home/claude/prototest/shot_{w}.png', full_page=True)
            await ctx.close()

        # ---------- Links and assets ----------
        ctx, pg = await page_at(1280)
        bad = []
        for url in ['index.html','checkout.html','confirmation.html','about.html']:
            await pg.goto(BASE+url)
            hrefs = await pg.eval_on_selector_all('a[href]','e=>e.map(x=>x.getAttribute("href"))')
            for h in hrefs:
                if h.startswith('http'): continue
                if h.startswith('#'):
                    if not await pg.evaluate(f"!!document.getElementById({json.dumps(h[1:])})"): bad.append(url+' '+h)
                    continue
                path = h.split('#')[0].split('?')[0]
                r = await pg.request.get(BASE+path)
                if r.status != 200: bad.append(url+' '+h)
                if '#' in h:
                    await pg.goto(BASE+h); 
                    if not await pg.evaluate(f"!!document.getElementById({json.dumps(h.split('#')[1])})"): bad.append(h)
                    await pg.goto(BASE+url)
        rec('All internal links and anchors resolve', not bad, str(bad))
        imgs = await pg.evaluate("[...document.images].filter(i=>!i.complete||i.naturalWidth===0).length")
        rec('All images load', imgs == 0)
        await ctx.close()
        rec('No console errors or warnings', not errors, str(errors[:5]))
        await b.close()
    fails = [r for r in results if not r[1]]
    print(f'\n{len(results)-len(fails)}/{len(results)} passed')
    json.dump(results, open('/home/claude/prototest/results.json','w'))
asyncio.run(main())
