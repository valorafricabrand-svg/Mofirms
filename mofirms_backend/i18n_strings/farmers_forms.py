STRINGS = {
    # ================= shared choice sets =================
    "choice.contact_preference.phone": {"en": "Phone or SMS", "sw": "Simu au SMS"},
    "choice.contact_preference.whatsapp": {"en": "WhatsApp", "sw": "WhatsApp"},
    "choice.contact_preference.email": {"en": "Email", "sw": "Barua pepe"},

    "choice.preferred_contact_short.email": {"en": "Email", "sw": "Barua pepe"},
    "choice.preferred_contact_short.phone": {"en": "Phone", "sw": "Simu"},
    "choice.preferred_contact_short.whatsapp": {"en": "WhatsApp", "sw": "WhatsApp"},

    "choice.applicant_type.general.individual": {"en": "Individual or sole proprietor", "sw": "Mtu binafsi au mmiliki pekee"},
    "choice.applicant_type.general.business": {"en": "Business, group, or organisation", "sw": "Biashara, kikundi, au shirika"},
    "choice.applicant_type.partner.individual": {"en": "Individual or sole proprietor", "sw": "Mtu binafsi au mmiliki pekee"},
    "choice.applicant_type.partner.business": {"en": "Registered or unregistered organisation", "sw": "Shirika lililosajiliwa au lisilosajiliwa"},

    "choice.registration_status.registered": {"en": "Registered", "sw": "Imesajiliwa"},
    "choice.registration_status.in_progress": {"en": "Registration in progress", "sw": "Usajili unaendelea"},
    "choice.registration_status.not_registered": {"en": "Not registered", "sw": "Haijasajiliwa"},
    "choice.registration_status.prefer_not": {"en": "Prefer not to say", "sw": "Napendelea nisiseme"},
    "choice.registration_status.choose_optional": {"en": "Choose one (optional)", "sw": "Chagua moja (si lazima)"},
    "choice.select_county": {"en": "Select a county", "sw": "Chagua kaunti"},

    # ================= FarmerRegistrationForm =================
    "field.farmer.activities": {"en": "What do you farm or plan to farm?", "sw": "Unalima nini au unapanga kulima nini?"},
    "field.farmer.water_sources": {"en": "Water sources used", "sw": "Vyanzo vya maji unavyotumia"},
    "field.farmer.sales_channels": {"en": "Where do you currently sell?", "sw": "Kwa sasa unauzia wapi?"},
    "field.farmer.challenges": {"en": "What are your main farming or business challenges?", "sw": "Ni changamoto zipi kuu za kilimo au biashara yako?"},
    "field.farmer.support_interests": {"en": "What support would be most useful?", "sw": "Msaada gani ungekufaa zaidi?"},
    "field.farmer.privacy_consent": {
        "en": "I agree that MoFirms may use these details to review this registration and contact me about it.",
        "sw": "Nakubali MoFirms kutumia maelezo haya kukagua usajili huu na kunipigia simu au kuwasiliana nami kulihusu.",
    },
    "field.farmer.research_invite_consent": {
        "en": (
            "Optional: I consent to MoFirms contacting me about research surveys. "
            "This does not enroll me or disclose my contact details to researchers. "
            "For a group, each respondent must separately choose to participate."
        ),
        "sw": (
            "Si lazima: Nakubali MoFirms kuwasiliana nami kuhusu tafiti. Hii "
            "hainiandikishi wala haitoi maelezo yangu ya mawasiliano kwa watafiti. "
            "Kwa kikundi, kila mshiriki lazima achague kushiriki kivyake."
        ),
    },
    "field.farmer.group_authorization_confirmed": {
        "en": "I am authorised to submit information for this group and have informed its members.",
        "sw": "Nimeidhinishwa kuwasilisha maelezo ya kikundi hiki na nimewajulisha wanachama wake.",
    },
    "field.farmer.create_account": {
        "en": "Create an account so I can sign in later and check my registration status.",
        "sw": "Fungua akaunti ili niweze kuingia baadaye na kuangalia hali ya usajili wangu.",
    },
    "field.farmer.password1": {"en": "Password", "sw": "Nenosiri"},
    "field.farmer.password2": {"en": "Confirm password", "sw": "Thibitisha nenosiri"},
    "help.farmer.password1": {
        "en": "Only needed if you tick \"Create an account\" above.",
        "sw": "Inahitajika tu ikiwa umeweka alama \"Fungua akaunti\" hapo juu.",
    },
    "help.farmer.group_registration_number": {
        "en": "Optional. Enter the organisation's registration number only, not a personal ID number or tax PIN.",
        "sw": "Si lazima. Ingiza namba ya usajili ya shirika pekee, si namba ya kitambulisho binafsi au PIN ya kodi.",
    },
    "help.farmer.farm_size": {
        "en": "Approximate area only. Do not enter coordinates or attach land documents.",
        "sw": "Eneo la makadirio pekee. Usiingize kuratibu au kuambatisha hati za ardhi.",
    },
    "help.farmer.production_summary": {
        "en": "Optional. Describe typical production and season. Avoid personal ID, bank account, or tax details.",
        "sw": "Si lazima. Eleza uzalishaji wa kawaida na msimu. Epuka kitambulisho binafsi, akaunti ya benki, au maelezo ya kodi.",
    },
    "help.farmer.sales_band": {
        "en": "Approximate annual farm/business sales; this is optional.",
        "sw": "Makadirio ya mauzo ya kila mwaka ya shamba/biashara; si lazima.",
    },
    "help.farmer.operating_cost_band": {
        "en": "Approximate annual operating costs; this is optional.",
        "sw": "Makadirio ya gharama za uendeshaji za kila mwaka; si lazima.",
    },
    "help.farmer.additional_notes": {
        "en": "Do not include ID numbers, PINs, account numbers, or passwords.",
        "sw": "Usijumuishe namba za kitambulisho, PIN, namba za akaunti, au manenosiri.",
    },
    "field.farmer.group_name": {"en": "Group or association name *", "sw": "Jina la kikundi au shirika *"},
    "field.farmer.group_type": {"en": "Organisation type *", "sw": "Aina ya shirika *"},
    "field.farmer.preferred_language": {"en": "Preferred language", "sw": "Lugha unayopendelea"},
    "err.farmer.group_field_required": {
        "en": "This field is required for a group registration.",
        "sw": "Sehemu hii inahitajika kwa usajili wa kikundi.",
    },
    "err.farmer.group_authorization_required": {
        "en": "Confirm that you are authorised to register this group.",
        "sw": "Thibitisha kuwa umeidhinishwa kusajili kikundi hiki.",
    },
    "err.farmer.email_required_for_contact": {
        "en": "Enter an email address if you prefer email contact.",
        "sw": "Ingiza barua pepe ikiwa unapendelea mawasiliano ya barua pepe.",
    },
    "err.farmer.phone_required_for_contact": {
        "en": "Enter a phone number for your preferred contact method.",
        "sw": "Ingiza namba ya simu kwa njia yako ya mawasiliano uliyopendelea.",
    },
    "err.farmer.farm_size_unit_required": {"en": "Choose acres or hectares.", "sw": "Chagua ekari au hekta."},
    "err.farmer.account_email_required": {
        "en": "Enter an email address to create an account.",
        "sw": "Ingiza barua pepe ili kufungua akaunti.",
    },
    "err.farmer.account_email_taken": {
        "en": "An account already uses this email address.",
        "sw": "Tayari kuna akaunti inayotumia barua pepe hii.",
    },
    "err.farmer.password_required": {"en": "Choose a password for your account.", "sw": "Chagua nenosiri la akaunti yako."},
    "err.farmer.password_confirm_required": {"en": "Confirm your chosen password.", "sw": "Thibitisha nenosiri ulilochagua."},
    "err.farmer.passwords_mismatch": {"en": "The passwords do not match.", "sw": "Manenosiri hayafanani."},
    "err.farmer.submission_failed": {
        "en": "The registration could not be submitted. Please try again.",
        "sw": "Imeshindikana kuwasilisha usajili. Tafadhali jaribu tena.",
    },

    "choice.registration_type.individual": {"en": "Individual farmer", "sw": "Mkulima binafsi"},
    "choice.registration_type.group": {"en": "Farmer group or association", "sw": "Kikundi au shirika la wakulima"},

    "choice.group_type.farmer_group": {"en": "Farmer group", "sw": "Kikundi cha wakulima"},
    "choice.group_type.self_help": {"en": "Self-help group", "sw": "Kikundi cha kujisaidia"},
    "choice.group_type.cooperative": {"en": "Cooperative", "sw": "Chama cha ushirika"},
    "choice.group_type.association": {"en": "Association", "sw": "Shirika"},
    "choice.group_type.producer_organisation": {"en": "Producer organisation", "sw": "Shirika la wazalishaji"},
    "choice.group_type.other": {"en": "Other", "sw": "Nyingine"},

    "choice.area_unit.acres": {"en": "Acres", "sw": "Ekari"},
    "choice.area_unit.hectares": {"en": "Hectares", "sw": "Hekta"},

    "choice.land_access.owned": {"en": "Owned by farmer or members", "sw": "Inamilikiwa na mkulima au wanachama"},
    "choice.land_access.leased": {"en": "Leased or rented", "sw": "Imekodishwa"},
    "choice.land_access.family_community": {"en": "Family or community land", "sw": "Ardhi ya familia au jamii"},
    "choice.land_access.other": {"en": "Other arrangement", "sw": "Mpango mwingine"},
    "choice.land_access.prefer_not": {"en": "Prefer not to say", "sw": "Napendelea nisiseme"},

    "choice.experience.under_1": {"en": "Less than 1 year", "sw": "Chini ya mwaka 1"},
    "choice.experience.1_3": {"en": "1–3 years", "sw": "Miaka 1–3"},
    "choice.experience.4_10": {"en": "4–10 years", "sw": "Miaka 4–10"},
    "choice.experience.over_10": {"en": "More than 10 years", "sw": "Zaidi ya miaka 10"},
    "choice.experience.prefer_not": {"en": "Prefer not to say", "sw": "Napendelea nisiseme"},

    "choice.financial_band.none": {"en": "None or not applicable", "sw": "Hakuna au haihusiki"},
    "choice.financial_band.under_100k": {"en": "Under KSh 100,000", "sw": "Chini ya KSh 100,000"},
    "choice.financial_band.100_500k": {"en": "KSh 100,000–500,000", "sw": "KSh 100,000–500,000"},
    "choice.financial_band.500k_2m": {"en": "KSh 500,001–2,000,000", "sw": "KSh 500,001–2,000,000"},
    "choice.financial_band.2_10m": {"en": "KSh 2,000,001–10,000,000", "sw": "KSh 2,000,001–10,000,000"},
    "choice.financial_band.over_10m": {"en": "Over KSh 10,000,000", "sw": "Zaidi ya KSh 10,000,000"},
    "choice.financial_band.prefer_not": {"en": "Prefer not to say", "sw": "Napendelea nisiseme"},

    "choice.record_keeping.none": {"en": "No regular written records", "sw": "Hakuna kumbukumbu za kawaida zilizoandikwa"},
    "choice.record_keeping.paper": {"en": "Paper records", "sw": "Kumbukumbu za karatasi"},
    "choice.record_keeping.digital": {"en": "Digital records", "sw": "Kumbukumbu za kidijitali"},
    "choice.record_keeping.both": {"en": "Paper and digital records", "sw": "Kumbukumbu za karatasi na kidijitali"},
    "choice.record_keeping.prefer_not": {"en": "Prefer not to say", "sw": "Napendelea nisiseme"},

    "choice.activity.crops": {"en": "Crops", "sw": "Mazao"},
    "choice.activity.livestock": {"en": "Livestock", "sw": "Mifugo"},
    "choice.activity.dairy": {"en": "Dairy", "sw": "Maziwa"},
    "choice.activity.poultry": {"en": "Poultry", "sw": "Kuku"},
    "choice.activity.horticulture": {"en": "Horticulture", "sw": "Kilimo cha bustani"},
    "choice.activity.beekeeping": {"en": "Beekeeping", "sw": "Ufugaji nyuki"},
    "choice.activity.fisheries": {"en": "Fisheries", "sw": "Uvuvi"},
    "choice.activity.agroforestry": {"en": "Agroforestry", "sw": "Kilimo-mseto"},
    "choice.activity.other": {"en": "Other", "sw": "Nyingine"},

    "choice.water_source.rainfed": {"en": "Rain-fed", "sw": "Inategemea mvua"},
    "choice.water_source.river": {"en": "River or stream", "sw": "Mto au kijito"},
    "choice.water_source.borehole": {"en": "Borehole or well", "sw": "Kisima"},
    "choice.water_source.piped": {"en": "Piped supply", "sw": "Maji ya bomba"},
    "choice.water_source.harvesting": {"en": "Rainwater harvesting", "sw": "Uvunaji wa maji ya mvua"},
    "choice.water_source.other": {"en": "Other", "sw": "Nyingine"},

    "choice.sales_channel.farm_gate": {"en": "Farm-gate sales", "sw": "Mauzo shambani"},
    "choice.sales_channel.local_market": {"en": "Local market", "sw": "Soko la hapa"},
    "choice.sales_channel.trader": {"en": "Trader or broker", "sw": "Mfanyabiashara au dalali"},
    "choice.sales_channel.cooperative": {"en": "Cooperative or farmer group", "sw": "Chama cha ushirika au kikundi cha wakulima"},
    "choice.sales_channel.processor": {"en": "Processor", "sw": "Kiwanda cha kuchakata"},
    "choice.sales_channel.retail": {"en": "Retail or direct to consumers", "sw": "Rejareja au moja kwa moja kwa watumiaji"},
    "choice.sales_channel.contract": {"en": "Contract or institutional buyer", "sw": "Mnunuzi wa mkataba au taasisi"},
    "choice.sales_channel.other": {"en": "Other", "sw": "Nyingine"},

    "choice.farmer_challenge.inputs": {"en": "Input cost or availability", "sw": "Gharama au upatikanaji wa pembejeo"},
    "choice.farmer_challenge.water": {"en": "Water or irrigation", "sw": "Maji au umwagiliaji"},
    "choice.farmer_challenge.weather": {"en": "Weather, pests, or disease", "sw": "Hali ya hewa, wadudu, au magonjwa"},
    "choice.farmer_challenge.labour": {"en": "Labour or skills", "sw": "Nguvu kazi au ujuzi"},
    "choice.farmer_challenge.storage": {"en": "Storage or post-harvest losses", "sw": "Uhifadhi au upotevu baada ya mavuno"},
    "choice.farmer_challenge.transport": {"en": "Transport or logistics", "sw": "Usafiri au vifaa"},
    "choice.farmer_challenge.markets": {"en": "Finding reliable buyers", "sw": "Kupata wanunuzi wa kuaminika"},
    "choice.farmer_challenge.finance": {"en": "Access to finance", "sw": "Upatikanaji wa fedha"},
    "choice.farmer_challenge.records": {"en": "Business records or planning", "sw": "Kumbukumbu za biashara au upangaji"},
    "choice.farmer_challenge.other": {"en": "Other", "sw": "Nyingine"},

    "choice.support.farm_planning": {"en": "Farm or production planning", "sw": "Upangaji wa shamba au uzalishaji"},
    "choice.support.training": {"en": "Training and capacity building", "sw": "Mafunzo na ujenzi wa uwezo"},
    "choice.support.markets": {"en": "Market access and buyers", "sw": "Upatikanaji wa soko na wanunuzi"},
    "choice.support.business_planning": {"en": "Business planning", "sw": "Upangaji wa biashara"},
    "choice.support.finance_readiness": {"en": "Finance readiness", "sw": "Utayari wa kifedha"},
    "choice.support.bookkeeping": {"en": "Bookkeeping and business records", "sw": "Uhasibu na kumbukumbu za biashara"},
    "choice.support.digital_tools": {"en": "Digital tools and data", "sw": "Zana za kidijitali na data"},
    "choice.support.climate": {"en": "Climate resilience", "sw": "Ustahimilivu wa hali ya hewa"},
    "choice.support.other": {"en": "Other or not sure yet", "sw": "Nyingine au sijui bado"},

    # ================= FarmerDocumentForm (and subclasses) =================
    "field.document.type": {"en": "Evidence type", "sw": "Aina ya ushahidi"},
    "field.document.type_financial": {"en": "Document type", "sw": "Aina ya hati"},
    "field.document.description": {"en": "Short description", "sw": "Maelezo mafupi"},
    "help.document.description": {
        "en": "Do not include ID numbers or other sensitive details in this description.",
        "sw": "Usijumuishe namba za kitambulisho au maelezo mengine nyeti kwenye maelezo haya.",
    },
    "field.document.file": {"en": "Choose a PDF, JPG, or PNG (maximum 5 MB)", "sw": "Chagua PDF, JPG, au PNG (upeo wa MB 5)"},
    "err.document.invalid_type": {"en": "Upload a PDF, JPG, or PNG file.", "sw": "Pakia faili la PDF, JPG, au PNG."},
    "err.document.too_large": {"en": "Each document must be no larger than 5 MB.", "sw": "Kila hati lazima isizidi MB 5."},
    "err.document.content_mismatch": {
        "en": "The file contents do not match the selected file type.",
        "sw": "Maudhui ya faili hayalingani na aina ya faili iliyochaguliwa.",
    },
    "err.document.dimensions_too_large": {"en": "The image dimensions are too large.", "sw": "Vipimo vya picha ni vikubwa mno."},
    "err.document.unreadable_image": {"en": "The image could not be safely read.", "sw": "Picha haikuweza kusomwa kwa usalama."},
    "err.document.scan_failed": {
        "en": "The evidence could not be scanned. Please try again later.",
        "sw": "Imeshindikana kuchunguza ushahidi. Tafadhali jaribu tena baadaye.",
    },
    "err.document.rejected_by_scanner": {
        "en": "The evidence could not be accepted. Check the file and try again.",
        "sw": "Imeshindikana kukubali ushahidi. Angalia faili na ujaribu tena.",
    },
    "err.document.choose_file_or_clear": {
        "en": "Choose a file or clear the description.",
        "sw": "Chagua faili au futa maelezo.",
    },

    "choice.farmer_document_type.identity": {"en": "Individual identity evidence", "sw": "Ushahidi wa kitambulisho binafsi"},
    "choice.farmer_document_type.group": {"en": "Group registration or governance evidence", "sw": "Ushahidi wa usajili au uongozi wa kikundi"},
    "choice.farmer_document_type.farm": {"en": "Farm activity or production evidence", "sw": "Ushahidi wa shughuli au uzalishaji wa shamba"},

    "choice.partner_document_type.identity": {"en": "Identity evidence for individual contact", "sw": "Ushahidi wa kitambulisho kwa mawasiliano binafsi"},
    "choice.partner_document_type.business": {"en": "Business or organisation registration", "sw": "Usajili wa biashara au shirika"},
    "choice.partner_document_type.authority": {"en": "Representative authorisation", "sw": "Idhini ya mwakilishi"},
    "choice.partner_document_type.professional": {"en": "Professional qualification or licence", "sw": "Sifa za kitaalamu au leseni"},
    "choice.partner_document_type.product": {"en": "Product catalogue or specification", "sw": "Katalogi au vipimo vya bidhaa"},
    "choice.partner_document_type.quality": {"en": "Quality, safety, or standards evidence", "sw": "Ushahidi wa ubora, usalama, au viwango"},
    "choice.partner_document_type.references": {"en": "Service or trade references", "sw": "Marejeleo ya huduma au biashara"},
    "choice.partner_document_type.capacity": {"en": "Supply or buying capacity evidence", "sw": "Ushahidi wa uwezo wa ugavi au ununuzi"},
    "choice.partner_document_type.other": {"en": "Other relevant evidence", "sw": "Ushahidi mwingine unaofaa"},

    "choice.financial_document_type.statement": {"en": "Financial statement or accounts", "sw": "Taarifa ya kifedha au hesabu"},
    "choice.financial_document_type.business_plan": {"en": "Business plan", "sw": "Mpango wa biashara"},
    "choice.financial_document_type.cash_flow": {"en": "Cash-flow or budget records", "sw": "Kumbukumbu za mtiririko wa fedha au bajeti"},
    "choice.financial_document_type.sales_records": {"en": "Sales or bookkeeping records", "sw": "Kumbukumbu za mauzo au uhasibu"},
    "choice.financial_document_type.other": {"en": "Other relevant document", "sw": "Hati nyingine inayofaa"},

    "choice.risk_document_type.business_profile": {"en": "Business or enterprise profile", "sw": "Wasifu wa biashara"},
    "choice.risk_document_type.production": {"en": "Production or operations summary", "sw": "Muhtasari wa uzalishaji au uendeshaji"},
    "choice.risk_document_type.market": {"en": "Market or customer summary", "sw": "Muhtasari wa soko au wateja"},
    "choice.risk_document_type.financial": {"en": "Redacted financial summary", "sw": "Muhtasari wa kifedha uliofichwa sehemu"},
    "choice.risk_document_type.other": {"en": "Other relevant document", "sw": "Hati nyingine inayofaa"},

    # ================= PartnerRegistrationForm =================
    "field.partner.roles": {"en": "How would you like to work with MoFirms?", "sw": "Ungependa kufanya kazi vipi na MoFirms?"},
    "field.partner.operating_counties": {"en": "Counties where you operate or deliver", "sw": "Kaunti unazofanyia kazi au kusambaza"},
    "field.partner.delivery_methods": {"en": "How do you deliver or collect?", "sw": "Unasambaza au kukusanya vipi?"},
    "field.partner.offer_categories": {"en": "What goods or services do you supply?", "sw": "Unatoa bidhaa au huduma zipi?"},
    "field.partner.produce_categories": {"en": "What produce are you looking to buy?", "sw": "Unatafuta kununua mazao gani?"},
    "field.partner.sourcing_counties": {"en": "Where are you looking to source produce?", "sw": "Unatafuta kupata mazao wapi?"},
    "field.partner.engagement_interests": {"en": "What would you like from a MoFirms partnership?", "sw": "Ungependa nini kutoka kwa ushirikiano na MoFirms?"},
    "field.partner.challenges": {"en": "What challenges would a partnership help address?", "sw": "Ushirikiano ungesaidia kutatua changamoto zipi?"},
    "field.partner.privacy_consent": {
        "en": (
            "I agree that MoFirms may review this registration and contact me about "
            "my business, offerings, buying needs, and relevant partnership enquiries."
        ),
        "sw": (
            "Nakubali MoFirms kukagua usajili huu na kuwasiliana nami kuhusu biashara "
            "yangu, ninachotoa, mahitaji yangu ya ununuzi, na maswali muhimu ya "
            "ushirikiano."
        ),
    },
    "field.partner.listing_consent": {
        "en": (
            "Optional: I agree that MoFirms may share relevant details from my business "
            "profile directly with potential farmer or business partners to facilitate "
            "a referral. This is not permission to publish my contact details."
        ),
        "sw": (
            "Si lazima: Nakubali MoFirms kushiriki maelezo muhimu kutoka kwenye wasifu "
            "wangu wa biashara moja kwa moja na wakulima au washirika watarajiwa wa "
            "biashara ili kuwezesha upendekezo. Hii si idhini ya kuchapisha maelezo "
            "yangu ya mawasiliano."
        ),
    },
    "field.partner.research_invite_consent": {
        "en": (
            "Optional: I consent to MoFirms contacting me about research surveys. "
            "This does not enroll me or disclose my contact details to researchers."
        ),
        "sw": (
            "Si lazima: Nakubali MoFirms kuwasiliana nami kuhusu tafiti. Hii "
            "hainiandikishi wala haitoi maelezo yangu ya mawasiliano kwa watafiti."
        ),
    },
    "help.partner.registration_number": {
        "en": "Business registration number only. Do not enter a personal ID number, KRA PIN, bank account, or password.",
        "sw": "Namba ya usajili wa biashara pekee. Usiingize namba ya kitambulisho binafsi, PIN ya KRA, akaunti ya benki, au nenosiri.",
    },
    "help.partner.website": {
        "en": "Optional public business website. Do not enter a sign-in or private link.",
        "sw": "Tovuti ya umma ya biashara, si lazima. Usiingize kiungo cha kuingia au cha faragha.",
    },
    "help.partner.business_size": {
        "en": "Approximate scale; do not enter revenue or account details.",
        "sw": "Ukubwa wa makadirio; usiingize mapato au maelezo ya akaunti.",
    },
    "help.partner.staff_band": {"en": "Approximate team capacity, not a staff list.", "sw": "Makadirio ya uwezo wa timu, si orodha ya wafanyakazi."},
    "help.partner.prices_and_terms": {
        "en": "Indicative only; do not enter confidential contract or bank details.",
        "sw": "Ni dalili pekee; usiingize maelezo ya siri ya mkataba au benki.",
    },
    "help.partner.clients_and_references": {
        "en": "Share reference names or organisations only if you have permission to do so.",
        "sw": "Shiriki majina ya marejeleo au mashirika tu ikiwa una ruhusa ya kufanya hivyo.",
    },
    "help.partner.licences_and_standards": {
        "en": "List relevant licence names and their issuing bodies. Do not include passwords or tax PINs.",
        "sw": "Orodhesha majina ya leseni zinazofaa na mashirika yaliyozitoa. Usijumuishe manenosiri au PIN za kodi.",
    },
    "help.partner.additional_notes": {
        "en": "Do not enter personal ID numbers, tax PINs, bank details, passwords, or confidential customer data.",
        "sw": "Usiingize namba za kitambulisho binafsi, PIN za kodi, maelezo ya benki, manenosiri, au data ya siri ya wateja.",
    },
    "field.partner.applicant_type": {"en": "Who does this profile represent?", "sw": "Wasifu huu unawakilisha nani?"},
    "field.partner.business_name": {"en": "Legal or registered business name", "sw": "Jina rasmi au la kisheria la biashara"},
    "err.partner.business_name_required": {
        "en": "Enter the name the organisation trades or registers under.",
        "sw": "Ingiza jina ambalo shirika linafanyia biashara au limesajiliwa nalo.",
    },
    "err.partner.email_required_for_contact": {
        "en": "Enter an email address for your preferred contact method.",
        "sw": "Ingiza barua pepe kwa njia yako ya mawasiliano uliyopendelea.",
    },
    "err.partner.phone_required_for_contact": {
        "en": "Enter a phone number for your preferred contact method.",
        "sw": "Ingiza namba ya simu kwa njia yako ya mawasiliano uliyopendelea.",
    },
    "err.partner.offer_categories_required": {
        "en": "Select at least one product or service you provide.",
        "sw": "Chagua angalau bidhaa au huduma moja unayotoa.",
    },
    "err.partner.offer_details_required": {
        "en": "Briefly describe what you supply and your availability.",
        "sw": "Eleza kwa ufupi unachosambaza na upatikanaji wako.",
    },
    "err.partner.produce_categories_required": {
        "en": "Select at least one type of produce you buy.",
        "sw": "Chagua angalau aina moja ya mazao unayonunua.",
    },
    "err.partner.produce_details_required": {
        "en": "Describe the produce you buy and any key specifications.",
        "sw": "Eleza mazao unayonunua na vipimo muhimu vyovyote.",
    },
    "err.partner.service_description_required": {
        "en": "Describe your services and the people or areas you serve.",
        "sw": "Eleza huduma zako na watu au maeneo unayohudumia.",
    },
    "err.partner.submission_failed": {
        "en": "The registration could not be submitted. Please try again.",
        "sw": "Imeshindikana kuwasilisha usajili. Tafadhali jaribu tena.",
    },

    "choice.partner_role.supplier": {"en": "Input or service supplier", "sw": "Msambazaji wa pembejeo au huduma"},
    "choice.partner_role.buyer": {"en": "Produce buyer", "sw": "Mnunuzi wa mazao"},
    "choice.partner_role.service_provider": {"en": "Professional or technical service provider", "sw": "Mtoa huduma wa kitaalamu au kiufundi"},

    "choice.partner_delivery.collection_point": {"en": "Buyer or supplier collection point", "sw": "Mahali pa kukusanyia pa mnunuzi au msambazaji"},
    "choice.partner_delivery.farm_gate": {"en": "Farm-gate collection or delivery", "sw": "Ukusanyaji au usambazaji shambani"},
    "choice.partner_delivery.county_delivery": {"en": "Delivery within a county", "sw": "Usambazaji ndani ya kaunti"},
    "choice.partner_delivery.multi_county": {"en": "Multi-county delivery or collection", "sw": "Usambazaji au ukusanyaji wa kaunti nyingi"},
    "choice.partner_delivery.national": {"en": "National delivery or collection", "sw": "Usambazaji au ukusanyaji wa kitaifa"},
    "choice.partner_delivery.online": {"en": "Online or remote service", "sw": "Huduma mtandaoni au ya mbali"},

    "choice.partner_offer.seeds_seedlings": {"en": "Seeds and seedlings", "sw": "Mbegu na miche"},
    "choice.partner_offer.fertilizer_soil": {"en": "Fertilizers, soil health, and crop inputs", "sw": "Mbolea, afya ya udongo, na pembejeo za mazao"},
    "choice.partner_offer.crop_protection": {"en": "Crop protection products", "sw": "Bidhaa za kulinda mazao"},
    "choice.partner_offer.farm_tools": {"en": "Farm tools and equipment", "sw": "Zana na vifaa vya shambani"},
    "choice.partner_offer.irrigation": {"en": "Irrigation and water systems", "sw": "Umwagiliaji na mifumo ya maji"},
    "choice.partner_offer.livestock_inputs": {"en": "Livestock feed and animal health", "sw": "Chakula cha mifugo na afya ya wanyama"},
    "choice.partner_offer.poultry_inputs": {"en": "Poultry inputs and equipment", "sw": "Pembejeo na vifaa vya kuku"},
    "choice.partner_offer.beekeeping": {"en": "Beekeeping inputs and equipment", "sw": "Pembejeo na vifaa vya ufugaji nyuki"},
    "choice.partner_offer.machinery": {"en": "Farm machinery and mechanisation", "sw": "Mitambo ya shambani na umekanika"},
    "choice.partner_offer.storage_processing": {"en": "Storage and processing", "sw": "Uhifadhi na uchakataji"},
    "choice.partner_offer.packaging": {"en": "Packaging and post-harvest handling", "sw": "Ufungaji na utunzaji baada ya mavuno"},
    "choice.partner_offer.transport": {"en": "Transport and logistics", "sw": "Usafiri na vifaa"},
    "choice.partner_offer.digital": {"en": "Digital and farm technology", "sw": "Teknolojia ya kidijitali na ya shambani"},
    "choice.partner_offer.training": {"en": "Training and capacity building", "sw": "Mafunzo na ujenzi wa uwezo"},
    "choice.partner_offer.consulting": {"en": "Agribusiness advisory and consulting", "sw": "Ushauri wa kilimo-biashara"},
    "choice.partner_offer.financial": {"en": "Finance and business support", "sw": "Fedha na msaada wa biashara"},
    "choice.partner_offer.veterinary": {"en": "Veterinary and animal-health services", "sw": "Huduma za mifugo na afya ya wanyama"},
    "choice.partner_offer.environmental": {"en": "Environmental and climate services", "sw": "Huduma za mazingira na hali ya hewa"},
    "choice.partner_offer.other": {"en": "Other goods or services", "sw": "Bidhaa au huduma nyingine"},

    "choice.produce_category.cereals": {"en": "Cereals and grains", "sw": "Nafaka"},
    "choice.produce_category.legumes": {"en": "Beans, peas, and pulses", "sw": "Maharagwe, njegere, na mikunde"},
    "choice.produce_category.roots": {"en": "Roots and tubers", "sw": "Mizizi"},
    "choice.produce_category.vegetables": {"en": "Vegetables", "sw": "Mboga"},
    "choice.produce_category.fruits": {"en": "Fruits", "sw": "Matunda"},
    "choice.produce_category.dairy": {"en": "Milk and dairy", "sw": "Maziwa na bidhaa zake"},
    "choice.produce_category.livestock": {"en": "Live animals and meat", "sw": "Wanyama hai na nyama"},
    "choice.produce_category.poultry": {"en": "Eggs and poultry", "sw": "Mayai na kuku"},
    "choice.produce_category.fish": {"en": "Fish and aquaculture", "sw": "Samaki na ufugaji wa samaki"},
    "choice.produce_category.honey": {"en": "Honey and bee products", "sw": "Asali na bidhaa za nyuki"},
    "choice.produce_category.oilseeds": {"en": "Oilseeds and oil crops", "sw": "Mbegu za mafuta na mazao ya mafuta"},
    "choice.produce_category.other": {"en": "Other produce", "sw": "Mazao mengine"},

    "choice.partner_engagement.supplier_referrals": {"en": "Be listed for farmer enquiries and referrals", "sw": "Kuorodheshwa kwa maswali na mapendekezo ya wakulima"},
    "choice.partner_engagement.buyer_linkages": {"en": "Find farmer groups and produce suppliers", "sw": "Kupata vikundi vya wakulima na wasambazaji wa mazao"},
    "choice.partner_engagement.project_work": {"en": "Explore projects or service contracts", "sw": "Kuchunguza miradi au mikataba ya huduma"},
    "choice.partner_engagement.market_events": {"en": "Hear about matching and market events", "sw": "Kupata habari za ulinganishaji na matukio ya soko"},

    "choice.partner_challenge.customer_access": {"en": "Finding farmers, groups, or customers", "sw": "Kupata wakulima, vikundi, au wateja"},
    "choice.partner_challenge.market_access": {"en": "Finding reliable buyers or suppliers", "sw": "Kupata wanunuzi au wasambazaji wa kuaminika"},
    "choice.partner_challenge.logistics": {"en": "Transport, delivery, or storage", "sw": "Usafiri, usambazaji, au uhifadhi"},
    "choice.partner_challenge.quality": {"en": "Quality standards or consistency", "sw": "Viwango vya ubora au uthabiti"},
    "choice.partner_challenge.working_capital": {"en": "Working capital or payment timing", "sw": "Mtaji wa kufanyia kazi au muda wa malipo"},
    "choice.partner_challenge.business_visibility": {"en": "Business visibility and referrals", "sw": "Mwonekano wa biashara na mapendekezo"},
    "choice.partner_challenge.contracting": {"en": "Contracts, procurement, or administration", "sw": "Mikataba, ununuzi, au utawala"},
    "choice.partner_challenge.skills": {"en": "Skills or specialist capacity", "sw": "Ujuzi au uwezo wa kitaalamu"},
    "choice.partner_challenge.other": {"en": "Other", "sw": "Nyingine"},

    # ================= FinancialAnalysisRequestForm / BusinessReadinessForm =================
    "field.financial.services_requested": {"en": "What financial support do you need?", "sw": "Unahitaji msaada gani wa kifedha?"},
    "field.financial.records_available": {"en": "Which records are available?", "sw": "Ni kumbukumbu zipi zinapatikana?"},
    "field.financial.privacy_consent": {
        "en": "I agree that MoFirms may review this request and contact me about its scope and a possible fee quote.",
        "sw": "Nakubali MoFirms kukagua ombi hili na kuwasiliana nami kuhusu wigo wake na bei inayowezekana.",
    },
    "help.financial.financial_period": {
        "en": "For example, January–December 2025. Approximate dates are fine.",
        "sw": "Kwa mfano, Januari–Desemba 2025. Tarehe za makadirio zinafaa.",
    },
    "help.financial.accounting_software": {
        "en": "Optional. Do not enter account names, passwords, or sign-in links.",
        "sw": "Si lazima. Usiingize majina ya akaunti, manenosiri, au viungo vya kuingia.",
    },
    "help.financial.annual_revenue_band": {
        "en": "Optional estimate only; do not enter exact account balances.",
        "sw": "Makadirio ya hiari pekee; usiingize salio kamili la akaunti.",
    },
    "help.financial.funding_need_band": {
        "en": "Optional estimate only; submitting a request is not a loan application.",
        "sw": "Makadirio ya hiari pekee; kuwasilisha ombi si maombi ya mkopo.",
    },
    "help.financial.request_summary": {
        "en": (
            "Describe the decision or output you need. Do not include passwords, account "
            "numbers, personal ID numbers, tax PINs, or unrelated people's data."
        ),
        "sw": (
            "Eleza uamuzi au matokeo unayohitaji. Usijumuishe manenosiri, namba za "
            "akaunti, namba za kitambulisho binafsi, PIN za kodi, au data ya watu "
            "wasiohusika."
        ),
    },
    "err.financial.submission_failed": {
        "en": "The request could not be submitted. Please try again.",
        "sw": "Imeshindikana kuwasilisha ombi. Tafadhali jaribu tena.",
    },

    "choice.financial_service.statement_review": {"en": "Financial statement or accounts review", "sw": "Mapitio ya taarifa ya kifedha au hesabu"},
    "choice.financial_service.business_plan": {"en": "Business plan development or review", "sw": "Uundaji au mapitio ya mpango wa biashara"},
    "choice.financial_service.cash_flow": {"en": "Cash-flow analysis", "sw": "Uchambuzi wa mtiririko wa fedha"},
    "choice.financial_service.budget_forecast": {"en": "Budget or financial forecast", "sw": "Bajeti au makadirio ya kifedha"},
    "choice.financial_service.funding_readiness": {"en": "Funding or lender readiness", "sw": "Utayari wa ufadhili au mkopeshaji"},
    "choice.financial_service.other": {"en": "Other financial analysis", "sw": "Uchambuzi mwingine wa kifedha"},

    "choice.records_available.financial_statements": {"en": "Financial statements", "sw": "Taarifa za kifedha"},
    "choice.records_available.sales_records": {"en": "Sales or income records", "sw": "Kumbukumbu za mauzo au mapato"},
    "choice.records_available.expense_records": {"en": "Expense or purchase records", "sw": "Kumbukumbu za matumizi au ununuzi"},
    "choice.records_available.cashbook": {"en": "Cashbook or bookkeeping records", "sw": "Kitabu cha fedha au kumbukumbu za uhasibu"},
    "choice.records_available.bank_statements": {"en": "Bank statements", "sw": "Taarifa za benki"},
    "choice.records_available.business_plan": {"en": "Existing business plan", "sw": "Mpango wa biashara uliopo"},
    "choice.records_available.budgets": {"en": "Budgets or forecasts", "sw": "Bajeti au makadirio"},
    "choice.records_available.none": {"en": "I do not have formal records yet", "sw": "Sina kumbukumbu rasmi bado"},

    "field.business_readiness.records_available": {"en": "Which records are available?", "sw": "Ni kumbukumbu zipi zinapatikana?"},
    "field.business_readiness.privacy_consent": {
        "en": "I agree that MoFirms may review this request and contact me about its scope and any proposed fee.",
        "sw": "Nakubali MoFirms kukagua ombi hili na kuwasiliana nami kuhusu wigo wake na bei yoyote inayopendekezwa.",
    },
    "field.business_readiness.average_monthly_sales": {"en": "Approximate average monthly sales (KSh)", "sw": "Wastani wa makadirio wa mauzo ya kila mwezi (KSh)"},
    "field.business_readiness.average_monthly_costs": {"en": "Approximate average monthly operating costs (KSh)", "sw": "Wastani wa makadirio wa gharama za uendeshaji za kila mwezi (KSh)"},
    "help.business_readiness.average_monthly_sales": {
        "en": "Optional estimate. Do not enter bank balances or account numbers.",
        "sw": "Makadirio ya hiari. Usiingize salio la benki au namba za akaunti.",
    },
    "help.business_readiness.average_monthly_costs": {
        "en": "Optional estimate for the same period as monthly sales.",
        "sw": "Makadirio ya hiari kwa kipindi kile kile cha mauzo ya kila mwezi.",
    },
    "help.business_readiness.financial_period": {"en": "Optional period covered by the records or estimates.", "sw": "Kipindi cha hiari kinachofunikwa na kumbukumbu au makadirio."},
    "help.business_readiness.business_goal": {"en": "What would you like the farm or enterprise to achieve?", "sw": "Ungependa shamba au biashara ifikie nini?"},
    "help.business_readiness.current_challenge": {"en": "What is the main issue you would like help addressing?", "sw": "Ni suala gani kuu ungependa kupata msaada wa kulitatua?"},
    "help.business_readiness.seasonality_notes": {
        "en": "Optional: note months when sales, production, or costs change.",
        "sw": "Si lazima: taja miezi ambapo mauzo, uzalishaji, au gharama hubadilika.",
    },
    "err.business_readiness.records_none_alone": {
        "en": "Choose 'I do not have formal records yet' by itself.",
        "sw": "Chagua 'Sina kumbukumbu rasmi bado' pekee yake.",
    },
    "err.business_readiness.sales_costs_both_or_neither": {
        "en": "Enter both monthly sales and monthly costs, or leave both blank.",
        "sw": "Ingiza mauzo na gharama za kila mwezi zote mbili, au uache zote tupu.",
    },
    "err.business_readiness.submission_failed": {
        "en": "The request could not be submitted. Please try again.",
        "sw": "Imeshindikana kuwasilisha ombi. Tafadhali jaribu tena.",
    },

    # ================= RiskAssessmentRequestForm =================
    "field.risk.assessment_areas": {"en": "What should the assessment cover?", "sw": "Tathmini inapaswa kuhusu nini?"},
    "field.risk.risk_priorities": {"en": "Which risks or uncertainties matter most?", "sw": "Ni hatari au mashaka gani ya muhimu zaidi?"},
    "field.risk.opportunity_priorities": {"en": "What opportunities would you like to explore?", "sw": "Ungependa kuchunguza fursa zipi?"},
    "field.risk.privacy_consent": {
        "en": "I agree that MoFirms may review this request and contact me about its scope and a possible fee quote.",
        "sw": "Nakubali MoFirms kukagua ombi hili na kuwasiliana nami kuhusu wigo wake na bei inayowezekana.",
    },
    "help.risk.business_name": {"en": "Required for a business, group, or organisation.", "sw": "Inahitajika kwa biashara, kikundi, au shirika."},
    "help.risk.sector": {"en": "For example, dairy, horticulture, produce trading, or farm services.", "sw": "Kwa mfano, maziwa, bustani, biashara ya mazao, au huduma za shambani."},
    "help.risk.request_summary": {
        "en": (
            "Describe the decision you are considering, the main concern or opportunity, "
            "and what a useful assessment should help you understand. Do not include "
            "passwords, ID numbers, tax PINs, account numbers, or confidential third-party data."
        ),
        "sw": (
            "Eleza uamuzi unaofikiria, wasiwasi au fursa kuu, na kile tathmini bora "
            "inapaswa kukusaidia kuelewa. Usijumuishe manenosiri, namba za "
            "kitambulisho, PIN za kodi, namba za akaunti, au data ya siri ya watu "
            "wengine."
        ),
    },
    "err.risk.submission_failed": {
        "en": "The request could not be submitted. Please try again.",
        "sw": "Imeshindikana kuwasilisha ombi. Tafadhali jaribu tena.",
    },

    "choice.enterprise_stage.production": {"en": "Production or farming", "sw": "Uzalishaji au kilimo"},
    "choice.enterprise_stage.aggregation": {"en": "Aggregation or cooperatives", "sw": "Uwekaji pamoja au vyama vya ushirika"},
    "choice.enterprise_stage.processing": {"en": "Processing or value addition", "sw": "Uchakataji au kuongeza thamani"},
    "choice.enterprise_stage.distribution": {"en": "Wholesale or distribution", "sw": "Jumla au usambazaji"},
    "choice.enterprise_stage.retail": {"en": "Retail or direct sales", "sw": "Rejareja au mauzo ya moja kwa moja"},
    "choice.enterprise_stage.services": {"en": "Agricultural services or inputs", "sw": "Huduma za kilimo au pembejeo"},
    "choice.enterprise_stage.multiple": {"en": "Multiple stages", "sw": "Hatua nyingi"},
    "choice.enterprise_stage.other": {"en": "Other or not sure", "sw": "Nyingine au sijui"},

    "choice.time_horizon.immediate": {"en": "Immediate decision (within 3 months)", "sw": "Uamuzi wa haraka (ndani ya miezi 3)"},
    "choice.time_horizon.this_year": {"en": "Within 12 months", "sw": "Ndani ya miezi 12"},
    "choice.time_horizon.longer_term": {"en": "More than 12 months", "sw": "Zaidi ya miezi 12"},
    "choice.time_horizon.exploratory": {"en": "Exploratory; no fixed deadline", "sw": "Uchunguzi; hakuna tarehe ya mwisho maalum"},

    "choice.assessment_area.enterprise": {"en": "Business model and enterprise resilience", "sw": "Mfumo wa biashara na ustahimilivu wa biashara"},
    "choice.assessment_area.market": {"en": "Markets, customers, and competition", "sw": "Masoko, wateja, na ushindani"},
    "choice.assessment_area.operations": {"en": "Production and day-to-day operations", "sw": "Uzalishaji na shughuli za kila siku"},
    "choice.assessment_area.financial_resilience": {"en": "Financial resilience and exposure", "sw": "Ustahimilivu wa kifedha na mwelekeo wa hatari"},
    "choice.assessment_area.climate_environment": {"en": "Climate and environmental factors", "sw": "Mambo ya hali ya hewa na mazingira"},
    "choice.assessment_area.supply_chain": {"en": "Suppliers, logistics, and value chain", "sw": "Wasambazaji, vifaa, na mnyororo wa thamani"},
    "choice.assessment_area.governance_compliance": {"en": "Governance and compliance", "sw": "Uongozi na ufuasi wa sheria"},
    "choice.assessment_area.technology": {"en": "Technology and data", "sw": "Teknolojia na data"},
    "choice.assessment_area.other": {"en": "Other or not sure", "sw": "Nyingine au sijui"},

    "choice.risk_priority.production": {"en": "Production, pests, disease, or input access", "sw": "Uzalishaji, wadudu, magonjwa, au upatikanaji wa pembejeo"},
    "choice.risk_priority.climate": {"en": "Weather, water, or climate exposure", "sw": "Hali ya hewa, maji, au mwelekeo wa hatari ya hali ya hewa"},
    "choice.risk_priority.market": {"en": "Price changes, buyer access, or competition", "sw": "Mabadiliko ya bei, upatikanaji wa wanunuzi, au ushindani"},
    "choice.risk_priority.financial": {"en": "Cash flow, cost changes, or funding exposure", "sw": "Mtiririko wa fedha, mabadiliko ya gharama, au mwelekeo wa ufadhili"},
    "choice.risk_priority.operations": {"en": "People, equipment, process, or continuity", "sw": "Watu, vifaa, mchakato, au uendelevu"},
    "choice.risk_priority.supply_chain": {"en": "Suppliers, transport, storage, or delivery", "sw": "Wasambazaji, usafiri, uhifadhi, au usambazaji"},
    "choice.risk_priority.governance": {"en": "Management, records, or decision-making", "sw": "Usimamizi, kumbukumbu, au ufanyaji maamuzi"},
    "choice.risk_priority.regulatory": {"en": "Licensing, standards, or regulatory changes", "sw": "Leseni, viwango, au mabadiliko ya kanuni"},
    "choice.risk_priority.technology": {"en": "Technology access, reliability, or data", "sw": "Upatikanaji wa teknolojia, uaminifu, au data"},
    "choice.risk_priority.not_sure": {"en": "I am not sure yet; help us scope the risks", "sw": "Sijui bado; tusaidie kubainisha hatari"},

    "choice.opportunity_priority.market_growth": {"en": "New markets, customers, or buyer relationships", "sw": "Masoko mapya, wateja, au uhusiano na wanunuzi"},
    "choice.opportunity_priority.value_addition": {"en": "Processing, storage, or value addition", "sw": "Uchakataji, uhifadhi, au kuongeza thamani"},
    "choice.opportunity_priority.productivity": {"en": "Productivity, quality, or cost improvements", "sw": "Uzalishaji, ubora, au uboreshaji wa gharama"},
    "choice.opportunity_priority.climate_resilience": {"en": "Climate adaptation or resource efficiency", "sw": "Kukabiliana na hali ya hewa au ufanisi wa rasilimali"},
    "choice.opportunity_priority.digital": {"en": "Digital tools or better business information", "sw": "Zana za kidijitali au taarifa bora za biashara"},
    "choice.opportunity_priority.partnerships": {"en": "Partnerships, aggregation, or collaboration", "sw": "Ushirikiano, uwekaji pamoja, au ushirikiano wa pamoja"},
    "choice.opportunity_priority.finance_readiness": {"en": "Investment or finance readiness", "sw": "Uwekezaji au utayari wa kifedha"},
    "choice.opportunity_priority.new_products": {"en": "New products or services", "sw": "Bidhaa au huduma mpya"},
    "choice.opportunity_priority.not_sure": {"en": "I am not sure yet; help identify opportunities", "sw": "Sijui bado; saidia kubainisha fursa"},

    # ================= ResearcherApplicationForm =================
    "field.researcher.email": {"en": "Institutional or work email", "sw": "Barua pepe ya taasisi au kazi"},
    "field.researcher.password1": {"en": "Password", "sw": "Nenosiri"},
    "field.researcher.password2": {"en": "Confirm password", "sw": "Thibitisha nenosiri"},
    "help.researcher.password1": {
        "en": "Use a unique password. Researcher access stays disabled until staff approval.",
        "sw": "Tumia nenosiri la kipekee. Ufikiaji wa mtafiti utabaki umezimwa hadi idhini ya wafanyakazi.",
    },
    "help.researcher.research_purpose": {
        "en": "What research will you conduct and what decisions may it inform?",
        "sw": "Utafiti gani utafanya na unaweza kufahamisha maamuzi gani?",
    },
    "help.researcher.methods_summary": {
        "en": "Describe recruitment, data handling, ethics review, and how findings will be used.",
        "sw": "Eleza uajiri wa washiriki, utunzaji wa data, mapitio ya kimaadili, na jinsi matokeo yatakavyotumika.",
    },
    "field.researcher.consent": {
        "en": (
            "I agree to MoFirms reviewing this application and contacting me about vetting. "
            "I understand that approval is manual and does not provide customer data access."
        ),
        "sw": (
            "Nakubali MoFirms kukagua ombi hili na kuwasiliana nami kuhusu uchunguzi. "
            "Naelewa idhini ni ya mkono na haitoi ufikiaji wa data ya wateja."
        ),
    },
    "err.researcher.email_taken": {
        "en": "An account using this email already exists.",
        "sw": "Tayari kuna akaunti inayotumia barua pepe hii.",
    },
    "err.researcher.passwords_mismatch": {"en": "The passwords do not match.", "sw": "Manenosiri hayafanani."},
    "err.researcher.supervisor_name_required": {
        "en": "Student applications require a supervisor.",
        "sw": "Maombi ya wanafunzi yanahitaji msimamizi.",
    },
    "err.researcher.supervisor_email_required": {
        "en": "Provide the supervisor's institutional email.",
        "sw": "Toa barua pepe ya taasisi ya msimamizi.",
    },
    "err.researcher.application_failed": {
        "en": "The application could not be saved. Please try again or contact MoFirms.",
        "sw": "Imeshindikana kuhifadhi ombi. Tafadhali jaribu tena au wasiliana na MoFirms.",
    },

    "choice.researcher_applicant_type.organisation": {"en": "Research organisation", "sw": "Shirika la utafiti"},
    "choice.researcher_applicant_type.university": {"en": "University or academic institution", "sw": "Chuo kikuu au taasisi ya kitaaluma"},
    "choice.researcher_applicant_type.marketing": {"en": "Marketing or insights company", "sw": "Kampuni ya uuzaji au utafiti wa soko"},
    "choice.researcher_applicant_type.student": {"en": "Research student", "sw": "Mwanafunzi wa utafiti"},

    # ================= ConsultationLeadForm / NewsletterSubscriptionForm =================
    "field.consultation.privacy_consent": {
        "en": "I agree that MoFirms may use these details to respond to my consultation request.",
        "sw": "Nakubali MoFirms kutumia maelezo haya kujibu ombi langu la mashauriano.",
    },
    "choice.consultation_category.agribusiness": {"en": "Agribusiness advice", "sw": "Ushauri wa kilimo-biashara"},
    "choice.consultation_category.business_intelligence": {"en": "Business intelligence", "sw": "Akili ya biashara"},
    "choice.consultation_category.training": {"en": "Training", "sw": "Mafunzo"},
    "choice.consultation_category.products": {"en": "Products", "sw": "Bidhaa"},
    "choice.consultation_category.project": {"en": "Project collaboration", "sw": "Ushirikiano wa mradi"},
    "choice.consultation_category.smart_hasibu": {"en": "SmartHasibu support", "sw": "Msaada wa SmartHasibu"},
    "choice.consultation_category.other": {"en": "Other", "sw": "Nyingine"},

    "field.newsletter.topics": {"en": "Choose the updates you want", "sw": "Chagua taarifa unazotaka"},
    "field.newsletter.marketing_consent": {
        "en": "I agree to receive the MoFirms newsletter by email about the topics selected. I can unsubscribe at any time.",
        "sw": "Nakubali kupokea taarifa za MoFirms kwa barua pepe kuhusu mada zilizochaguliwa. Naweza kujitoa wakati wowote.",
    },
    "choice.newsletter_topic.farming": {"en": "Farming and agribusiness", "sw": "Kilimo na kilimo-biashara"},
    "choice.newsletter_topic.entrepreneurship": {"en": "Entrepreneurship and business advisory", "sw": "Ujasiriamali na ushauri wa biashara"},
    "choice.newsletter_topic.risk_assessment": {"en": "Business risk assessment", "sw": "Tathmini ya hatari za biashara"},

    "err.honeypot.unable_to_submit": {
        "en": "Unable to submit this request.",
        "sw": "Imeshindikana kuwasilisha ombi hili.",
    },

    # ================= views.py generic messages =================
    "err.view.too_many_requests": {
        "en": "Too many requests. Please try again later.",
        "sw": "Maombi mengi mno. Tafadhali jaribu tena baadaye.",
    },
    "err.view.newsletter_save_failed": {
        "en": "We couldn’t save your subscription. Please try again later.",
        "sw": "Imeshindikana kuhifadhi usajili wako. Tafadhali jaribu tena baadaye.",
    },
    "err.view.upload_too_large": {
        "en": "The combined upload size must not exceed 100 MB.",
        "sw": "Jumla ya ukubwa wa mafaili yaliyopakiwa haipaswi kuzidi MB 100.",
    },
    "err.view.document_consent_required_evidence": {
        "en": "Please agree to the one-year document retention notice before uploading evidence.",
        "sw": "Tafadhali kubali taarifa ya uhifadhi wa hati wa mwaka mmoja kabla ya kupakia ushahidi.",
    },
    "err.view.document_consent_required_files": {
        "en": "Please agree to the one-year document retention notice before uploading files.",
        "sw": "Tafadhali kubali taarifa ya uhifadhi wa hati wa mwaka mmoja kabla ya kupakia mafaili.",
    },
    "err.view.registration_save_failed": {
        "en": "The registration could not be saved because a file could not be stored. Please try again.",
        "sw": "Imeshindikana kuhifadhi usajili kwa sababu faili halikuweza kuhifadhiwa. Tafadhali jaribu tena.",
    },
    "err.view.request_save_failed": {
        "en": "The request could not be saved because a file could not be stored. Please try again.",
        "sw": "Imeshindikana kuhifadhi ombi kwa sababu faili halikuweza kuhifadhiwa. Tafadhali jaribu tena.",
    },
}
