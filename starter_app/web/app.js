/* FareForge student app. NEVER present fictional demo data as live travel offers. */
const el = id => document.getElementById(id);
const money = v => typeof v === 'number' && Number.isFinite(v)
  ? new Intl.NumberFormat('en-US', {style:'currency',currency:'USD'}).format(v) : 'Not available';
const safe = value => String(value ?? '').replace(/[&<>"']/g, m => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[m]));
let searchVersion = 0;
const scenarios = {
  nyc: { origin:'DALLAS',destination:'NYC',depart_date:'2027-03-11',return_date:'2027-03-15',travelers:1 },
  tokyo:{origin:'DALLAS',destination:'TOKYO',depart_date:'2027-04-23',return_date:'2027-04-30',travelers:2},
  vegas:{origin:'DALLAS',destination:'LAS VEGAS',depart_date:'2027-05-20',return_date:'2027-05-23',travelers:2}
};
const getRequest = () => ({
  origin:el('origin').value.trim(),destination:el('destination').value.trim(),
  depart_date:el('departDate').value,return_date:el('returnDate').value,
  travelers:Number(el('travelers').value),mode:el('mode').value,
  checked_bag:el('checkedBag').checked,carry_on:el('carryOn').checked,
  card_name:el('cardName').value,card_multiplier:Number(el('cardMultiplier').value),
  point_value_cents:Number(el('pointValue').value),award_points_balance:Number(el('pointsBalance').value)
});
for(const button of document.querySelectorAll('[data-case]')){
  button.addEventListener('click',()=>{
    const s=scenarios[button.dataset.case];
    el('origin').value=s.origin;el('destination').value=s.destination;
    el('departDate').value=s.depart_date;el('returnDate').value=s.return_date;
    el('travelers').value=s.travelers;el('mode').value='demo';
    doSearch();
  });
}
el('tripForm').addEventListener('submit',event=>{event.preventDefault();doSearch();});

/* ---------- formatting helpers (all output passes through safe()) ---------- */
// Only provider-supplied http(s) links are rendered; anything else is dropped.
function safeLink(url,label){
  try{
    const parsed=new URL(String(url));
    if(parsed.protocol!=='https:'&&parsed.protocol!=='http:')return '';
    return `<a class="source-link" href="${safe(parsed.href)}" target="_blank" rel="noopener noreferrer">${safe(label)} ↗</a>`;
  }catch{return '';}
}
function utcTime(iso){
  const d=new Date(iso);
  if(!iso||Number.isNaN(d.getTime()))return 'Unknown';
  return d.toLocaleString('en-US',{timeZone:'UTC',month:'short',day:'numeric',year:'numeric',hour:'2-digit',minute:'2-digit',hourCycle:'h23'})+' UTC';
}
// Provider times look like "2027-03-11 06:00" (local airport time).
function legTime(value){
  const m=/^(\d{4})-(\d{2})-(\d{2})[ T](\d{2}:\d{2})/.exec(String(value||''));
  if(!m)return 'time unknown';
  const month=new Date(Date.UTC(+m[1],+m[2]-1,+m[3])).toLocaleString('en-US',{month:'short',day:'numeric',timeZone:'UTC'});
  return `${month} ${m[4]}`;
}
const hours=mins=>typeof mins==='number'&&mins>0?`${Math.round(mins/60*10)/10} h`:'Duration unknown';
const stopsLabel=n=>typeof n!=='number'?'Stops unknown':n===0?'Nonstop':`${n} stop${n===1?'':'s'}`;
const isLive=offer=>String(offer.data_status||'').startsWith('LIVE');
const isDemo=offer=>String(offer.data_status||'').includes('FICTIONAL');

/* ---------- price completeness ---------- */
// Prefer the backend's price_complete; when absent, treat fees_incomplete conservatively.
const offerComplete=offer=>typeof offer.price_complete==='boolean'?offer.price_complete:!offer.fees_incomplete;
function unknownFees(offer,isHotel,query){
  if(Array.isArray(offer.unknown_fee_categories))return offer.unknown_fee_categories;
  if(!offer.fees_incomplete)return [];
  const list=[];
  if(isHotel){
    list.push('Resort / mandatory fees');
  }else{
    if(query.carry_on&&offer.carry_on_included==null)list.push('Carry-on bag');
    if(query.checked_bag&&offer.checked_bag_included==null)list.push('Checked bag');
  }
  return list.length?list:['Fees not confirmed by provider'];
}
function bagStatus(included,fee,selected,incomplete){
  if(included===true)return 'Included';
  if(included==null&&incomplete)return 'Unknown';
  const amount=`${money(Number(fee)||0)} / traveler`;
  return selected?amount:`${amount} (not selected)`;
}

/* ---------- offer cards ---------- */
function statusTag(offer){
  if(isDemo(offer))return '<span class="tag fake">SYNTHETIC TEST PRICE</span>';
  if(isLive(offer))return '<span class="tag live">UNVERIFIED LIVE LISTING</span>';
  return `<span class="tag">${safe(offer.data_status||'Source status unknown')}</span>`;
}
function legsHtml(offer){
  if(!Array.isArray(offer.legs)||!offer.legs.length){
    return `<div class="facts"><span>Out ${safe(offer.depart_date||'date unknown')}</span><span>Return ${safe(offer.return_date||'date unknown')}</span></div>`;
  }
  return `<div class="legs">${offer.legs.map(leg=>`<div class="leg"><span class="leg-dir">${leg.direction==='return'?'Return':'Out'}</span><span class="leg-main"><strong>${safe(legTime(leg.depart_time))}</strong> ${safe(leg.from||'?')} → <strong>${safe(legTime(leg.arrive_time))}</strong> ${safe(leg.to||'?')}</span><span class="leg-sub">${safe(leg.carrier)}${leg.flight_numbers&&leg.flight_numbers.length?' · '+safe(leg.flight_numbers.join(', ')):''} · ${safe(stopsLabel(leg.stops))} · ${safe(hours(leg.duration_minutes))} · ${money(leg.price_per_adult_usd)} / adult</span></div>`).join('')}</div>`;
}
function offerHtml(offer,index,isHotel,query,marks=null){
  const complete=offerComplete(offer);
  const missing=complete?[]:unknownFees(offer,isHotel,query);
  const title=isHotel?offer.name:`${offer.origin} → ${offer.destination} · ${offer.carrier}`;
  const priceNote=isHotel
    ?(complete?'full stay':'known stay price')
    :`${complete?'total ·':'known fare ·'} ${query.travelers} traveler${query.travelers===1?'':'s'}`;
  let body;
  if(isHotel){
    const nights=offer.nights?` (${offer.nights} night${offer.nights===1?'':'s'})`:'';
    const occupancy=offer.max_occupancy
      ?`Up to ${offer.max_occupancy} guest(s)`
      :`Searched for ${offer.searched_adults||query.travelers} adult(s); room capacity not confirmed`;
    const refund=offer.refundable===true?'Refundable listed':offer.refundable===false?'Nonrefundable listed':'Cancellation terms unknown';
    body=`<div class="facts"><span>${safe(offer.checkin)} → ${safe(offer.checkout)}${safe(nights)}</span>${offer.property_type?`<span>${safe(offer.property_type)}</span>`:''}</div>
      <dl class="detail-list"><div><dt>Room</dt><dd>${safe(offer.room_type||'Room type unknown')}</dd></div><div><dt>Occupancy</dt><dd>${safe(occupancy)}</dd></div><div><dt>Cancellation</dt><dd>${safe(refund)}</dd></div>${offer.rate_basis?`<div><dt>Price basis</dt><dd>${safe(offer.rate_basis)}</dd></div>`:''}</dl>`;
  }else{
    const incomplete=Boolean(offer.fees_incomplete);
    body=`${legsHtml(offer)}
      <div class="facts"><span>${safe(stopsLabel(offer.stops))}</span><span>${safe(hours(offer.duration_minutes))} total</span></div>
      <dl class="detail-list"><div><dt>Carry-on</dt><dd>${safe(bagStatus(offer.carry_on_included,offer.carry_on_per_traveler_usd,query.carry_on,incomplete))}</dd></div><div><dt>Checked bag</dt><dd>${safe(bagStatus(offer.checked_bag_included,offer.checked_bag_per_traveler_usd,query.checked_bag,incomplete))}</dd></div><div><dt>Fare</dt><dd>${safe(offer.fare_label||'Fare not specified')}</dd></div>${offer.price_basis?`<div><dt>Price basis</dt><dd>${safe(offer.price_basis)}</dd></div>`:''}</dl>`;
  }
  const unknownBox=missing.length?`<div class="unknown-fees"><strong>Unknown, not included:</strong> ${safe(missing.join(', '))}. This is not an all-in price.</div>`:'';
  const award=offer.points_required > 0?`<div class="award">${offer.award_affordable?'Points scenario — availability unverified':'Not enough entered points'}: <strong>${offer.points_required.toLocaleString()} points + ${offer.award_price_complete === false?'unknown cash fees':money(offer.award_fees_usd)}</strong><br>Economic cost at your valuation: ${offer.award_price_complete === false?'Unknown':money(offer.award_economic_cost_usd)}</div>`:'';
  const observed=isDemo(offer)?'Synthetic fixture · no live observation':`Observed ${utcTime(offer.observed_utc)}`;
  const link=safeLink(offer.source_url,isHotel?'Listing link':'View search');
  const est=offer.points_estimate||null;
  const rankTags=marks
    ?`${marks.cheapest?'<span class="tag best">Lowest cash price</span>':''}${marks.fewestPoints?'<span class="tag points">Fewest points</span>':''}`
    :index===0?'<span class="tag best">Lowest known price</span>':'';
  const programTag=est?`<span class="tag program">${safe(est.programs.map(p=>p.short).join(' + '))} · ${safe(est.cards.map(c=>c.card_short).join(' + '))}</span>`
    :isLive(offer)?'<span class="tag no-points">No Chase/Amex points option</span>':'';
  return `<article class="offer ${index===0?'offer-best':''}" data-offer-id="${safe(offer.id)}">
    <div class="offer-top"><div>${marks?`<span class="rank">#${index+1}</span>`:''}<h4>${safe(title)}</h4><div class="sourceline">${safe(offer.source||'Source unknown')} ${link}</div></div><div class="cost">${money(offer.total_cash_usd)}<small>${safe(priceNote)}</small></div></div>
    <div class="tags">${statusTag(offer)}${rankTags}${programTag}<span class="tag">${safe(offer.id)}</span></div>
    ${body}${unknownBox}${award}${est?pointsEstimateHtml(est):''}
    <div class="offer-foot"><span>${safe(observed)}</span><span>${offer.checkout_verified?'Checkout verified':'Not checkout verified'}</span></div></article>`;
}

const fmtPts=n=>typeof n==='number'?n.toLocaleString('en-US'):'—';
function pointsEstimateHtml(est){
  const programs=est.programs.map(p=>`<p>≈ ${fmtPts(p.program_points)} ${safe(p.name)} points${est.programs.length>1?` (${safe(p.covers.join(' + '))})`:''}${p.via_partner?' <span class="tag partner">partner booking</span>':''}: ${money(p.cash_basis_usd)} ÷ ${safe(p.cents_per_point)}¢ per point</p>`).join('');
  const cards=est.cards.map(c=>`<li><span>${safe(c.card_name)} <small>${safe(c.ratios.join(', '))}</small></span><strong>${fmtPts(c.card_points)}</strong></li>`).join('');
  const notes=est.cards.flatMap(c=>c.notes.map(n=>`<p class="pe-note">${safe(c.card_short)} → ${safe(n)}.</p>`)).join('');
  return `<div class="points-estimate"><div class="pe-head"><strong>≈ ${fmtPts(est.lowest_card_points)} ${safe(est.lowest_cards.join(' or '))} points</strong><span class="tag est">ESTIMATE</span></div>
    ${programs}<ul>${cards}</ul>${notes}<p class="pe-source">Values: ${safeLink(est.valuation_url,est.valuation_source)||safe(est.valuation_source)}</p></div>`;
}

/* ---------- sorting flights and hotels (cash / points) ---------- */
const lists={flights:{sort:'cash',items:[],isHotel:false},hotels:{sort:'cash',items:[],isHotel:true}};
let currentQuery=null;
let currentMode='demo';
const byCash=(a,b)=>a.total_cash_usd-b.total_cash_usd;
function sortOffers(items,mode){
  const copy=[...items];
  if(mode!=='points')return copy.sort(byCash);
  // Fewest points regardless of card; offers with no points figure go last.
  return copy.sort((a,b)=>{
    const pa=a.points_sort_value,pb=b.points_sort_value;
    if(pa==null||pb==null)return pa==null&&pb==null?byCash(a,b):pa==null?1:-1;
    return pa-pb||byCash(a,b);
  });
}
function offerMarks(items){
  const cheapest=items.length?sortOffers(items,'cash')[0].id:null;
  const withPoints=items.filter(o=>o.points_sort_value!=null);
  const fewest=withPoints.length?sortOffers(withPoints,'points')[0].id:null;
  return id=>({cheapest:id===cheapest,fewestPoints:id===fewest});
}
const sortNote=(kind,mode)=>mode==='points'
  ?`Fewest card points first, whichever card (Chase or Amex) needs fewer. Live points are estimates; ${kind} without a points figure go last.`
  :'Cheapest cash price first.';
function renderList(kind,animate){
  const list=lists[kind];
  const container=el(kind);
  for(const button of document.querySelectorAll(`[data-list="${kind}"] [data-sort]`))button.setAttribute('aria-pressed',String(button.dataset.sort===list.sort));
  el(kind+'SortNote').textContent=list.items.length?sortNote(kind,list.sort):'';
  if(!list.items.length){container.innerHTML=currentQuery?emptyHtml(kind,currentMode):'';return;}
  const order=sortOffers(list.items,list.sort);
  const marks=offerMarks(list.items);
  const existing=new Map([...container.querySelectorAll('[data-offer-id]')].map(node=>[node.dataset.offerId,node]));
  if(!animate||existing.size!==order.length||!order.every(o=>existing.has(o.id))){
    container.innerHTML=order.map((o,i)=>offerHtml(o,i,list.isHotel,currentQuery,marks(o.id))).join('');
    return;
  }
  // FLIP: remember where each card was, move it in the DOM, then animate from old to new position.
  const before=new Map([...existing].map(([id,node])=>[id,node.getBoundingClientRect().top]));
  const oldRank=new Map([...existing.keys()].map((id,i)=>[id,i]));
  order.forEach(o=>container.appendChild(existing.get(o.id)));
  const reduceMotion=typeof matchMedia==='function'&&matchMedia('(prefers-reduced-motion: reduce)').matches;
  order.forEach((o,i)=>{
    const node=existing.get(o.id);
    node.classList.toggle('offer-best',i===0);
    const rank=node.querySelector('.rank');if(rank)rank.textContent=`#${i+1}`;
    node.classList.remove('moved-up','moved-down');
    const delta=before.get(o.id)-node.getBoundingClientRect().top;
    if(!delta||reduceMotion)return;
    node.style.transition='none';
    node.style.transform=`translateY(${delta}px)`;
    if(i<oldRank.get(o.id))node.classList.add('moved-up');else if(i>oldRank.get(o.id))node.classList.add('moved-down');
  });
  void container.offsetHeight;
  for(const node of existing.values()){
    if(!node.style.transform)continue;
    node.style.transition='transform 500ms cubic-bezier(.2,.8,.2,1)';
    node.style.transform='';
    node.addEventListener('transitionend',()=>{node.style.transition='';},{once:true});
  }
}
for(const button of document.querySelectorAll('[data-list] [data-sort]')){
  button.addEventListener('click',()=>{
    const kind=button.closest('[data-list]').dataset.list;
    if(button.dataset.sort===lists[kind].sort)return;
    lists[kind].sort=button.dataset.sort;
    renderList(kind,true);
  });
}

