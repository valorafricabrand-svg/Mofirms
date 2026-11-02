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
const FEATS=["Record farm sales and operating costs","Separate books for crops, livestock, and other activities","Track unpaid customer sales and supplier costs","Record partial or full credit repayments","Review monthly income, costs, and outstanding balances"];
const PORTALS=[["Portal A: Farmer registration","Securely capture farmer and group registrations for MoFirms staff review. Identity and farm evidence are reviewed manually; uploads are private and time-limited.","/portal/register/"],["Portal B: Supplier & buyer registration","Register suppliers, produce buyers, and professional service providers. Choose multiple roles and submit an optional business profile for MoFirms review.","/portal/partners/register/"],["Portal C: Financial analysis","Request specialist-reviewed financial statements, cash-flow analysis, business plans, budgeting, and funding readiness. Staff review the scope and send a fee quote before work begins.","/portal/financial-analysis/"],["Portal D: Risk & opportunity","Request a human-led, specialist-prepared assessment of enterprise risks, resilience, and growth opportunities. Staff review the scope and issue a fee quote before work begins.","/portal/risk-assessment/"],["Portal E: Research questionnaires","Research organisations, universities, marketing companies, and students can apply for manual vetting and submit studies for review. Respondents opt in separately; researchers receive aggregate results only.","/portal/research/register/"]];
const PATHS={Farmer:["Farmers & farmer groups","Register an individual farmer or group, share farming and business needs, and request a MoFirms review.","/portal/register/"],Entrepreneur:["Entrepreneurs","Business planning, cash-flow modelling and finance readiness for your venture.","#services"],Institution:["Institutions & partners","Project design, analysis and partnership enquiries, with clear roles and ownership.","#projects"]};
const CATS=["Agribusiness advice","Business intelligence","Training","Products","Project collaboration","SmartHasibu waitlist","Other"];
const $=s=>document.querySelector(s),el=(h)=>{const d=document.createElement("div");d.innerHTML=h.trim();return d.firstChild};
$("#yr").textContent=new Date().getFullYear();
$("#burger").onclick=e=>{const o=$("#menu").classList.toggle("open");e.target.setAttribute("aria-expanded",o)};
$("#menu").onclick=()=>$("#menu").classList.remove("open");
$("#pv").onclick=()=>{const notice=$("#privacy");notice.hidden=!notice.hidden;$("#pv").setAttribute("aria-expanded",String(!notice.hidden))};
/* agriculture story carousel */
const carousel=$("#agriCarousel");
if(carousel){
  const slides=[...carousel.querySelectorAll(".carousel-slide")];
  const dots=[...carousel.querySelectorAll(".carousel-dot")];
  const announcement=$("#carouselAnnouncement");
  let currentSlide=0;
  function showSlide(index,announce=false){
    currentSlide=(index+slides.length)%slides.length;
    slides.forEach((slide,i)=>{
      const active=i===currentSlide;
      slide.hidden=!active;
      slide.classList.toggle("is-active",active);
    });
    dots.forEach((dot,i)=>{
      const active=i===currentSlide;
      dot.classList.toggle("is-active",active);
      if(active)dot.setAttribute("aria-current","true");
      else dot.removeAttribute("aria-current");
    });
    if(announce)announcement.textContent=`Slide ${currentSlide+1} of ${slides.length}: ${slides[currentSlide].querySelector("h1,h2").textContent}`;
  }
  $("#carouselPrevious").onclick=()=>showSlide(currentSlide-1,true);
  $("#carouselNext").onclick=()=>showSlide(currentSlide+1,true);
  dots.forEach((dot,i)=>dot.onclick=()=>showSlide(i,true));
  carousel.addEventListener("keydown",event=>{
    if(event.key==="ArrowLeft"||event.key==="ArrowRight"){
      event.preventDefault();
      showSlide(currentSlide+(event.key==="ArrowRight"?1:-1),true);
    }
  });
  showSlide(0);
}
/* pathways */
const tabs=$("#tabs");Object.keys(PATHS).forEach((k,i)=>{const b=el(`<button role="tab" aria-selected="${i==0}">${PATHS[k][0]}</button>`);b.onclick=()=>{tabs.querySelectorAll("button").forEach(x=>x.setAttribute("aria-selected","false"));b.setAttribute("aria-selected","true");show(k)};tabs.append(b)});
function show(k){const p=PATHS[k];$("#pathOut").innerHTML=`<h3>${p[0]}</h3><p>${p[1]}</p><a class="btn sm" href="${p[2]}">Continue</a>`}show("Farmer");
/* services */
let flt="all";const F=$("#filters");
[["all","All"],...Object.entries(STATUS)].forEach(([k,v])=>{const b=el(`<button class="${k=="all"?"on":""}">${v}</button>`);b.onclick=()=>{flt=k;F.querySelectorAll("button").forEach(x=>x.classList.remove("on"));b.classList.add("on");draw()};F.append(b)});
function draw(){$("#svcGrid").innerHTML=SERVICES.filter(s=>flt=="all"||s.s==flt).map(s=>`<article class="card reveal in"><span class="tag ${s.s}">${STATUS[s.s]}</span><h3>${s.t}</h3><p>${s.d}</p><a href="#contact">Enquire →</a></article>`).join("")}draw();
$("#projGrid").innerHTML=PROJECTS.map(p=>`<article class="card"><span class="tag concept">Concept</span><h3>${p.t}</h3><p><b>Owner:</b> ${p.o}</p><p><b>MoFirms’ role:</b> ${p.r}</p></article>`).join("");
$("#feat").innerHTML=FEATS.map(f=>`<li>${f}</li>`).join("");
$("#portals").innerHTML=PORTALS.map((p,i)=>`<li><h3>${p[0]}</h3><p>${p[1]}</p>${i<5?`<a class="btn sm" href="${p[2]}">${["Register as a farmer","Register as a partner","Request financial analysis","Request an assessment","Apply as a researcher"][i]}</a>`:`<span class="tag planned">Under development</span>`}</li>`).join("");
$("#cat").innerHTML=CATS.map(c=>`<option>${c}</option>`).join("");
document.querySelectorAll("[data-cat]").forEach(a=>a.addEventListener("click",()=>$("#cat").value=a.dataset.cat));
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
/* enquiry form: validates, then opens the visitor's email app (static-site friendly) */
$("#form").onsubmit=e=>{e.preventDefault();const n=$("#name").value.trim(),w=$("#who").value.trim(),m=$("#msg").value.trim();
if(!n||!w||!m){$("#err").textContent="Please fill in your name, contact and message.";return}
if($("#how").value=="Email"&&!/^\S+@\S+\.\S+$/.test(w)){$("#err").textContent="Please enter a valid email address.";return}
$("#err").textContent="";const body=`Name: ${n}\nContact (${$("#how").value}): ${w}\nOrganisation/county: ${$("#org").value}\nUpdates OK: ${$("#mk").checked?"Yes":"No"}\n\n${m}`;
location.href=`mailto:mconceptslimited@gmail.com?subject=${encodeURIComponent("Website enquiry: "+$("#cat").value)}&body=${encodeURIComponent(body)}`;$("#ok").hidden=false};
/* scroll reveal */
const io=new IntersectionObserver(es=>es.forEach(x=>x.isIntersecting&&x.target.classList.add("in")),{threshold:.1});
document.querySelectorAll("section:not(.hero):not(.hero-carousel) .card,.steps li,section:not(.hero):not(.hero-carousel) h2").forEach(n=>{n.classList.add("reveal");io.observe(n)});
