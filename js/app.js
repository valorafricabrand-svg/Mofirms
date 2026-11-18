const LANG=(document.cookie.match(/(?:^|; )lang=([^;]*)/)||[])[1]==="sw"?"sw":"en";
const pick=(en,sw)=>LANG==="sw"?sw:en;
/* EDIT HERE: change a service's status independently of its text. status: now | spec | planned */
const STATUS=pick(
  {now:"Available now",spec:"Through an identified specialist",planned:"Planned"},
  {now:"Inapatikana sasa",spec:"Kupitia mtaalamu aliyetambuliwa",planned:"Imepangwa"}
);
const SERVICES=pick([
{t:"Agribusiness planning & access to finance",s:"now",d:"Business plans, feasibility assessments, cash-flow models and investment proposals, and preparation for lender or investor discussions. We support applications; we do not guarantee funding."},
{t:"Sustainable farming & farmer development",s:"now",d:"Farm planning, agroforestry, poultry, beekeeping and farmer training, where delivery capacity is confirmed. Organic-readiness and records support only; we do not issue certificates."},
{t:"Market access & enterprise development",s:"now",d:"Value-chain analysis, aggregation planning, buyer engagement and business formalisation support, with qualified professionals identified for legal work."},
{t:"Business intelligence & digital systems",s:"now",d:"Data-collection design, analysis and management dashboards. Farmer identification and traceability are development areas."},
{t:"Environmental greening & landscaping",s:"spec",d:"Advisory support for greening and landscaping plans. Our role is consultancy unless a different arrangement is documented."},
{t:"Climate projects & specialist coordination",s:"planned",d:"Scoping and coordination of climate opportunities such as solar, mobility and monitoring. Development area only: no accreditation, credit issuance or drone operations are claimed."},
{t:"SmartHasibu bookkeeping",s:"now",d:"Phone-friendly bookkeeping for farmers and small enterprises: record sales and costs, track credit, and review monthly totals."}],[
{t:"Upangaji wa kilimo-biashara na upatikanaji wa fedha",s:"now",d:"Mipango ya biashara, tathmini za uwezekano, mifano ya mtiririko wa fedha na mapendekezo ya uwekezaji, na maandalizi ya mazungumzo na wakopeshaji au wawekezaji. Tunasaidia maombi; hatuhakikishii ufadhili."},
{t:"Kilimo endelevu na maendeleo ya mkulima",s:"now",d:"Upangaji wa shamba, kilimo-mseto, ufugaji wa kuku, ufugaji nyuki na mafunzo ya wakulima, pale uwezo wa utoaji unapothibitishwa. Msaada wa kujiandaa kwa uthibitisho wa kilimo-hai na kumbukumbu pekee; hatutoi vyeti."},
{t:"Upatikanaji wa soko na maendeleo ya biashara",s:"now",d:"Uchambuzi wa mnyororo wa thamani, upangaji wa uwekaji pamoja, ushirikiano na wanunuzi na msaada wa urasimishaji wa biashara, pamoja na wataalamu waliohitimu kwa kazi za kisheria."},
{t:"Akili ya biashara na mifumo ya kidijitali",s:"now",d:"Ubunifu wa ukusanyaji wa data, uchambuzi na dashibodi za usimamizi. Utambuzi wa wakulima na ufuatiliaji wa mazao ni maeneo ya maendeleo."},
{t:"Uoto wa mazingira na mandhari",s:"spec",d:"Msaada wa ushauri kwa mipango ya uoto na mandhari. Jukumu letu ni ushauri isipokuwa mpango mwingine umeandikwa."},
{t:"Miradi ya hali ya hewa na uratibu wa kitaalamu",s:"planned",d:"Upekuzi na uratibu wa fursa za hali ya hewa kama vile jua, usafiri na ufuatiliaji. Eneo la maendeleo pekee: hakuna uthibitisho, utoaji wa mikopo ya kaboni au shughuli za ndege zisizo na rubani zinazodaiwa."},
{t:"Uhasibu wa SmartHasibu",s:"now",d:"Uhasibu rahisi wa simu kwa wakulima na biashara ndogo: andika mauzo na gharama, fuatilia mikopo, na kagua jumla za kila mwezi."}]
);
const PROJECTS=pick([
{t:"VOFA advisory work",s:"concept",o:"Vihiga Organic Farmers Association (separate organisation)",r:"Proposed agribusiness consulting and technical coordination, subject to a written engagement. Prospective client; not yet contracted."},
{t:"Agroforestry & poultry (VOFA Phase I)",s:"concept",o:"VOFA’s programme",r:"Part of VOFA’s proposed plan. Not a completed MoFirms project."},
{t:"Integrated Vihiga concept",s:"concept",o:"To be confirmed",r:"Digital agriculture, clean mobility, solar access and monitoring. A future programme concept until a funded scope is confirmed."},
{t:"Digital platform & carbon",s:"concept",o:"VOFA concept",r:"Farmer onboarding and monitoring ideas. Not live; no carbon credits have been issued."}],[
{t:"Kazi ya ushauri ya VOFA",s:"concept",o:"Vihiga Organic Farmers Association (shirika tofauti)",r:"Ushauri wa kilimo-biashara na uratibu wa kiufundi unaopendekezwa, ukitegemea mkataba ulioandikwa. Mteja mtarajiwa; bado hajakatiwa mkataba."},
{t:"Kilimo-mseto na kuku (VOFA Awamu ya I)",s:"concept",o:"Mpango wa VOFA",r:"Sehemu ya mpango unaopendekezwa na VOFA. Si mradi uliokamilika wa MoFirms."},
{t:"Dhana ya Vihiga iliyounganishwa",s:"concept",o:"Itathibitishwa",r:"Kilimo cha kidijitali, usafiri safi, upatikanaji wa jua na ufuatiliaji. Dhana ya mpango wa baadaye hadi wigo wenye ufadhili uthibitishwe."},
{t:"Jukwaa la kidijitali na kaboni",s:"concept",o:"Dhana ya VOFA",r:"Mawazo ya kujiunga na ufuatiliaji wa wakulima. Haijaanza; hakuna mikopo ya kaboni iliyotolewa."}]
);
const VOFA_CLUSTERS=pick([
{t:"Beekeeping & small livestock",activities:["Organic honey","Improved indigenous poultry under semi-free-range management","Rabbits","Pigs"]},
{t:"Orchards & tree crops",activities:["Apples, Hass and Fuerte avocado, mango, macadamia, and guava","Oil palm, including crude-oil processing","Vanilla intercropped with banana"]},
{t:"Oilseeds & protein crops",activities:["Sunflower for oil and press cake","Soya","Simsim (sesame)","Groundnuts","Sacha inchi"]},
{t:"Roots, vegetables, herbs & mushrooms",activities:["Sweet potatoes, including orange-fleshed varieties","Indigenous vegetables such as managu, saga, and terere","White ginger (Omukombero)","Mushrooms"]},
{t:"Fish farming",activities:["Pond aquaculture using locally formulated feed"]}],[
{t:"Ufugaji wa nyuki na mifugo midogo",activities:["Asali ya kiasili","Kuku wa kienyeji walioboreshwa chini ya usimamizi wa nusu-huru","Sungura","Nguruwe"]},
{t:"Mashamba ya miti na mazao ya miti",activities:["Maapulo, parachichi za Hass na Fuerte, embe, macadamia, na mapera","Mchikichi wa mafuta, ikiwemo uchakataji wa mafuta ghafi","Vanila iliyochanganywa na migomba"]},
{t:"Mbegu za mafuta na mazao ya protini",activities:["Alizeti kwa mafuta na mabaki ya kushinikizwa","Soya","Simsim (ufuta)","Karanga","Sacha inchi"]},
{t:"Mizizi, mboga, viungo na uyoga",activities:["Viazi vitamu, ikiwemo aina zenye rangi ya chungwa","Mboga za kiasili kama vile managu, saga, na terere","Tangawizi nyeupe (Omukombero)","Uyoga"]},
{t:"Ufugaji wa samaki",activities:["Ufugaji wa samaki wa madimbwi ukitumia chakula kilichotengenezwa kieneo"]}]
);
const FEATS=pick(
["Record farm sales and operating costs","Separate books for crops, livestock, and other activities","Track unpaid customer sales and supplier costs","Record partial or full credit repayments","Review monthly income, costs, and outstanding balances"],
["Andika mauzo na gharama za uendeshaji wa shamba","Weka vitabu tofauti vya mazao, mifugo, na shughuli nyingine","Fuatilia mauzo ya wateja na gharama za wasambazaji zisizolipwa","Andika malipo ya mkopo, kamili au sehemu","Kagua mapato, gharama, na salio linalodaiwa kila mwezi"]
);
const ONLINE_SERVICES=pick([
["Farmer and group registration","Register as a farmer or farmer group for MoFirms staff review. Identity and farm evidence are reviewed manually; uploads are private and time-limited.","/portal/register/"],
["Supplier, buyer and service-provider registration","Register suppliers, produce buyers, and professional service providers. Choose multiple roles and submit an optional business profile for MoFirms review.","/portal/partners/register/"],
["Financial analysis and business planning","Request specialist-reviewed financial statements, cash-flow analysis, business plans, budgeting, and funding readiness. Staff review the scope and send a fee quote before work begins.","/portal/financial-analysis/"],
["Risk and opportunity assessment","Request a human-led, specialist-prepared assessment of enterprise risks, resilience, and growth opportunities. Staff review the scope and issue a fee quote before work begins.","/portal/risk-assessment/"],
["Research and questionnaires","Research organisations, universities, marketing companies, and students can apply for manual vetting and submit studies for review. Respondents opt in separately; researchers receive aggregate results only.","/portal/research/register/"]],[
["Usajili wa mkulima na kikundi","Jisajili kama mkulima au kikundi cha wakulima kwa ukaguzi wa wafanyakazi wa MoFirms. Kitambulisho na ushahidi wa shamba hukaguliwa kwa mkono; mafaili yaliyopakiwa ni ya faragha na ya muda mfupi.","/portal/register/"],
["Usajili wa msambazaji, mnunuzi na mtoa huduma","Jisajili kama msambazaji, mnunuzi wa mazao, au mtoa huduma wa kitaalamu. Chagua majukumu kadhaa na wasilisha wasifu wa hiari wa biashara kwa ukaguzi wa MoFirms.","/portal/partners/register/"],
["Uchambuzi wa kifedha na upangaji wa biashara","Omba taarifa za kifedha zilizokaguliwa na wataalamu, uchambuzi wa mtiririko wa fedha, mipango ya biashara, bajeti, na utayari wa ufadhili. Wafanyakazi hukagua wigo na kutuma bei kabla kazi haijaanza.","/portal/financial-analysis/"],
["Tathmini ya hatari na fursa","Omba tathmini inayoongozwa na binadamu, iliyoandaliwa na mtaalamu, ya hatari za biashara, ustahimilivu, na fursa za ukuaji. Wafanyakazi hukagua wigo na kutoa bei kabla kazi haijaanza.","/portal/risk-assessment/"],
["Utafiti na hojaji","Mashirika ya utafiti, vyuo vikuu, kampuni za uuzaji, na wanafunzi wanaweza kuomba uchunguzi wa mkono na kuwasilisha tafiti kwa ukaguzi. Washiriki hukubali kwa hiari tofauti; watafiti hupokea matokeo ya pamoja pekee.","/portal/research/register/"]]
);
const PATHS=pick({
Farmer:["Farmers & farmer groups","Register an individual farmer or group, share farming and business needs, and request a MoFirms review.","/portal/register/"],
Entrepreneur:["Entrepreneurs","Business planning, cash-flow modelling and finance readiness for your venture.","#services"],
Institution:["Institutions & partners","Project design, analysis and partnership enquiries, with clear roles and ownership.","#projects"]},{
Farmer:["Wakulima na vikundi vya wakulima","Jisajili kama mkulima binafsi au kikundi, eleza mahitaji ya kilimo na biashara, na omba ukaguzi wa MoFirms.","/portal/register/"],
Entrepreneur:["Wajasiriamali","Upangaji wa biashara, uigaji wa mtiririko wa fedha na utayari wa kifedha kwa mradi wako.","#services"],
Institution:["Taasisi na washirika","Ubunifu wa miradi, uchambuzi na maswali ya ushirikiano, yenye majukumu na umiliki wazi.","#projects"]}
);
const $=s=>document.querySelector(s),el=(h)=>{const d=document.createElement("div");d.innerHTML=h.trim();return d.firstChild};
const reducedMotion=window.matchMedia("(prefers-reduced-motion: reduce)");
$("#yr").textContent=new Date().getFullYear();
const menu=$("#menu"),burger=$("#burger");
const UI_OPEN_MENU=pick("Open menu","Fungua menyu"),UI_CLOSE_MENU=pick("Close menu","Funga menyu");
function closeMenu(restoreFocus=false){
  menu.classList.remove("open");
  burger.setAttribute("aria-expanded","false");
  burger.setAttribute("aria-label",UI_OPEN_MENU);
  burger.textContent="☰";
  if(restoreFocus)burger.focus();
}
burger.onclick=()=>{
  const open=!menu.classList.contains("open");
  menu.classList.toggle("open",open);
  burger.setAttribute("aria-expanded",String(open));
  burger.setAttribute("aria-label",open?UI_CLOSE_MENU:UI_OPEN_MENU);
  burger.textContent=open?"×":"☰";
};
menu.addEventListener("click",event=>{if(event.target.closest("a"))closeMenu()});
document.addEventListener("keydown",event=>{if(event.key==="Escape"&&menu.classList.contains("open"))closeMenu(true)});
window.addEventListener("resize",()=>{if(window.innerWidth>980)closeMenu()});
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
    toggle.setAttribute("aria-label",reducedMotion.matches?pick("Automatic slide rotation is disabled by your reduced motion setting","Mzunguko wa kiotomatiki wa slaidi umezimwa na mpangilio wako wa mwendo uliopunguzwa"):carouselPaused?pick("Start automatic slide rotation","Anzisha mzunguko wa kiotomatiki wa slaidi"):pick("Pause automatic slide rotation","Simamisha mzunguko wa kiotomatiki wa slaidi"));
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
      slide.setAttribute("aria-label",`${i+1} ${pick("of","kati ya")} ${slides.length}: ${slide.querySelector("h1,h2").textContent}`);
    });
    currentDisplay.textContent=String(currentSlide+1).padStart(2,"0");
    progress.setAttribute("aria-valuenow",String(currentSlide+1));
    progressFill.style.width=`${((currentSlide+1)/slides.length)*100}%`;
    if(announce)announcement.textContent=pick(`Slide ${currentSlide+1} of ${slides.length}: ${slides[currentSlide].querySelector("h1,h2").textContent}`,`Slaidi ${currentSlide+1} kati ya ${slides.length}: ${slides[currentSlide].querySelector("h1,h2").textContent}`);
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
const UI_CONTINUE=pick("Continue","Endelea");
const tabs=$("#tabs");Object.keys(PATHS).forEach((k,i)=>{const b=el(`<button role="tab" aria-selected="${i==0}">${PATHS[k][0]}</button>`);b.onclick=()=>{tabs.querySelectorAll("button").forEach(x=>x.setAttribute("aria-selected","false"));b.setAttribute("aria-selected","true");show(k)};tabs.append(b)});
function show(k){const p=PATHS[k];$("#pathOut").innerHTML=`<h3>${p[0]}</h3><p>${p[1]}</p><a class="btn sm" href="${p[2]}">${UI_CONTINUE}</a>`}show("Farmer");
/* services */
const UI_ALL=pick("All","Zote"),UI_ENQUIRE=pick("Enquire →","Uliza →");
let flt="all";const F=$("#filters");
[["all",UI_ALL],...Object.entries(STATUS)].forEach(([k,v])=>{const b=el(`<button type="button" class="${k=="all"?"on":""}" aria-pressed="${k=="all"}">${v}</button>`);b.onclick=()=>{flt=k;F.querySelectorAll("button").forEach(x=>{x.classList.remove("on");x.setAttribute("aria-pressed","false")});b.classList.add("on");b.setAttribute("aria-pressed","true");draw()};F.append(b)});
const serviceViewport=$("#servicesViewport"),serviceSet=$("#serviceSet");
function draw(){
  const visibleServices=SERVICES.filter(s=>flt=="all"||s.s==flt);
  const cards=visibleServices.map(s=>`<article class="service-card"><span class="tag ${s.s}">${STATUS[s.s]}</span><h3>${s.t}</h3><p>${s.d}</p><a href="#contact">${UI_ENQUIRE}</a></article>`).join("");
  serviceSet.innerHTML=cards;
  serviceViewport.scrollLeft=0;
}
$("#servicesPrevious").onclick=()=>serviceViewport.scrollBy({left:-serviceViewport.clientWidth*.8,behavior:reducedMotion.matches?"auto":"smooth"});
$("#servicesNext").onclick=()=>serviceViewport.scrollBy({left:serviceViewport.clientWidth*.8,behavior:reducedMotion.matches?"auto":"smooth"});
draw();
const UI_CONCEPT=pick("Concept","Dhana"),UI_OWNER=pick("Owner:","Mmiliki:"),UI_MOFIRMS_ROLE=pick("MoFirms’ role:","Jukumu la MoFirms:"),UI_DISCUSS_PROJECT=pick("Discuss a similar project","Jadili mradi kama huu");
$("#projGrid").innerHTML=PROJECTS.map(p=>`<article class="card project-card"><span class="tag concept">${UI_CONCEPT}</span><h3>${p.t}</h3><p><b>${UI_OWNER}</b> ${p.o}</p><p><b>${UI_MOFIRMS_ROLE}</b> ${p.r}</p><a class="project-link" href="#contact" data-cat="Project collaboration">${UI_DISCUSS_PROJECT} <span aria-hidden="true">→</span></a></article>`).join("");
const UI_PROPOSED_TAG=pick("Proposed · not approved or funded","Imependekezwa · haijaidhinishwa wala kufadhiliwa"),UI_ACTIVITIES_LABEL=pick("Activities under consideration","Shughuli zinazozingatiwa");
const clusterCards=VOFA_CLUSTERS.map(cluster=>`<article class="card project-card cluster-card"><span class="tag concept">${UI_PROPOSED_TAG}</span><h4>${cluster.t}</h4><ul aria-label="${UI_ACTIVITIES_LABEL}">${cluster.activities.map(activity=>`<li>${activity}</li>`).join("")}</ul><a class="project-link" href="#contact" data-cat="Project collaboration">${UI_DISCUSS_PROJECT} <span aria-hidden="true">→</span></a></article>`).join("");
const clusterViewport=$("#clustersViewport"),clusterSet=$("#clusterGrid");
clusterSet.innerHTML=clusterCards;
$("#clustersPrevious").onclick=()=>clusterViewport.scrollBy({left:-clusterViewport.clientWidth*.8,behavior:reducedMotion.matches?"auto":"smooth"});
$("#clustersNext").onclick=()=>clusterViewport.scrollBy({left:clusterViewport.clientWidth*.8,behavior:reducedMotion.matches?"auto":"smooth"});
$("#feat").innerHTML=FEATS.map(f=>`<li>${f}</li>`).join("");
const ONLINE_SERVICE_ACTIONS=pick(
  ["Register as a farmer","Register as a partner","Request financial analysis","Request an assessment","Apply as a researcher"],
  ["Jisajili kama mkulima","Jisajili kama mshirika","Omba uchambuzi wa kifedha","Omba tathmini","Omba kuwa mtafiti"]
);
const onlineServiceCards=ONLINE_SERVICES.map((service,i)=>`<li><h3>${service[0]}</h3><p>${service[1]}</p><a class="btn sm" href="${service[2]}">${ONLINE_SERVICE_ACTIONS[i]}</a></li>`).join("");
$("#onlineServices").innerHTML=onlineServiceCards;
const onlineServiceViewport=$("#onlineServicesViewport");
$("#onlineServicesPrevious").onclick=()=>onlineServiceViewport.scrollBy({left:-onlineServiceViewport.clientWidth*.8,behavior:reducedMotion.matches?"auto":"smooth"});
$("#onlineServicesNext").onclick=()=>onlineServiceViewport.scrollBy({left:onlineServiceViewport.clientWidth*.8,behavior:reducedMotion.matches?"auto":"smooth"});
document.querySelectorAll("[data-cat]").forEach(a=>a.addEventListener("click",()=>{const option=[...$("#cat").options].find(item=>item.textContent===a.dataset.cat);if(option)$("#cat").value=option.value}));
/* change calculator */
const UI_CUSTOMER_OWES=pick("Customer owes KSh ","Mteja anadaiwa KSh "),UI_CHANGE=pick("Change: KSh ","Chenji: KSh ");
const calc=()=>{const c=(+$("#paid").value||0)-(+$("#amt").value||0);$("#chg").textContent=c<0?UI_CUSTOMER_OWES+(-c).toLocaleString():UI_CHANGE+c.toLocaleString()};
$("#amt").oninput=$("#paid").oninput=calc;
/* readiness check */
const Q=pick([
["Do you keep written records of sales and expenses?","records"],
["Do you know who your main buyers are?","buyers"],
["Do you have a written business plan?","plan"],
["Have you worked out your cash-flow for the next 12 months?","cash"],
["Do you know the main risks to your enterprise?","risk"]],[
["Je, unaweka kumbukumbu zilizoandikwa za mauzo na matumizi?","records"],
["Je, unajua ni akina nani wanunuzi wako wakuu?","buyers"],
["Je, una mpango wa biashara ulioandikwa?","plan"],
["Je, umekokotoa mtiririko wako wa fedha kwa miezi 12 ijayo?","cash"],
["Je, unajua hatari kuu zinazokabili biashara yako?","risk"]]
);
const TIPS=pick({
records:"Start simple bookkeeping with SmartHasibu.",
buyers:"Map buyers and test market access.",
plan:"A structured business plan would help most.",
cash:"A cash-flow model helps you prepare for financing.",
risk:"A risk and opportunity review would clarify priorities."},{
records:"Anza uhasibu rahisi na SmartHasibu.",
buyers:"Tambua wanunuzi na jaribu upatikanaji wa soko.",
plan:"Mpango wa biashara uliopangwa vizuri ungesaidia zaidi.",
cash:"Mfano wa mtiririko wa fedha unakusaidia kujiandaa kwa ufadhili.",
risk:"Mapitio ya hatari na fursa yangefafanua vipaumbele."}
);
let qi=0,gaps=[];const qz=$("#quiz");
const UI_IN_PLACE=pick("in place","vimewekwa"),UI_WELL_PREPARED=pick("You’re well prepared. We can help you grow further.","Umejiandaa vyema. Tunaweza kukusaidia kukua zaidi."),UI_INDICATION_ONLY=pick("An indication only, not an assessment.","Hii ni dalili tu, si tathmini."),UI_TALK_TO_US=pick("Talk to us","Zungumza nasi"),UI_RESTART=pick("Restart","Anza upya"),UI_QUESTION=pick("Question","Swali"),UI_YES=pick("Yes","Ndiyo"),UI_NOT_YET=pick("Not yet","Bado hapana");
function ask(){if(qi>=Q.length){const sc=Q.length-gaps.length;qz.innerHTML=`<h3>${sc} ${pick("of","kati ya")} ${Q.length} ${UI_IN_PLACE}</h3><div class="bar2"><i style="width:${sc/Q.length*100}%"></i></div>${gaps.length?"<ul>"+gaps.map(g=>`<li>${TIPS[g]}</li>`).join("")+"</ul>":`<p>${UI_WELL_PREPARED}</p>`}<p class="note">${UI_INDICATION_ONLY}</p><a class="btn sm" href="#contact">${UI_TALK_TO_US}</a> <button class="opt" id="rs">${UI_RESTART}</button>`;$("#rs").onclick=()=>{qi=0;gaps=[];ask()};return}
qz.innerHTML=`<p class="note">${UI_QUESTION} ${qi+1} ${pick("of","kati ya")} ${Q.length}</p><h3>${Q[qi][0]}</h3><button class="opt" data-a="1">${UI_YES}</button> <button class="opt" data-a="0">${UI_NOT_YET}</button>`;
qz.querySelectorAll("button").forEach(b=>b.onclick=()=>{if(b.dataset.a=="0")gaps.push(Q[qi][1]);qi++;ask()})}ask();
