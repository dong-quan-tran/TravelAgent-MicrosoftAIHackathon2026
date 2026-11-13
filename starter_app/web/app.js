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
function offerHtml(offer,index,isHotel,mode){
  const title=isHotel?offer.name:`${offer.origin} → ${offer.destination} · ${offer.carrier}`;
  const details=isHotel?`${offer.room_type || 'Room type unknown'}`:
    `${offer.stops === 0?'Nonstop':`${offer.stops} stop(s)`} · ${offer.duration_minutes?Math.round(offer.duration_minutes/60*10)/10+' h':'Duration unknown'}`;
  const meta=isHotel?`Room: ${safe(offer.refundable===true?'Refundable listed':offer.refundable===false?'Nonrefundable listed':'Refundability unknown')}`:
    `${safe(offer.fare_label||'Fare not specified')}`;
  const award=offer.points_required > 0?`<div class="award">${offer.award_affordable?'Potential demo redemption':'Not enough entered demo points'}: <strong>${offer.points_required.toLocaleString()} points + ${money(offer.award_fees_usd)}</strong><br>Economic cost at your custom valuation: ${money(offer.award_economic_cost_usd)}</div>`:'';
  const timeLabel=offer.observed_utc?`Observed: ${safe(offer.observed_utc)}`:"Synthetic fixture • no live observation";
  const completeness=offer.fees_incomplete?'Further fees may apply; NOT an all-in total':
    `Estimated rewards on cash purchase: ${Number(offer.reward_points_earned||0).toLocaleString()} points`;
  return `<article class="offer ${index===0?'offer-best':''}"><div class="offer-top"><div><h4>${safe(title)}</h4><div class="sourceline">${safe(offer.source)}</div></div><div class="cost">${money(offer.total_cash_usd)}<small>${isHotel?'full stay':'all travelers'}</small></div></div><div class="tags"><span class="tag fake">${mode==='demo'?'SYNTHETIC TEST PRICE':'UNVERIFIED LIVE SEARCH'}</span><span class="tag">${safe(details)}</span><span class="tag">${safe(offer.id)}</span></div><div class="sourceline">${meta}</div>${award}<div class="offer-foot"><span>${safe(completeness)}</span><span>${safe(timeLabel)} · ${offer.checkout_verified?'Checkout verified':'Not checkout verified'}</span></div></article>`;
}
function render(data){
  const mode=data.query.mode;
  el('warnings').innerHTML=(data.warnings||[]).map((w,i)=>`<div class="warn">${i===0?'<strong>Important:</strong> ':''}${safe(w)}</div>`).join('');
  const summary=data.summary;
  const hasTrip=typeof summary.modeled_trip_cash_usd==='number';
  el('summary').innerHTML=`<div class="trip-summary"><div><small>${mode==='demo'?'FICTIONAL TEST TOTAL':'PRELIMINARY SEARCH ESTIMATE'}</small><strong>${hasTrip?money(summary.modeled_trip_cash_usd):'Incomplete trip'}</strong><p>${hasTrip?'Lowest modeled cash flight + hotel • USD':'One or both parts of the trip are missing'}</p></div><div class="summary-note"><small>ILLUSTRATIVE CARD REWARDS</small><strong>${Number(summary.modeled_points_earned_if_cash||0).toLocaleString()} pts</strong><p>At ${safe(data.query.card_multiplier)} points / $1 on eligible spending; actual card rules vary.</p></div></div>`;
  el('flightCount').textContent=`${data.flights.length} result(s)`;
  el('hotelCount').textContent=`${data.hotels.length} result(s)`;
  el('flights').innerHTML=data.flights.length?data.flights.map((o,i)=>offerHtml(o,i,false,mode)).join(''):'<div class="empty">No matching flights. Demo fixtures cover the three scenario buttons; try a sample or connect live search.</div>';
  el('hotels').innerHTML=data.hotels.length?data.hotels.map((o,i)=>offerHtml(o,i,true,mode)).join(''):'<div class="empty">No matching hotels. Demo fixtures cover the three scenario buttons; try a sample or connect live search.</div>';
  el('recommendations').innerHTML=`<div class="reco-box"><h3>Agent-style recommendations</h3>${summary.recommendations.map(s=>`<p>${safe(s)}</p>`).join('') || '<p>No recommendation available. Improve source coverage and rerun.</p>'}<p><strong>Next step:</strong> Students must improve verification and use actual accessible providers. These are not bookable results.</p></div>`;
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
    el('summary').innerHTML='';el('flights').innerHTML='';el('hotels').innerHTML='';el('recommendations').innerHTML='';
  }finally{button.disabled=false;}
}
doSearch();
