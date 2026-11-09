/* EDIT HERE: change a service's status independently of its text. status: now | spec | planned */
const STATUS={now:"Available now",spec:"Through an identified specialist",planned:"Planned"};
const SERVICES=[
{t:"Agribusiness planning & access to finance",s:"now",d:"Business plans, feasibility assessments, cash-flow models and investment proposals, and preparation for lender or investor discussions. We support applications; we do not guarantee funding."},
{t:"Sustainable farming & farmer development",s:"now",d:"Farm planning, agroforestry, poultry, beekeeping and farmer training, where delivery capacity is confirmed. Organic-readiness and records support only; we do not issue certificates."},
{t:"Market access & enterprise development",s:"now",d:"Value-chain analysis, aggregation planning, buyer engagement and business formalisation support, with qualified professionals identified for legal work."},
{t:"Business intelligence & digital systems",s:"now",d:"Data-collection design, analysis and management dashboards. Farmer identification and traceability are development areas."},
{t:"Environmental greening & landscaping",s:"spec",d:"Advisory support for greening and landscaping plans. Our role is consultancy unless a different arrangement is documented."},
{t:"Climate projects & specialist coordination",s:"planned",d:"Scoping and coordination of climate opportunities such as solar, mobility and monitoring. Development area only: no accreditation, credit issuance or drone operations are claimed."},
{t:"SmartHasibu bookkeeping",s:"planned",d:"Our planned phone-based bookkeeping product for farmers and small enterprises."}];
const PROJECTS=[
{t:"VOFA advisory work",s:"concept",o:"Vihiga Organic Farmers Association (separate organisation)",r:"Proposed agribusiness consulting and technical coordination, subject to a written engagement. Prospective client; not yet contracted."},
{t:"Agroforestry & poultry (VOFA Phase I)",s:"concept",o:"VOFA’s programme",r:"Part of VOFA’s proposed plan. Not a completed MoFirms project."},
{t:"Integrated Vihiga concept",s:"concept",o:"To be confirmed",r:"Digital agriculture, clean mobility, solar access and monitoring. A future programme concept until a funded scope is confirmed."},
{t:"Digital platform & carbon",s:"concept",o:"VOFA concept",r:"Farmer onboarding and monitoring ideas. Not live; no carbon credits have been issued."}];
const VOFA_CLUSTERS=[
{t:"Beekeeping & small livestock",activities:["Organic honey","Improved indigenous poultry under semi-free-range management","Rabbits","Pigs"]},
{t:"Orchards & tree crops",activities:["Apples, Hass and Fuerte avocado, mango, macadamia, and guava","Oil palm, including crude-oil processing","Vanilla intercropped with banana"]},
{t:"Oilseeds & protein crops",activities:["Sunflower for oil and press cake","Soya","Simsim (sesame)","Groundnuts","Sacha inchi"]},
{t:"Roots, vegetables, herbs & mushrooms",activities:["Sweet potatoes, including orange-fleshed varieties","Indigenous vegetables such as managu, saga, and terere","White ginger (Omukombero)","Mushrooms"]},
{t:"Fish farming",activities:["Pond aquaculture using locally formulated feed"]}];
const FEATS=["Record farm sales and operating costs","Separate books for crops, livestock, and other activities","Track unpaid customer sales and supplier costs","Record partial or full credit repayments","Review monthly income, costs, and outstanding balances"];
const PORTALS=[["Portal A: Farmer registration","Securely capture farmer and group registrations for MoFirms staff review. Identity and farm evidence are reviewed manually; uploads are private and time-limited.","/portal/register/"],["Portal B: Supplier & buyer registration","Register suppliers, produce buyers, and professional service providers. Choose multiple roles and submit an optional business profile for MoFirms review.","/portal/partners/register/"],["Portal C: Financial analysis","Request specialist-reviewed financial statements, cash-flow analysis, business plans, budgeting, and funding readiness. Staff review the scope and send a fee quote before work begins.","/portal/financial-analysis/"],["Portal D: Risk & opportunity","Request a human-led, specialist-prepared assessment of enterprise risks, resilience, and growth opportunities. Staff review the scope and issue a fee quote before work begins.","/portal/risk-assessment/"],["Portal E: Research questionnaires","Research organisations, universities, marketing companies, and students can apply for manual vetting and submit studies for review. Respondents opt in separately; researchers receive aggregate results only.","/portal/research/register/"]];
const PATHS={Farmer:["Farmers & farmer groups","Register an individual farmer or group, share farming and business needs, and request a MoFirms review.","/portal/register/"],Entrepreneur:["Entrepreneurs","Business planning, cash-flow modelling and finance readiness for your venture.","#services"],Institution:["Institutions & partners","Project design, analysis and partnership enquiries, with clear roles and ownership.","#projects"]};
const CATS=["Agribusiness advice","Business intelligence","Training","Products","Project collaboration","SmartHasibu waitlist","Other"];
const $=s=>document.querySelector(s),el=(h)=>{const d=document.createElement("div");d.innerHTML=h.trim();return d.firstChild};
const reducedMotion=window.matchMedia("(prefers-reduced-motion: reduce)");
$("#yr").textContent=new Date().getFullYear();
const menu=$("#menu"),burger=$("#burger");
function closeMenu(restoreFocus=false){
  menu.classList.remove("open");
  burger.setAttribute("aria-expanded","false");
  burger.setAttribute("aria-label","Open menu");
  burger.textContent="☰";
  if(restoreFocus)burger.focus();
}
burger.onclick=()=>{
  const open=!menu.classList.contains("open");
  menu.classList.toggle("open",open);
  burger.setAttribute("aria-expanded",String(open));
  burger.setAttribute("aria-label",open?"Close menu":"Open menu");
  burger.textContent=open?"×":"☰";
};
menu.addEventListener("click",event=>{if(event.target.closest("a"))closeMenu()});
document.addEventListener("keydown",event=>{if(event.key==="Escape"&&menu.classList.contains("open"))closeMenu(true)});
window.addEventListener("resize",()=>{if(window.innerWidth>760)closeMenu()});
$("#pv").onclick=()=>{const notice=$("#privacy");notice.hidden=!notice.hidden;$("#pv").setAttribute("aria-expanded",String(!notice.hidden))};
/* agriculture story carousel */
const carousel=$("#agriCarousel");
if(carousel){
  const slides=[...carousel.querySelectorAll(".carousel-slide")];
  const announcement=$("#carouselAnnouncement");
  const currentDisplay=$("#carouselCurrent");
  const totalDisplay=$("#carouselTotal");
  const progress=carousel.querySelector(".carousel-progress");
  const progressFill=$("#carouselProgress");
  const toggle=$("#carouselToggle");
  let currentSlide=0;
  let carouselPaused=true;
  let carouselEngaged=false;
  let carouselTimer;
  totalDisplay.textContent=String(slides.length).padStart(2,"0");
  progress.setAttribute("aria-valuemax",String(slides.length));
  function updateCarouselToggle(){
    toggle.disabled=reducedMotion.matches;
    toggle.textContent=carouselPaused?"▶":"Ⅱ";
    toggle.setAttribute("aria-label",reducedMotion.matches?"Automatic slide rotation is disabled by your reduced motion setting":carouselPaused?"Start automatic slide rotation":"Pause automatic slide rotation");
  }
  function scheduleCarouselAdvance(){
    window.clearTimeout(carouselTimer);
    if(carouselPaused||carouselEngaged||document.hidden||reducedMotion.matches)return;
    carouselTimer=window.setTimeout(()=>{
      showSlide(currentSlide+1);
      scheduleCarouselAdvance();
    },7000);
  }
  function showSlide(index,announce=false){
    currentSlide=(index+slides.length)%slides.length;
    slides.forEach((slide,i)=>{
      const active=i===currentSlide;
      slide.hidden=!active;
      slide.classList.toggle("is-active",active);
      slide.setAttribute("aria-label",`${i+1} of ${slides.length}: ${slide.querySelector("h1,h2").textContent}`);
    });
    currentDisplay.textContent=String(currentSlide+1).padStart(2,"0");
    progress.setAttribute("aria-valuenow",String(currentSlide+1));
    progressFill.style.width=`${((currentSlide+1)/slides.length)*100}%`;
    if(announce)announcement.textContent=`Slide ${currentSlide+1} of ${slides.length}: ${slides[currentSlide].querySelector("h1,h2").textContent}`;
    scheduleCarouselAdvance();
  }
  function setCarouselEngaged(engaged){
    carouselEngaged=engaged||carousel.matches(":hover")||carousel.contains(document.activeElement);
    scheduleCarouselAdvance();
  }
  $("#carouselPrevious").onclick=()=>showSlide(currentSlide-1,true);
  $("#carouselNext").onclick=()=>showSlide(currentSlide+1,true);
  toggle.onclick=()=>{carouselPaused=!carouselPaused;updateCarouselToggle();scheduleCarouselAdvance()};
  carousel.addEventListener("pointerenter",()=>setCarouselEngaged(true));
  carousel.addEventListener("pointerleave",()=>setCarouselEngaged(false));
  carousel.addEventListener("focusin",()=>setCarouselEngaged(true));
  carousel.addEventListener("focusout",event=>{if(!carousel.contains(event.relatedTarget))setCarouselEngaged(false)});
  let touchStart=null;
  carousel.addEventListener("pointerdown",event=>{
    if(event.pointerType==="touch")touchStart={x:event.clientX,y:event.clientY};
  });
  carousel.addEventListener("pointerup",event=>{
    if(!touchStart)return;
    const deltaX=event.clientX-touchStart.x;
    const deltaY=event.clientY-touchStart.y;
    if(Math.abs(deltaX)>50&&Math.abs(deltaX)>Math.abs(deltaY)){
      showSlide(currentSlide+(deltaX<0?1:-1),true);
    }
    touchStart=null;
  });
  carousel.addEventListener("pointercancel",()=>{touchStart=null});
  carousel.addEventListener("keydown",event=>{
    if(event.key==="ArrowLeft"||event.key==="ArrowRight"){
      event.preventDefault();
      showSlide(currentSlide+(event.key==="ArrowRight"?1:-1),true);
    }
  });
  reducedMotion.addEventListener("change",()=>{
    if(reducedMotion.matches)carouselPaused=true;
    updateCarouselToggle();
    scheduleCarouselAdvance();
  });
  document.addEventListener("visibilitychange",scheduleCarouselAdvance);
  updateCarouselToggle();
  showSlide(0);
}
/* pathways */
const tabs=$("#tabs");Object.keys(PATHS).forEach((k,i)=>{const b=el(`<button role="tab" aria-selected="${i==0}">${PATHS[k][0]}</button>`);b.onclick=()=>{tabs.querySelectorAll("button").forEach(x=>x.setAttribute("aria-selected","false"));b.setAttribute("aria-selected","true");show(k)};tabs.append(b)});
function show(k){const p=PATHS[k];$("#pathOut").innerHTML=`<h3>${p[0]}</h3><p>${p[1]}</p><a class="btn sm" href="${p[2]}">Continue</a>`}show("Farmer");
/* services */
let flt="all";const F=$("#filters");
[["all","All"],...Object.entries(STATUS)].forEach(([k,v])=>{const b=el(`<button type="button" class="${k=="all"?"on":""}" aria-pressed="${k=="all"}">${v}</button>`);b.onclick=()=>{flt=k;F.querySelectorAll("button").forEach(x=>{x.classList.remove("on");x.setAttribute("aria-pressed","false")});b.classList.add("on");b.setAttribute("aria-pressed","true");draw()};F.append(b)});
const serviceViewport=$("#servicesViewport"),serviceSet=$("#serviceSet");
function draw(){
  const visibleServices=SERVICES.filter(s=>flt=="all"||s.s==flt);
  const cards=visibleServices.map(s=>`<article class="service-card"><span class="tag ${s.s}">${STATUS[s.s]}</span><h3>${s.t}</h3><p>${s.d}</p><a href="#contact">Enquire →</a></article>`).join("");
  serviceSet.innerHTML=cards;
  serviceViewport.scrollLeft=0;
}
$("#servicesPrevious").onclick=()=>serviceViewport.scrollBy({left:-serviceViewport.clientWidth*.8,behavior:reducedMotion.matches?"auto":"smooth"});
$("#servicesNext").onclick=()=>serviceViewport.scrollBy({left:serviceViewport.clientWidth*.8,behavior:reducedMotion.matches?"auto":"smooth"});
draw();
$("#projGrid").innerHTML=PROJECTS.map(p=>`<article class="card project-card"><span class="tag concept">Concept</span><h3>${p.t}</h3><p><b>Owner:</b> ${p.o}</p><p><b>MoFirms’ role:</b> ${p.r}</p><a class="project-link" href="#contact" data-cat="Project collaboration">Discuss a similar project <span aria-hidden="true">→</span></a></article>`).join("");
const clusterCards=VOFA_CLUSTERS.map(cluster=>`<article class="card project-card cluster-card"><span class="tag concept">Proposed · not approved or funded</span><h4>${cluster.t}</h4><ul aria-label="Activities under consideration">${cluster.activities.map(activity=>`<li>${activity}</li>`).join("")}</ul><a class="project-link" href="#contact" data-cat="Project collaboration">Discuss a similar project <span aria-hidden="true">→</span></a></article>`).join("");
const clusterViewport=$("#clustersViewport"),clusterSet=$("#clusterGrid");
clusterSet.innerHTML=clusterCards;
$("#clustersPrevious").onclick=()=>clusterViewport.scrollBy({left:-clusterViewport.clientWidth*.8,behavior:reducedMotion.matches?"auto":"smooth"});
$("#clustersNext").onclick=()=>clusterViewport.scrollBy({left:clusterViewport.clientWidth*.8,behavior:reducedMotion.matches?"auto":"smooth"});
$("#feat").innerHTML=FEATS.map(f=>`<li>${f}</li>`).join("");
const PORTAL_ACTIONS=["Register as a farmer","Register as a partner","Request financial analysis","Request an assessment","Apply as a researcher"];
const portalCards=PORTALS.map((p,i)=>`<li><h3>${p[0]}</h3><p>${p[1]}</p><a class="btn sm" href="${p[2]}">${PORTAL_ACTIONS[i]}</a></li>`).join("");
const portalViewport=$("#portalsViewport"),portalSet=$("#portals");
portalSet.innerHTML=portalCards;
$("#portalsPrevious").onclick=()=>portalViewport.scrollBy({left:-portalViewport.clientWidth*.8,behavior:reducedMotion.matches?"auto":"smooth"});
$("#portalsNext").onclick=()=>portalViewport.scrollBy({left:portalViewport.clientWidth*.8,behavior:reducedMotion.matches?"auto":"smooth"});
document.querySelectorAll("[data-cat]").forEach(a=>a.addEventListener("click",()=>{const option=[...$("#cat").options].find(item=>item.textContent===a.dataset.cat);if(option)$("#cat").value=option.value}));
/* change calculator */
const calc=()=>{const c=(+$("#paid").value||0)-(+$("#amt").value||0);$("#chg").textContent=c<0?"Customer owes KSh "+(-c).toLocaleString():"Change: KSh "+c.toLocaleString()};
$("#amt").oninput=$("#paid").oninput=calc;
/* readiness check */
const Q=[["Do you keep written records of sales and expenses?","records"],["Do you know who your main buyers are?","buyers"],["Do you have a written business plan?","plan"],["Have you worked out your cash-flow for the next 12 months?","cash"],["Do you know the main risks to your enterprise?","risk"]];
const TIPS={records:"Start simple bookkeeping. SmartHasibu is planned for this.",buyers:"Map buyers and test market access.",plan:"A structured business plan would help most.",cash:"A cash-flow model helps you prepare for financing.",risk:"A risk and opportunity review would clarify priorities."};
let qi=0,gaps=[];const qz=$("#quiz");
function ask(){if(qi>=Q.length){const sc=Q.length-gaps.length;qz.innerHTML=`<h3>${sc} of ${Q.length} in place</h3><div class="bar2"><i style="width:${sc/Q.length*100}%"></i></div>${gaps.length?"<ul>"+gaps.map(g=>`<li>${TIPS[g]}</li>`).join("")+"</ul>":"<p>You’re well prepared. We can help you grow further.</p>"}<p class="note">An indication only, not an assessment.</p><a class="btn sm" href="#contact">Talk to us</a> <button class="opt" id="rs">Restart</button>`;$("#rs").onclick=()=>{qi=0;gaps=[];ask()};return}
qz.innerHTML=`<p class="note">Question ${qi+1} of ${Q.length}</p><h3>${Q[qi][0]}</h3><button class="opt" data-a="1">Yes</button> <button class="opt" data-a="0">Not yet</button>`;
qz.querySelectorAll("button").forEach(b=>b.onclick=()=>{if(b.dataset.a=="0")gaps.push(Q[qi][1]);qi++;ask()})}ask();
