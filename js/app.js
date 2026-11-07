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
$("#burger").onclick=e=>{const o=$("#menu").classList.toggle("open");e.target.setAttribute("aria-expanded",o)};
$("#menu").onclick=()=>$("#menu").classList.remove("open");
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
  let carouselPaused=reducedMotion.matches;
  let carouselEngaged=false;
  let lastCarouselChange=Date.now();
  totalDisplay.textContent=String(slides.length).padStart(2,"0");
  progress.setAttribute("aria-valuemax",String(slides.length));
  function updateCarouselToggle(){
    toggle.disabled=reducedMotion.matches;
    toggle.textContent=carouselPaused?"▶":"Ⅱ";
    toggle.setAttribute("aria-label",reducedMotion.matches?"Automatic slide rotation is disabled by your reduced motion setting":carouselPaused?"Resume automatic slide rotation":"Pause automatic slide rotation");
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
    lastCarouselChange=Date.now();
    if(announce)announcement.textContent=`Slide ${currentSlide+1} of ${slides.length}: ${slides[currentSlide].querySelector("h1,h2").textContent}`;
  }
  function setCarouselEngaged(engaged){
    carouselEngaged=engaged;
    lastCarouselChange=Date.now();
  }
  $("#carouselPrevious").onclick=()=>showSlide(currentSlide-1,true);
  $("#carouselNext").onclick=()=>showSlide(currentSlide+1,true);
  toggle.onclick=()=>{carouselPaused=!carouselPaused;updateCarouselToggle();lastCarouselChange=Date.now()};
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
  });
  window.setInterval(()=>{
    if(!carouselPaused&&!carouselEngaged&&!document.hidden&&Date.now()-lastCarouselChange>=7000){
      showSlide(currentSlide+1);
    }
  },500);
  updateCarouselToggle();
  showSlide(0);
}
/* pathways */
const tabs=$("#tabs");Object.keys(PATHS).forEach((k,i)=>{const b=el(`<button role="tab" aria-selected="${i==0}">${PATHS[k][0]}</button>`);b.onclick=()=>{tabs.querySelectorAll("button").forEach(x=>x.setAttribute("aria-selected","false"));b.setAttribute("aria-selected","true");show(k)};tabs.append(b)});
function show(k){const p=PATHS[k];$("#pathOut").innerHTML=`<h3>${p[0]}</h3><p>${p[1]}</p><a class="btn sm" href="${p[2]}">Continue</a>`}show("Farmer");
/* services */
let flt="all";const F=$("#filters");
[["all","All"],...Object.entries(STATUS)].forEach(([k,v])=>{const b=el(`<button type="button" class="${k=="all"?"on":""}" aria-pressed="${k=="all"}">${v}</button>`);b.onclick=()=>{flt=k;F.querySelectorAll("button").forEach(x=>{x.classList.remove("on");x.setAttribute("aria-pressed","false")});b.classList.add("on");b.setAttribute("aria-pressed","true");draw()};F.append(b)});
const serviceViewport=$("#servicesViewport"),serviceSet=$("#serviceSet"),serviceSetCopy=$("#serviceSetCopy"),servicesMotion=$("#servicesMotion"),servicesAnnouncement=$("#servicesAnnouncement");
let servicesPaused=reducedMotion.matches,servicesEngaged=false,lastServicesFrame=0;
function draw(){
  const visibleServices=SERVICES.filter(s=>flt=="all"||s.s==flt);
  const cards=visibleServices.map(s=>`<article class="service-card"><span class="tag ${s.s}">${STATUS[s.s]}</span><h3>${s.t}</h3><p>${s.d}</p><a href="#contact">Enquire →</a></article>`).join("");
  serviceSet.innerHTML=cards;
  serviceSetCopy.innerHTML=cards;
  serviceSetCopy.inert=true;
  serviceSetCopy.setAttribute("aria-hidden","true");
  serviceViewport.scrollLeft=0;
}
function updateServicesMotion(){
  servicesMotion.disabled=reducedMotion.matches;
  servicesMotion.textContent=reducedMotion.matches?"Motion reduced":servicesPaused?"Resume motion":"Pause motion";
  servicesMotion.setAttribute("aria-label",reducedMotion.matches?"Automatic motion is disabled by your reduced motion setting":servicesPaused?"Resume moving service banners":"Pause moving service banners");
}
function animateServices(timestamp){
  if(lastServicesFrame&& !servicesPaused&&!servicesEngaged&&!document.hidden){
    const elapsed=Math.min(timestamp-lastServicesFrame,50);
    const loopPoint=serviceSet.offsetWidth+parseFloat(getComputedStyle($("#serviceTrack")).gap||"0");
    if(loopPoint>0){
      serviceViewport.scrollLeft+=elapsed*.035;
      if(serviceViewport.scrollLeft>=loopPoint)serviceViewport.scrollLeft-=loopPoint;
    }
  }
  lastServicesFrame=timestamp;
  requestAnimationFrame(animateServices);
}
F.querySelectorAll("button").forEach(button=>button.setAttribute("aria-pressed",String(button.classList.contains("on"))));
servicesMotion.onclick=()=>{servicesPaused=!servicesPaused;updateServicesMotion()};
$("#servicesPrevious").onclick=()=>serviceViewport.scrollBy({left:-serviceViewport.clientWidth*.8,behavior:reducedMotion.matches?"auto":"smooth"});
$("#servicesNext").onclick=()=>serviceViewport.scrollBy({left:serviceViewport.clientWidth*.8,behavior:reducedMotion.matches?"auto":"smooth"});
serviceViewport.addEventListener("pointerenter",()=>servicesEngaged=true);
serviceViewport.addEventListener("pointerleave",()=>servicesEngaged=false);
serviceViewport.addEventListener("focusin",()=>servicesEngaged=true);
serviceViewport.addEventListener("focusout",event=>{if(!serviceViewport.contains(event.relatedTarget))servicesEngaged=false});
serviceViewport.addEventListener("scroll",()=>{
  if(!serviceSet.offsetWidth)return;
  const card=serviceSet.querySelector(".service-card");
  const index=Math.floor(serviceViewport.scrollLeft/(card.offsetWidth+16))%serviceSet.children.length;
  servicesAnnouncement.textContent=`Service ${index+1} of ${serviceSet.children.length}: ${card ? serviceSet.children[index].querySelector("h3").textContent : ""}`;
},{passive:true});
reducedMotion.addEventListener("change",()=>{if(reducedMotion.matches)servicesPaused=true;updateServicesMotion()});
draw();
updateServicesMotion();
requestAnimationFrame(animateServices);
$("#projGrid").innerHTML=PROJECTS.map(p=>`<article class="card project-card"><span class="tag concept">Concept</span><h3>${p.t}</h3><p><b>Owner:</b> ${p.o}</p><p><b>MoFirms’ role:</b> ${p.r}</p><a class="project-link" href="#contact" data-cat="Project collaboration">Discuss a similar project <span aria-hidden="true">→</span></a></article>`).join("");
const clusterCards=VOFA_CLUSTERS.map(cluster=>`<article class="card project-card cluster-card"><span class="tag concept">Proposed · not approved or funded</span><h4>${cluster.t}</h4><ul aria-label="Activities under consideration">${cluster.activities.map(activity=>`<li>${activity}</li>`).join("")}</ul><a class="project-link" href="#contact" data-cat="Project collaboration">Discuss a similar project <span aria-hidden="true">→</span></a></article>`).join("");
const clusterViewport=$("#clustersViewport"),clusterSet=$("#clusterGrid"),clusterSetCopy=$("#clusterGridCopy"),clustersMotion=$("#clustersMotion"),clustersAnnouncement=$("#clustersAnnouncement");
clusterSet.innerHTML=clusterCards;
clusterSetCopy.innerHTML=clusterCards;
clusterSetCopy.inert=true;
clusterSetCopy.setAttribute("aria-hidden","true");
let clustersPaused=reducedMotion.matches,clustersEngaged=false,lastClustersFrame=0;
function updateClustersMotion(){
  clustersMotion.disabled=reducedMotion.matches;
  clustersMotion.textContent=reducedMotion.matches?"Motion reduced":clustersPaused?"Resume motion":"Pause motion";
  clustersMotion.setAttribute("aria-label",reducedMotion.matches?"Automatic motion is disabled by your reduced motion setting":clustersPaused?"Resume moving project cluster banners":"Pause moving project cluster banners");
}
function animateClusters(timestamp){
  if(lastClustersFrame&&!clustersPaused&&!clustersEngaged&&!document.hidden){
    const elapsed=Math.min(timestamp-lastClustersFrame,50);
    const loopPoint=clusterSet.offsetWidth+parseFloat(getComputedStyle($("#clusterTrack")).gap||"0");
    if(loopPoint>0){
      clusterViewport.scrollLeft+=elapsed*.035;
      if(clusterViewport.scrollLeft>=loopPoint)clusterViewport.scrollLeft-=loopPoint;
    }
  }
  lastClustersFrame=timestamp;
  requestAnimationFrame(animateClusters);
}
clustersMotion.onclick=()=>{clustersPaused=!clustersPaused;updateClustersMotion()};
$("#clustersPrevious").onclick=()=>clusterViewport.scrollBy({left:-clusterViewport.clientWidth*.8,behavior:reducedMotion.matches?"auto":"smooth"});
$("#clustersNext").onclick=()=>clusterViewport.scrollBy({left:clusterViewport.clientWidth*.8,behavior:reducedMotion.matches?"auto":"smooth"});
clusterViewport.addEventListener("pointerenter",()=>clustersEngaged=true);
clusterViewport.addEventListener("pointerleave",()=>clustersEngaged=false);
clusterViewport.addEventListener("focusin",()=>clustersEngaged=true);
clusterViewport.addEventListener("focusout",event=>{if(!clusterViewport.contains(event.relatedTarget))clustersEngaged=false});
clusterViewport.addEventListener("scroll",()=>{
  if(!clusterSet.offsetWidth)return;
  const firstCard=clusterSet.querySelector(".cluster-card");
  if(!firstCard)return;
  const index=Math.floor(clusterViewport.scrollLeft/(firstCard.offsetWidth+18))%clusterSet.children.length;
  clustersAnnouncement.textContent=`Cluster ${index+1} of ${clusterSet.children.length}: ${clusterSet.children[index].querySelector("h4").textContent}`;
},{passive:true});
reducedMotion.addEventListener("change",()=>{if(reducedMotion.matches)clustersPaused=true;updateClustersMotion()});
updateClustersMotion();
requestAnimationFrame(animateClusters);
$("#feat").innerHTML=FEATS.map(f=>`<li>${f}</li>`).join("");
const PORTAL_ACTIONS=["Register as a farmer","Register as a partner","Request financial analysis","Request an assessment","Apply as a researcher"];
const portalCards=PORTALS.map((p,i)=>`<li><h3>${p[0]}</h3><p>${p[1]}</p><a class="btn sm" href="${p[2]}">${PORTAL_ACTIONS[i]}</a></li>`).join("");
const portalViewport=$("#portalsViewport"),portalSet=$("#portals"),portalSetCopy=$("#portalsCopy"),portalsMotion=$("#portalsMotion"),portalsAnnouncement=$("#portalsAnnouncement");
portalSet.innerHTML=portalCards;
portalSetCopy.innerHTML=portalCards;
portalSetCopy.inert=true;
portalSetCopy.setAttribute("aria-hidden","true");
let portalsPaused=reducedMotion.matches,portalsEngaged=false,lastPortalsFrame=0;
function updatePortalsMotion(){
  portalsMotion.disabled=reducedMotion.matches;
  portalsMotion.textContent=reducedMotion.matches?"Motion reduced":portalsPaused?"Resume motion":"Pause motion";
  portalsMotion.setAttribute("aria-label",reducedMotion.matches?"Automatic motion is disabled by your reduced motion setting":portalsPaused?"Resume moving customer portal banners":"Pause moving customer portal banners");
}
function animatePortals(timestamp){
  if(lastPortalsFrame&&!portalsPaused&&!portalsEngaged&&!document.hidden){
    const elapsed=Math.min(timestamp-lastPortalsFrame,50);
    const loopPoint=portalSet.offsetWidth+parseFloat(getComputedStyle($("#portalTrack")).gap||"0");
    if(loopPoint>0){
      portalViewport.scrollLeft+=elapsed*.035;
      if(portalViewport.scrollLeft>=loopPoint)portalViewport.scrollLeft-=loopPoint;
    }
  }
  lastPortalsFrame=timestamp;
  requestAnimationFrame(animatePortals);
}
portalsMotion.onclick=()=>{portalsPaused=!portalsPaused;updatePortalsMotion()};
$("#portalsPrevious").onclick=()=>portalViewport.scrollBy({left:-portalViewport.clientWidth*.8,behavior:reducedMotion.matches?"auto":"smooth"});
$("#portalsNext").onclick=()=>portalViewport.scrollBy({left:portalViewport.clientWidth*.8,behavior:reducedMotion.matches?"auto":"smooth"});
portalViewport.addEventListener("pointerenter",()=>portalsEngaged=true);
portalViewport.addEventListener("pointerleave",()=>portalsEngaged=false);
portalViewport.addEventListener("focusin",()=>portalsEngaged=true);
portalViewport.addEventListener("focusout",event=>{if(!portalViewport.contains(event.relatedTarget))portalsEngaged=false});
portalViewport.addEventListener("scroll",()=>{
  if(!portalSet.offsetWidth)return;
  const firstCard=portalSet.querySelector("li");
  if(!firstCard)return;
  const index=Math.floor(portalViewport.scrollLeft/(firstCard.offsetWidth+14))%portalSet.children.length;
  portalsAnnouncement.textContent=`Portal ${index+1} of ${portalSet.children.length}: ${portalSet.children[index].querySelector("h3").textContent}`;
},{passive:true});
reducedMotion.addEventListener("change",()=>{if(reducedMotion.matches)portalsPaused=true;updatePortalsMotion()});
updatePortalsMotion();
requestAnimationFrame(animatePortals);
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
/* scroll reveal */
const io=new IntersectionObserver(es=>es.forEach(x=>x.isIntersecting&&x.target.classList.add("in")),{threshold:.1});
document.querySelectorAll("section:not(.hero):not(.hero-carousel) .card,.steps li,section:not(.hero):not(.hero-carousel) h2").forEach(n=>{n.classList.add("reveal");io.observe(n)});
