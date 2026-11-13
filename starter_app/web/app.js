/* FareForge student app. NEVER present fictional demo data as live travel offers. */
const el = id => document.getElementById(id);
const money = v => typeof v === 'number' && Number.isFinite(v)
  ? new Intl.NumberFormat('en-US', {style:'currency',currency:'USD'}).format(v) : 'Not available';
const safe = value => String(value ?? '').replace(/[&<>"']/g, m => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[m]));
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
function offerHtml(offer,index,isHotel,query){
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
  const award=offer.points_required > 0?`<div class="award">${offer.award_affordable?'Potential demo redemption':'Not enough entered demo points'}: <strong>${offer.points_required.toLocaleString()} points + ${money(offer.award_fees_usd)}</strong><br>Economic cost at your custom valuation: ${money(offer.award_economic_cost_usd)}</div>`:'';
  const observed=isDemo(offer)?'Synthetic fixture · no live observation':`Observed ${utcTime(offer.observed_utc)}`;
  const link=safeLink(offer.source_url,isHotel?'Listing link':'View search');
  return `<article class="offer ${index===0?'offer-best':''}">
    <div class="offer-top"><div><h4>${safe(title)}</h4><div class="sourceline">${safe(offer.source||'Source unknown')} ${link}</div></div><div class="cost">${money(offer.total_cash_usd)}<small>${safe(priceNote)}</small></div></div>
    <div class="tags">${statusTag(offer)}${index===0?'<span class="tag best">Lowest known price</span>':''}<span class="tag">${safe(offer.id)}</span></div>
    ${body}${unknownBox}${award}
    <div class="offer-foot"><span>${safe(observed)}</span><span>${offer.checkout_verified?'Checkout verified':'Not checkout verified'}</span></div></article>`;
}

/* ---------- summary ---------- */
function summaryHtml(data){
  const {summary,query,flights,hotels}=data;
  const flight=flights.find(f=>f.id===summary.flight_offer_id)||null;
  const hotel=hotels.find(h=>h.id===summary.hotel_offer_id)||null;
  const bothParts=Boolean(flight&&hotel);
  const complete=typeof summary.price_complete==='boolean'?summary.price_complete:bothParts&&offerComplete(flight)&&offerComplete(hotel);
  const known=typeof summary.known_trip_cash_usd==='number'?summary.known_trip_cash_usd
    :bothParts?Math.round((flight.total_cash_usd+hotel.total_cash_usd)*100)/100:null;
  const modeLabel=query.mode==='demo'?'FICTIONAL TEST TOTAL':'PRELIMINARY LIVE SEARCH ESTIMATE';
  let headline,detail;
  if(!bothParts){
    const missingPart=!flight&&!hotel?'No flight or hotel result':!flight?'No flight result':'No hotel result';
    headline='Incomplete trip';
    detail=`${missingPart}, so there is no trip total.`;
  }else if(complete){
    headline=money(typeof summary.modeled_trip_cash_usd==='number'?summary.modeled_trip_cash_usd:known);
    detail='Lowest modeled cash flight + hotel · USD';
  }else{
    const missing=[...new Set([...unknownFees(flight,false,query),...unknownFees(hotel,true,query)])];
    headline=`${money(known)} <span class="known-tag">known so far</span>`;
    detail=`Not an all-in total. Unknown: ${safe(missing.join(', '))}.`;
  }
  return `<div class="trip-summary"><div><small>${modeLabel}</small><strong>${headline}</strong><p>${detail}</p></div><div class="summary-note"><small>ILLUSTRATIVE CARD REWARDS</small><strong>${Number(summary.modeled_points_earned_if_cash||0).toLocaleString()} pts</strong><p>At ${safe(query.card_multiplier)} points / $1 on eligible spending; actual card rules vary.</p></div></div>`;
}
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
  el('summary').innerHTML=summaryHtml(data);
  el('flightCount').innerHTML=`${data.flights.length} result(s) ${sourceBadge(data.flights,mode)}`;
  el('hotelCount').innerHTML=`${data.hotels.length} result(s) ${sourceBadge(data.hotels,mode)}`;
  el('flights').innerHTML=data.flights.length?data.flights.map((o,i)=>offerHtml(o,i,false,data.query)).join(''):emptyHtml('flights',mode);
  el('hotels').innerHTML=data.hotels.length?data.hotels.map((o,i)=>offerHtml(o,i,true,data.query)).join(''):emptyHtml('hotels',mode);
  const summary=data.summary;
  el('recommendations').innerHTML=`<div class="reco-box"><h3>Agent-style recommendations</h3>${summary.recommendations.map(s=>`<p>${safe(s)}</p>`).join('') || '<p>No recommendation available. Improve source coverage and rerun.</p>'}<p><strong>Next step:</strong> Verify every price directly with the airline or hotel before booking. These are not bookable results.</p></div>`;
}
function clearResults(){
  el('modeBanner').className='mode-banner';el('modeBanner').innerHTML='';
  for(const id of ['summary','flights','hotels','recommendations','flightCount','hotelCount'])el(id).innerHTML='';
}
async function doSearch(){
  const button=el('searchButton');button.disabled=true;
  el('status').textContent='Searching and comparing. Live API calls may take longer…';
  try{
    const response=await fetch('/api/search',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(getRequest())});
    const payload=await response.json();
    if(!response.ok)throw new Error(payload.error||'Search failed');
    render(payload);
    el('status').textContent=`Search complete • ${payload.query.mode==='demo'?'fictional data':'preliminary live listing estimates'} • prices in USD`;
  }catch(error){
    el('status').textContent='Error: '+error.message;
    el('warnings').innerHTML='<div class="warn">Check your inputs or live API configuration. See README.md.</div>';
    clearResults();
  }finally{button.disabled=false;}
}
doSearch();
