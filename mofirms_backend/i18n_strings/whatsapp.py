STRINGS = {
    "wa.menu": {
        "en": (
            "Welcome to MoFirms 🌱\n"
            "Reply with a number:\n"
            "1 - Register as a farmer\n"
            "2 - Check my registration status\n"
            "3 - See my registered details\n"
            "4 - Get a new login code\n"
            "5 - Talk to the MoFirms team\n"
            "Reply KISWAHILI for Swahili. Reply CANCEL any time to stop."
        ),
        "sw": (
            "Karibu MoFirms 🌱\n"
            "Jibu kwa namba:\n"
            "1 - Jisajili kama mkulima\n"
            "2 - Angalia hali ya usajili wangu\n"
            "3 - Ona taarifa zangu\n"
            "4 - Pata nambari mpya ya kuingia\n"
            "5 - Zungumza na timu ya MoFirms\n"
            "Jibu ENGLISH kwa Kiingereza. Jibu ACHA wakati wowote kusimamisha."
        ),
    },
    "wa.cancelled": {
        "en": "Okay, stopped. Reply MENU to see the options again.",
        "sw": "Sawa, imesimamishwa. Jibu MENU kuona chaguo tena.",
    },
    "wa.language_set": {
        "en": "Language set to English.",
        "sw": "Lugha imewekwa kuwa Kiswahili.",
    },
    "wa.help": {
        "en": (
            "Thank you. We have asked the MoFirms team to call you back on this number. "
            "You can also call +254 140 949 415 or email info@mofirm.co.ke."
        ),
        "sw": (
            "Asante. Tumeiomba timu ya MoFirms ikupigie simu kwa namba hii. "
            "Unaweza pia kupiga +254 140 949 415 au kutuma barua pepe info@mofirm.co.ke."
        ),
    },
    "wa.already_registered": {
        "en": "You are already registered (reference {reference}). Reply 2 to check your status.",
        "sw": "Tayari umesajiliwa (kumbukumbu {reference}). Jibu 2 kuangalia hali yako.",
    },
    "wa.not_registered": {
        "en": "We could not find a registration for this number. Reply 1 to register.",
        "sw": "Hatukupata usajili wa namba hii. Jibu 1 kujisajili.",
    },
    "wa.ask_name": {
        "en": "Let's register you. What is your full name?",
        "sw": "Tukusajili. Jina lako kamili ni nani?",
    },
    "wa.invalid_name": {
        "en": "Please type your full name (2 to 180 letters).",
        "sw": "Tafadhali andika jina lako kamili (herufi 2 hadi 180).",
    },
    "wa.ask_county": {
        "en": "Which county do you farm in? Type the county name, e.g. Vihiga.",
        "sw": "Unalima katika kaunti gani? Andika jina la kaunti, mfano Vihiga.",
    },
    "wa.invalid_county": {
        "en": "We could not find that county. Please type a Kenyan county name, e.g. Kisumu.",
        "sw": "Hatukupata kaunti hiyo. Tafadhali andika jina la kaunti ya Kenya, mfano Kisumu.",
    },
    "wa.ask_activities": {
        "en": "What do you farm? Reply with one or more numbers, e.g. 1 4\n{options}",
        "sw": "Unalima/unafuga nini? Jibu kwa namba moja au zaidi, mfano 1 4\n{options}",
    },
    "wa.invalid_activities": {
        "en": "Please reply with numbers from the list, e.g. 1 4.",
        "sw": "Tafadhali jibu kwa namba kutoka kwenye orodha, mfano 1 4.",
    },
    "wa.ask_consent": {
        "en": (
            "MoFirms will use these details to review your registration and contact you "
            "about it. Reply YES to agree and finish, or CANCEL to stop."
        ),
        "sw": (
            "MoFirms itatumia taarifa hizi kukagua usajili wako na kuwasiliana nawe "
            "kuhusu usajili huo. Jibu NDIO kukubali na kumaliza, au ACHA kusimamisha."
        ),
    },
    "wa.invalid_consent": {
        "en": "Reply YES to agree and finish, or CANCEL to stop.",
        "sw": "Jibu NDIO kukubali na kumaliza, au ACHA kusimamisha.",
    },
    "wa.registered": {
        "en": (
            "✅ You are registered! Your reference is {reference}.\n"
            "Your MoFirms login code is: {code}\n"
            "Keep this code private. Use it to check your details here, or to sign in at "
            "mofirm.co.ke/portal/login/whatsapp/ with this phone number.\n"
            "A MoFirms reviewer will check your registration within a few working days."
        ),
        "sw": (
            "✅ Umesajiliwa! Kumbukumbu yako ni {reference}.\n"
            "Nambari yako ya kuingia MoFirms ni: {code}\n"
            "Usimpe mtu nambari hii. Itumie kuangalia taarifa zako hapa, au kuingia kwenye "
            "mofirm.co.ke/portal/login/whatsapp/ kwa namba hii ya simu.\n"
            "Mkaguzi wa MoFirms atakagua usajili wako ndani ya siku chache za kazi."
        ),
    },
    "wa.new_code": {
        "en": (
            "Your new MoFirms login code is: {code}\n"
            "Your old code no longer works. Keep this one private."
        ),
        "sw": (
            "Nambari yako mpya ya kuingia MoFirms ni: {code}\n"
            "Nambari ya zamani haitumiki tena. Usimpe mtu nambari hii."
        ),
    },
    "wa.ask_code": {
        "en": "Please reply with your 6-digit MoFirms login code. Forgot it? Reply 4 for a new one.",
        "sw": "Tafadhali jibu kwa nambari yako ya tarakimu 6 ya MoFirms. Umeisahau? Jibu 4 upate mpya.",
    },
    "wa.wrong_code": {
        "en": "That code is not correct. {remaining} tries left. Reply 4 for a new code.",
        "sw": "Nambari hiyo si sahihi. Majaribio {remaining} yamebaki. Jibu 4 upate nambari mpya.",
    },
    "wa.locked": {
        "en": "Too many wrong codes. Please try again in {minutes} minutes, or reply 4 for a new code.",
        "sw": "Nambari nyingi zisizo sahihi. Jaribu tena baada ya dakika {minutes}, au jibu 4 upate mpya.",
    },
    "wa.status": {
        "en": "Reference: {reference}\nStatus: {status}\nSubmitted: {submitted}",
        "sw": "Kumbukumbu: {reference}\nHali: {status}\nIliwasilishwa: {submitted}",
    },
    "wa.details": {
        "en": (
            "Your MoFirms details:\nName: {name}\nCounty: {county}\n"
            "Farming: {activities}\nPhone: {phone}\nReference: {reference}\n"
            "To change anything, reply 5 to talk to the team."
        ),
        "sw": (
            "Taarifa zako za MoFirms:\nJina: {name}\nKaunti: {county}\n"
            "Kilimo: {activities}\nSimu: {phone}\nKumbukumbu: {reference}\n"
            "Kubadilisha chochote, jibu 5 kuzungumza na timu."
        ),
    },
    "wa.status.pending": {"en": "Pending review", "sw": "Inasubiri ukaguzi"},
    "wa.status.in_review": {"en": "In review", "sw": "Inakaguliwa"},
    "wa.status.verified": {"en": "Verified by MoFirms", "sw": "Imethibitishwa na MoFirms"},
    "wa.status.follow_up": {
        "en": "Needs follow-up — the team will contact you",
        "sw": "Inahitaji ufuatiliaji — timu itawasiliana nawe",
    },
    "wa.status.not_verified": {"en": "Not verified", "sw": "Haijathibitishwa"},
    "wa.delete_request": {
        "en": (
            "We have received your request to delete your data. A member of the MoFirms "
            "team will contact you on this number to confirm it is you, and let you know "
            "when your data has been deleted."
        ),
        "sw": (
            "Tumepokea ombi lako la kufuta taarifa zako. Mwanatimu wa MoFirms atawasiliana "
            "nawe kwa namba hii kuthibitisha kuwa ni wewe, na kukujulisha taarifa zako "
            "zikishafutwa."
        ),
    },
    "wa.unsupported": {
        "en": "Sorry, I can only read text messages. Reply MENU to see the options.",
        "sw": "Samahani, ninaweza kusoma ujumbe wa maandishi tu. Jibu MENU kuona chaguo.",
    },
    "farmers.wa_login.eyebrow": {"en": "Farmer portal", "sw": "Lango la mkulima"},
    "farmers.wa_login.title": {
        "en": "Sign in with your WhatsApp code",
        "sw": "Ingia kwa nambari yako ya WhatsApp",
    },
    "farmers.wa_login.body": {
        "en": (
            "Enter the phone number you registered on WhatsApp and your 6-digit MoFirms code. "
            "Lost your code? Send 4 to MoFirms on WhatsApp for a new one."
        ),
        "sw": (
            "Weka namba ya simu uliyosajili kwenye WhatsApp na nambari yako ya MoFirms ya "
            "tarakimu 6. Umepoteza nambari? Tuma 4 kwa MoFirms kwenye WhatsApp upate mpya."
        ),
    },
    "farmers.wa_login.phone_label": {"en": "WhatsApp phone number", "sw": "Namba ya simu ya WhatsApp"},
    "farmers.wa_login.code_label": {"en": "6-digit code", "sw": "Nambari ya tarakimu 6"},
    "farmers.wa_login.failed": {
        "en": "That phone number and code did not match. Check them and try again.",
        "sw": "Namba ya simu na nambari hazikulingana. Ziangalie kisha ujaribu tena.",
    },
    "farmers.wa_login.locked": {
        "en": "Too many wrong codes. Please wait 15 minutes or get a new code on WhatsApp.",
        "sw": "Nambari nyingi zisizo sahihi. Subiri dakika 15 au pata nambari mpya kwenye WhatsApp.",
    },
    "farmers.wa_login.link": {
        "en": "Registered on WhatsApp? Sign in with your WhatsApp code",
        "sw": "Ulisajiliwa kwenye WhatsApp? Ingia kwa nambari yako ya WhatsApp",
    },
    "farmers.wa_login.password_link": {
        "en": "Sign in with email and password instead",
        "sw": "Ingia kwa barua pepe na nenosiri badala yake",
    },
}