/* ---------- summary ---------- */
function sourceBadge(list,mode){
  if(mode==='demo')return '<span class="source-badge demo">Fictional demo</span>';
  return list.length?'<span class="source-badge live">Live listings · unverified</span>':'<span class="source-badge none">No live results</span>';
}
function emptyHtml(kind,mode){
  return mode==='demo'
    ?`<div class="empty">No matching ${kind}. Demo fixtures only cover the three sample trips; try a sample or switch to Live mode.</div>`
    :`<div class="empty">No priced live ${kind} for this search. See the warnings above for the reason. Demo prices are never substituted in Live mode.</div>`;
}

function render(data){
  const mode=data.query.mode;
  el('modeBanner').className=`mode-banner ${mode}`;
  el('modeBanner').innerHTML=mode==='demo'
    ?'<strong>DEMO MODE</strong> · Every price below is fictional test data and cannot be booked.'
    :'<strong>LIVE MODE</strong> · Search-listing estimates from SerpApi. Not checkout verified; fees may be missing.';
  el('warnings').innerHTML=(data.warnings||[]).map((w,i)=>`<div class="warn">${i===0?'<strong>Important:</strong> ':''}${safe(w)}</div>`).join('');
  el('flightCount').innerHTML=`${data.flights.length} result(s) ${sourceBadge(data.flights,mode)}`;
  el('hotelCount').innerHTML=`${data.hotels.length} result(s) ${sourceBadge(data.hotels,mode)}`;
  currentQuery=data.query;currentMode=mode;
  lists.flights.items=data.flights;lists.hotels.items=data.hotels;
  renderList('flights',false);renderList('hotels',false);
  const summary=data.summary;
  const hasTrip=typeof summary.modeled_trip_cash_usd==='number';
  const hasKnown=typeof summary.known_trip_cash_usd==='number';
  const a=summary.comparison_illustrative_award || summary.best_illustrative_award;
  const savings=a?Number(a.economic_savings_usd):null;
  const verdict=a?(savings>0?`Points offer better modeled value by ${money(savings)}.`:savings<0?`Cash offers better modeled value by ${money(-savings)}.`:'Cash and points have equal modeled value.'):'No eligible points scenario to compare.';
  const unavailable=!hasTrip?'A complete trip price is needed before comparing points.':'No affordable points option with complete fee information was returned.';
  const comparison=`<div class="payment-comparison"><div><small>PAY CASH</small><strong>${hasTrip?money(summary.modeled_trip_cash_usd):hasKnown?money(summary.known_trip_cash_usd):'Not available'}</strong><p>${hasTrip?'Flight + hotel cash outlay':hasKnown?'Known estimate — required fees unknown':'Flight or hotel results missing'}</p></div><div><small>ONE AWARD + CASH · SCENARIO ONLY</small><strong>${a?money(a.trip_cash_outlay_usd):'Not available'}</strong><p>${a?`Plus ${Number(a.points).toLocaleString()} points<br>Value of points used: ${money(Number(a.points)*data.query.point_value_cents/100)}<br>Total economic cost: <b>${money(a.trip_economic_cost_usd)}</b><br>${safe(a.kind)} award: ${safe(a.offer_id)}`:safe(unavailable)}</p></div></div><p><strong>${safe(verdict)}</strong></p>${a?'<p>Economic cost = cash paid + your value of points used. Availability and program eligibility are unverified.</p>':''}`;
  el('recommendations').innerHTML=`<div class="reco-box"><h3>Your cash-versus-points comparison</h3>${comparison}${summary.recommendations.map(s=>`<p>${safe(s)}</p>`).join('') || '<p>No recommendation available. Try another search.</p>'}<p><strong>Before booking:</strong> Verify exact flights, room conditions, required fees, and award availability with the provider.</p></div>`;
}
function clearResults(){
  el('modeBanner').className='mode-banner';el('modeBanner').innerHTML='';
  for(const id of ['flights','hotels','recommendations','flightCount','hotelCount'])el(id).innerHTML='';
  currentQuery=null;lists.flights.items=[];lists.hotels.items=[];
  el('flightsSortNote').textContent='';el('hotelsSortNote').textContent='';
}
async function doSearch(){
  const version=++searchVersion;
  const button=el('searchButton');button.disabled=true;
  el('results').setAttribute('aria-busy','true');
  clearResults();el('warnings').innerHTML='';
  el('status').textContent='Searching and comparing. Live API calls may take longer…';
  try{
    const response=await fetch('/api/search',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(getRequest())});
    const payload=await response.json();
    if(version!==searchVersion)return;
    if(!response.ok)throw new Error(payload.error||'Search failed');
    render(payload);
    el('status').textContent=`Search complete • ${payload.query.mode==='demo'?'fictional data':'preliminary live listing estimates'} • prices in USD`;
  }catch(error){
    if(version!==searchVersion)return;
    el('status').textContent='Error: '+error.message;
    el('warnings').innerHTML='<div class="warn">Check your inputs or live API configuration. See README.md.</div>';
    clearResults();
  }finally{if(version===searchVersion){button.disabled=false;el('results').setAttribute('aria-busy','false');}}
}
doSearch();
