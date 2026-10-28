import { YEARS, SINCE } from "./content";
/* ═══════════════════════════════════════════════════════════════════
   CHAT ASSISTANT — ready answers in English, Telugu and Hindi.
   These work instantly and without any AI key. When the AI is switched on
   (server setting), typed questions are answered by the AI using the
   clinic's instruction sheets; these topics stay as quick buttons.
   Each answer: an array of lines; lines starting with "• " are bullets.
   ═══════════════════════════════════════════════════════════════════ */

export const LANGS = [["en", "English"], ["te", "తెలుగు"], ["hi", "हिंदी"]];

export const UI = {
  en: {
    title: "Clinic assistant", sub: "Timings, appointments and after-treatment care",
    hello: "Namaste! I can help with clinic timings, booking an appointment, directions and care after your treatment. What would you like to know?",
    placeholder: "Type your question…", send: "Send", aftercare: "After-treatment care", back: "← Main topics",
    pickTreatment: "Which treatment did you have?", notFound: "Sorry, I don't have an answer for that. Please call or WhatsApp the clinic on +91 99088 94449.",
    note: "General instructions only. Always follow your doctor's advice. In an emergency, call the clinic or 108.",
    thinking: "Typing…", call: "Call", whatsapp: "WhatsApp", open: "Chat with us", close: "Close chat", teaser: "Hi! Need help with timings, booking or after-care?", bookForm: "Open the booking form", maps: "Open in Google Maps",
    aiOff: "Choose a topic below, or type a few words (for example: timings, extraction, braces).",
  },
  te: {
    title: "క్లినిక్ సహాయకుడు", sub: "సమయాలు, అపాయింట్‌మెంట్లు, చికిత్స తర్వాత జాగ్రత్తలు",
    hello: "నమస్తే! క్లినిక్ సమయాలు, అపాయింట్‌మెంట్ బుకింగ్, దారి, చికిత్స తర్వాత జాగ్రత్తల గురించి సహాయం చేయగలను. మీకు ఏమి తెలుసుకోవాలి?",
    placeholder: "మీ ప్రశ్న టైప్ చేయండి…", send: "పంపండి", aftercare: "చికిత్స తర్వాత జాగ్రత్తలు", back: "← ప్రధాన విషయాలు",
    pickTreatment: "మీకు ఏ చికిత్స జరిగింది?", notFound: "క్షమించండి, దీనికి నా దగ్గర సమాధానం లేదు. దయచేసి క్లినిక్‌కు +91 99088 94449 కు కాల్ లేదా వాట్సాప్ చేయండి.",
    note: "ఇవి సాధారణ సూచనలు మాత్రమే. ఎల్లప్పుడూ డాక్టర్ సలహా పాటించండి. అత్యవసరమైతే క్లినిక్‌కు లేదా 108 కు కాల్ చేయండి.",
    thinking: "టైప్ చేస్తోంది…", call: "కాల్", whatsapp: "వాట్సాప్", open: "మాతో చాట్ చేయండి", close: "చాట్ మూసివేయండి", teaser: "నమస్తే! సమయాలు, బుకింగ్ లేదా చికిత్స తర్వాత జాగ్రత్తల గురించి అడగండి.", bookForm: "బుకింగ్ ఫారమ్ తెరవండి", maps: "గూగుల్ మ్యాప్స్‌లో తెరవండి",
    aiOff: "క్రింద ఒక విషయం ఎంచుకోండి, లేదా కొన్ని పదాలు టైప్ చేయండి (ఉదా: సమయాలు, పన్ను తీయడం, బ్రేసెస్).",
  },
  hi: {
    title: "क्लिनिक सहायक", sub: "समय, अपॉइंटमेंट और इलाज के बाद की देखभाल",
    hello: "नमस्ते! मैं क्लिनिक का समय, अपॉइंटमेंट बुकिंग, रास्ता और इलाज के बाद की देखभाल के बारे में मदद कर सकता हूँ। आप क्या जानना चाहते हैं?",
    placeholder: "अपना सवाल लिखें…", send: "भेजें", aftercare: "इलाज के बाद देखभाल", back: "← मुख्य विषय",
    pickTreatment: "आपका कौन-सा इलाज हुआ है?", notFound: "माफ़ कीजिए, इसका जवाब मेरे पास नहीं है। कृपया क्लिनिक को +91 99088 94449 पर कॉल या व्हाट्सऐप करें।",
    note: "ये केवल सामान्य निर्देश हैं। हमेशा डॉक्टर की सलाह मानें। आपात स्थिति में क्लिनिक या 108 पर कॉल करें।",
    thinking: "लिख रहा है…", call: "कॉल", whatsapp: "व्हाट्सऐप", open: "हमसे चैट करें", close: "चैट बंद करें", teaser: "नमस्ते! समय, बुकिंग या इलाज के बाद की देखभाल के बारे में पूछें।", bookForm: "बुकिंग फ़ॉर्म खोलें", maps: "गूगल मैप्स में खोलें",
    aiOff: "नीचे कोई विषय चुनें, या कुछ शब्द लिखें (जैसे: समय, दाँत निकालना, ब्रेसेस)।",
  },
};

/* group: "clinic" = main topics, "care" = after-treatment care */
export const TOPICS = [
  // ───────────── CLINIC ─────────────
  {
    id: "timings", group: "clinic",
    title: { en: "Clinic timings", te: "క్లినిక్ సమయాలు", hi: "क्लिनिक का समय" },
    keys: ["timing", "time", "open", "hours", "sunday", "holiday", "సమయ", "టైమ్", "ఆదివారం", "समय", "टाइम", "खुला", "रविवार", "samayam", "samay"],
    a: {
      en: ["• Monday to Saturday: 11:00 am – 7:00 pm", "• Sunday: holiday", "We see patients by appointment only, so please call or WhatsApp +91 99088 94449 before you come."],
      te: ["• సోమవారం నుండి శనివారం వరకు: ఉదయం 11:00 – సాయంత్రం 7:00", "• ఆదివారం: సెలవు", "అపాయింట్‌మెంట్ ద్వారా మాత్రమే చూస్తాము. రావడానికి ముందు +91 99088 94449 కు కాల్ లేదా వాట్సాప్ చేయండి."],
      hi: ["• सोमवार से शनिवार: सुबह 11:00 – शाम 7:00", "• रविवार: छुट्टी", "हम केवल अपॉइंटमेंट से मरीज़ देखते हैं, इसलिए आने से पहले +91 99088 94449 पर कॉल या व्हाट्सऐप करें।"],
    },
  },
  {
    id: "appointment", group: "clinic", action: "book",
    title: { en: "Book an appointment", te: "అపాయింట్‌మెంట్ బుక్ చేయండి", hi: "अपॉइंटमेंट बुक करें" },
    keys: ["appointment", "book", "booking", "slot", "visit", "consult", "అపాయింట్", "బుక్", "అపాయింట్‌మెంట్", "अपॉइंटमेंट", "बुक", "मिलना", "appointment kaavali"],
    a: {
      en: ["• Call or WhatsApp: +91 99088 94449", "• Or fill the “Book an appointment” form on this page — it sends your request on WhatsApp.", "The clinic will confirm a time with you. Timings: Mon–Sat, 11 am – 7 pm."],
      te: ["• కాల్ లేదా వాట్సాప్: +91 99088 94449", "• లేదా ఈ పేజీలోని “Book an appointment” ఫారమ్ నింపండి — అది మీ అభ్యర్థనను వాట్సాప్‌లో పంపుతుంది.", "క్లినిక్ మీకు సమయం నిర్ధారిస్తుంది. సమయాలు: సోమ–శని, ఉదయం 11 – సాయంత్రం 7."],
      hi: ["• कॉल या व्हाट्सऐप: +91 99088 94449", "• या इस पेज पर “Book an appointment” फ़ॉर्म भरें — यह आपका अनुरोध व्हाट्सऐप पर भेज देता है।", "क्लिनिक आपको समय पक्का करके बताएगा। समय: सोम–शनि, सुबह 11 – शाम 7।"],
    },
  },
  {
    id: "location", group: "clinic", action: "map",
    title: { en: "Address and directions", te: "చిరునామా, దారి", hi: "पता और रास्ता" },
    keys: ["address", "location", "where", "direction", "map", "metro", "reach", "చిరునామా", "ఎక్కడ", "దారి", "అడ్రస్", "पता", "कहाँ", "रास्ता", "मेट्रो", "ekkada", "kahan"],
    a: {
      en: ["G-15, Ground Floor, Rajanigandha Apartments,", "Opposite Metro Pillar No. 1563, Chaitanyapuri,", "Hyderabad – 500060 (near Dilsukhnagar).", "Google Maps: https://maps.app.goo.gl/F8Zp631MJP9MvKtk7"],
      te: ["G-15, గ్రౌండ్ ఫ్లోర్, రజనీగంధ అపార్ట్‌మెంట్స్,", "మెట్రో పిల్లర్ నం. 1563 ఎదురుగా, చైతన్యపురి,", "హైదరాబాద్ – 500060 (దిల్‌సుఖ్‌నగర్ దగ్గర).", "గూగుల్ మ్యాప్స్: https://maps.app.goo.gl/F8Zp631MJP9MvKtk7"],
      hi: ["G-15, ग्राउंड फ़्लोर, रजनीगंधा अपार्टमेंट्स,", "मेट्रो पिलर नं. 1563 के सामने, चैतन्यपुरी,", "हैदराबाद – 500060 (दिलसुखनगर के पास)।", "गूगल मैप्स: https://maps.app.goo.gl/F8Zp631MJP9MvKtk7"],
    },
  },
  {
    id: "fees", group: "clinic",
    title: { en: "Treatment cost", te: "చికిత్స ఖర్చు", hi: "इलाज का खर्च" },
    keys: ["cost", "fee", "fees", "price", "charge", "how much", "ఖర్చు", "ఫీజు", "ధర", "ఎంత", "खर्च", "फ़ीस", "फीस", "कीमत", "कितना", "entha", "kitna"],
    a: {
      en: ["The cost depends on the treatment your teeth need.", "The doctor examines you, explains the options and the cost clearly before any treatment starts.", "For a rough idea, please call +91 99088 94449."],
      te: ["ఖర్చు మీ పళ్ళకు అవసరమైన చికిత్సపై ఆధారపడి ఉంటుంది.", "డాక్టర్ పరీక్షించి, చికిత్స ప్రారంభించే ముందే అవకాశాలు, ఖర్చు స్పష్టంగా వివరిస్తారు.", "సుమారు అంచనా కోసం +91 99088 94449 కు కాల్ చేయండి."],
      hi: ["खर्च इस पर निर्भर करता है कि आपके दाँतों को कौन-सा इलाज चाहिए।", "डॉक्टर जाँच करके, इलाज शुरू करने से पहले विकल्प और खर्च साफ़-साफ़ बताते हैं।", "अनुमान के लिए +91 99088 94449 पर कॉल करें।"],
    },
  },
  {
    id: "doctor", group: "clinic",
    title: { en: "About the doctor", te: "డాక్టర్ గురించి", hi: "डॉक्टर के बारे में" },
    keys: ["doctor", "dentist", "rama raju", "qualification", "mds", "డాక్టర్", "రామరాజు", "डॉक्टर", "रामराजू"],
    a: {
      en: ["Dr. D. Rama Raju — BDS, MDS, Osmania Medical College, Hyderabad.", `• ${YEARS} years of experience · clinic running since ${SINCE}`, "• Dental Council Reg. No. A-1096", "• Member, Indian Dental Association"],
      te: ["డా. డి. రామరాజు — BDS, MDS, ఉస్మానియా మెడికల్ కాలేజ్, హైదరాబాద్.", `• ${YEARS} సంవత్సరాల అనుభవం · ${SINCE} నుండి క్లినిక్ సేవలు`, "• డెంటల్ కౌన్సిల్ రిజిస్ట్రేషన్ నం. A-1096", "• ఇండియన్ డెంటల్ అసోసియేషన్ సభ్యులు"],
      hi: ["डॉ. डी. रामराजू — BDS, MDS, उस्मानिया मेडिकल कॉलेज, हैदराबाद।", `• ${YEARS} साल का अनुभव · ${SINCE} से क्लिनिक सेवा में`, "• डेंटल काउंसिल रजिस्ट्रेशन नं. A-1096", "• इंडियन डेंटल एसोसिएशन के सदस्य"],
    },
  },
  {
    id: "emergency", group: "clinic", urgent: true,
    title: { en: "Emergency / when to call", te: "అత్యవసరం / ఎప్పుడు కాల్ చేయాలి", hi: "आपात स्थिति / कब कॉल करें" },
    keys: ["emergency", "urgent", "bleeding", "blood", "swelling", "fever", "pain", "knocked", "breath", "అత్యవసర", "రక్తం", "వాపు", "నొప్పి", "జ్వరం", "आपात", "खून", "सूजन", "दर्द", "बुखार", "noppi", "dard", "khoon"],
    a: {
      en: ["Call the clinic now (+91 99088 94449) if:", "• bleeding does not stop after 30–45 minutes of firm pressure on gauze", "• pain or swelling keeps increasing after the 3rd day, or you have fever", "• a tooth is knocked out (keep it in milk and come immediately)", "Go to the nearest hospital or call 108 at once if there is difficulty breathing or swallowing, or swelling spreading to the eye or neck."],
      te: ["ఇలా ఉంటే వెంటనే క్లినిక్‌కు కాల్ చేయండి (+91 99088 94449):", "• గాజ్‌పై గట్టిగా 30–45 నిమిషాలు నొక్కినా రక్తం ఆగకపోతే", "• 3వ రోజు తర్వాత కూడా నొప్పి లేదా వాపు పెరుగుతుంటే, లేదా జ్వరం ఉంటే", "• పన్ను పూర్తిగా ఊడిపోతే (పాలలో ఉంచి వెంటనే రండి)", "శ్వాస తీసుకోవడం లేదా మింగడం కష్టంగా ఉంటే, లేదా వాపు కన్ను/మెడ వరకు వ్యాపిస్తే వెంటనే దగ్గరి ఆసుపత్రికి వెళ్ళండి లేదా 108 కు కాల్ చేయండి."],
      hi: ["इन हालात में तुरंत क्लिनिक को कॉल करें (+91 99088 94449):", "• गॉज़ पर 30–45 मिनट कसकर दबाने पर भी खून न रुके", "• तीसरे दिन के बाद भी दर्द या सूजन बढ़ती रहे, या बुखार हो", "• दाँत पूरा निकल जाए (उसे दूध में रखकर तुरंत आएँ)", "साँस लेने या निगलने में तकलीफ़ हो, या सूजन आँख/गर्दन तक फैले तो तुरंत नज़दीकी अस्पताल जाएँ या 108 पर कॉल करें।"],
    },
  },
  {
    id: "portal", group: "clinic",
    title: { en: "See my records online", te: "నా రికార్డులు ఆన్‌లైన్‌లో", hi: "मेरे रिकॉर्ड ऑनलाइन" },
    keys: ["record", "report", "x-ray", "xray", "prescription", "portal", "login", "రికార్డ్", "రిపోర్ట్", "ఎక్స్‌రే", "रिकॉर्ड", "रिपोर्ट", "एक्स-रे", "पर्चा"],
    a: {
      en: ["When the doctor shares them, you can see your visit summary, prescriptions, X-rays and receipts online.", "• Tap “Patient login” at the top of this website", "• Enter your registered mobile number and the SMS code", "If you cannot log in, ask at the reception."],
      te: ["డాక్టర్ షేర్ చేసినప్పుడు, మీ విజిట్ సారాంశం, ప్రిస్క్రిప్షన్లు, ఎక్స్‌రేలు, రసీదులు ఆన్‌లైన్‌లో చూడవచ్చు.", "• ఈ వెబ్‌సైట్ పైభాగంలో “Patient login” నొక్కండి", "• మీ రిజిస్టర్ అయిన మొబైల్ నంబర్, SMS కోడ్ ఇవ్వండి", "లాగిన్ కాకపోతే రిసెప్షన్‌లో అడగండి."],
      hi: ["जब डॉक्टर शेयर करते हैं, तब आप अपनी विज़िट का सार, पर्चे, एक्स-रे और रसीदें ऑनलाइन देख सकते हैं।", "• इस वेबसाइट के ऊपर “Patient login” दबाएँ", "• अपना रजिस्टर्ड मोबाइल नंबर और SMS कोड डालें", "लॉगिन न हो तो रिसेप्शन पर पूछें।"],
    },
  },

  // ───────────── AFTER-TREATMENT CARE ─────────────
  {
    id: "extraction", group: "care",
    title: { en: "Tooth extraction", te: "పన్ను తీయించిన తర్వాత", hi: "दाँत निकलवाने के बाद" },
    keys: ["extraction", "removed", "pulled", "socket", "tooth out", "పన్ను తీ", "పీకి", "दाँत निकाल", "दांत निकाल", "pannu", "daant nikal"],
    a: {
      en: ["• Bite firmly on the gauze; change it every 45 minutes until bleeding stops. If it continues, bite on a moist tea bag.", "• Ice pack on the cheek for the first 24–36 hours.", "• Soft food and plenty of fluids for a few days.", "• Take the medicines exactly as prescribed, for the full number of days.", "• From the next day: warm salt-water rinses 4–5 times a day.", "Do not: smoke for 24 hours, spit, rinse or use a straw for 24 hours, chew hard food on that side for 6–8 weeks, touch the area with tongue or fingers, or do heavy exercise that day."],
      te: ["• గాజ్‌ను గట్టిగా కొరికి పట్టుకోండి; రక్తం ఆగే వరకు ప్రతి 45 నిమిషాలకు మార్చండి. ఆగకపోతే తడి టీ బ్యాగ్ కొరకండి.", "• మొదటి 24–36 గంటలు బుగ్గపై ఐస్ ప్యాక్ పెట్టండి.", "• కొన్ని రోజులు మెత్తని ఆహారం, ఎక్కువ ద్రవాలు తీసుకోండి.", "• మందులు డాక్టర్ చెప్పినట్లే, పూర్తి రోజులు వాడండి.", "• మరుసటి రోజు నుండి: గోరువెచ్చని ఉప్పు నీటితో రోజుకు 4–5 సార్లు పుక్కిలించండి.", "చేయకూడనివి: 24 గంటలు పొగ తాగడం, ఉమ్మడం, పుక్కిలించడం, స్ట్రా వాడడం; 6–8 వారాలు ఆ వైపు గట్టి ఆహారం నమలడం; నాలుక/వేలితో తాకడం; ఆ రోజు ఎక్కువ శ్రమ."],
      hi: ["• गॉज़ को कसकर दबाए रखें; खून रुकने तक हर 45 मिनट पर बदलें। फिर भी न रुके तो गीली टी-बैग दबाएँ।", "• पहले 24–36 घंटे गाल पर बर्फ़ की सिकाई करें।", "• कुछ दिन नरम खाना और खूब तरल लें।", "• दवाइयाँ ठीक वैसे ही, पूरे दिनों तक लें जैसे डॉक्टर ने लिखी हैं।", "• अगले दिन से: गुनगुने नमक-पानी से दिन में 4–5 बार कुल्ला करें।", "न करें: 24 घंटे धूम्रपान, थूकना, कुल्ला करना या स्ट्रॉ से पीना; 6–8 हफ़्ते उस तरफ़ सख़्त चीज़ चबाना; जीभ या उँगली से छूना; उस दिन भारी मेहनत।"],
    },
  },
  {
    id: "wisdom", group: "care",
    title: { en: "Wisdom tooth surgery", te: "జ్ఞాన దంతం శస్త్రచికిత్స", hi: "अक़्ल दाढ़ की सर्जरी" },
    keys: ["wisdom", "impacted", "third molar", "surgical extraction", "జ్ఞాన దంత", "విజ్డమ్", "अक्ल", "अक़्ल", "विज़डम"],
    a: {
      en: ["Follow all the tooth-extraction instructions, and also:", "• Swelling and jaw stiffness usually increase for 2–3 days, then settle. Ice packs in the first 24–36 hours; warm compresses after 48 hours.", "• Opening the mouth may be limited for a few days.", "• Stitches are removed after about 7 days (some dissolve).", "Call the clinic if bleeding does not stop, swelling keeps increasing after day 3, you get fever, a bad taste with throbbing pain, or numbness that does not go away."],
      te: ["పన్ను తీసిన తర్వాతి సూచనలన్నీ పాటించండి, ఇంకా:", "• వాపు, దవడ బిగుసుకుపోవడం 2–3 రోజులు పెరిగి తర్వాత తగ్గుతాయి. మొదటి 24–36 గంటలు ఐస్; 48 గంటల తర్వాత వెచ్చని కాపడం.", "• కొన్ని రోజులు నోరు పూర్తిగా తెరవడం కష్టంగా ఉండవచ్చు.", "• కుట్లు సుమారు 7 రోజుల తర్వాత తీస్తారు (కొన్ని వాటంతటవే కరుగుతాయి).", "రక్తం ఆగకపోయినా, 3వ రోజు తర్వాత వాపు పెరుగుతున్నా, జ్వరం, దుర్వాసనతో కొట్టుకునే నొప్పి, లేదా తగ్గని తిమ్మిరి ఉంటే క్లినిక్‌కు కాల్ చేయండి."],
      hi: ["दाँत निकलवाने के बाद के सभी निर्देश मानें, और साथ ही:", "• सूजन और जबड़े की जकड़न 2–3 दिन बढ़ती है, फिर कम होती है। पहले 24–36 घंटे बर्फ़; 48 घंटे बाद गर्म सिकाई।", "• कुछ दिन मुँह पूरा खोलने में दिक्कत हो सकती है।", "• टाँके लगभग 7 दिन बाद निकाले जाते हैं (कुछ अपने आप घुल जाते हैं)।", "खून न रुके, तीसरे दिन के बाद सूजन बढ़े, बुखार हो, बदबू के साथ धड़कता दर्द हो, या सुन्नपन न जाए तो क्लिनिक को कॉल करें।"],
    },
  },
  {
    id: "rct", group: "care",
    title: { en: "Root canal treatment", te: "రూట్ కెనాల్ చికిత్స", hi: "रूट कैनाल इलाज" },
    keys: ["root canal", "rct", "endo", "రూట్ కెనాల్", "ఆర్‌సిటి", "रूट कैनाल", "आरसीटी"],
    a: {
      en: ["• Do not chew until the numbness wears off (about 1 hour upper jaw, up to 4 hours lower jaw); avoid hot food and drinks until then.", "• Some discomfort for a few days, especially when chewing, is normal. Take the medicines as prescribed and finish the antibiotics.", "• Avoid sticky and hard food; chew on the other side to protect the temporary filling.", "• If the whole temporary filling or crown comes out, contact the clinic.", "• A root-canal-treated tooth becomes brittle — get the crown done soon, or the tooth may break.", "Call if severe pain or pressure lasts more than a few days."],
      te: ["• తిమ్మిరి తగ్గే వరకు నమలకండి (పై దవడ సుమారు 1 గంట, కింది దవడ 4 గంటల వరకు); అప్పటి వరకు వేడి ఆహారం, పానీయాలు వద్దు.", "• కొన్ని రోజులు, ముఖ్యంగా నమిలేటప్పుడు, కొంచెం నొప్పి సాధారణం. మందులు చెప్పినట్లు వాడి, యాంటీబయాటిక్స్ పూర్తి చేయండి.", "• తాత్కాలిక ఫిల్లింగ్‌ను కాపాడడానికి జిగట, గట్టి ఆహారం మానండి; మరో వైపు నమలండి.", "• తాత్కాలిక ఫిల్లింగ్ లేదా క్రౌన్ పూర్తిగా ఊడిపోతే క్లినిక్‌ను సంప్రదించండి.", "• రూట్ కెనాల్ చేసిన పన్ను పెళుసుగా మారుతుంది — త్వరగా క్రౌన్ వేయించుకోండి, లేకపోతే పన్ను విరగవచ్చు.", "తీవ్రమైన నొప్పి కొన్ని రోజులకు మించి ఉంటే కాల్ చేయండి."],
      hi: ["• सुन्नपन जाने तक न चबाएँ (ऊपरी जबड़ा लगभग 1 घंटा, निचला 4 घंटे तक); तब तक गर्म खाना-पीना नहीं।", "• कुछ दिन, खासकर चबाते समय, हल्का दर्द सामान्य है। दवाइयाँ लिखे अनुसार लें और एंटीबायोटिक पूरी करें।", "• अस्थायी फ़िलिंग बचाने के लिए चिपचिपी और सख़्त चीज़ें न खाएँ; दूसरी तरफ़ से चबाएँ।", "• पूरी अस्थायी फ़िलिंग या क्राउन निकल जाए तो क्लिनिक से संपर्क करें।", "• रूट कैनाल वाला दाँत कमज़ोर हो जाता है — जल्दी क्राउन लगवाएँ, वरना दाँत टूट सकता है।", "तेज़ दर्द कुछ दिनों से ज़्यादा रहे तो कॉल करें।"],
    },
  },
  {
    id: "composite", group: "care",
    title: { en: "Tooth-coloured filling", te: "పన్ను రంగు ఫిల్లింగ్", hi: "दाँत के रंग की फ़िलिंग" },
    keys: ["composite", "tooth colour", "tooth color", "white filling", "bonding", "filling", "gic", "ఫిల్లింగ్", "కంపోజిట్", "फ़िलिंग", "फिलिंग", "कंपोजिट"],
    a: {
      en: ["• Avoid heavy chewing on the new filling for 24 hours.", "• Tea, coffee and tobacco can stain it over time; daily brushing and flossing reduce this.", "• Decay can still start at the edges — clean well every day.", "• If a small piece chips off, it can usually be repaired. Come for regular check-ups.", "• Mild sensitivity to hot and cold for a few days is common; call if it gets worse."],
      te: ["• కొత్త ఫిల్లింగ్‌పై 24 గంటలు గట్టిగా నమలకండి.", "• టీ, కాఫీ, పొగాకు వల్ల కాలక్రమేణా మరకలు పడవచ్చు; రోజూ బ్రష్, ఫ్లాస్ చేస్తే తగ్గుతాయి.", "• అంచుల దగ్గర మళ్ళీ పిప్పి రావచ్చు — రోజూ బాగా శుభ్రం చేయండి.", "• చిన్న ముక్క విరిగితే సాధారణంగా సరిచేయవచ్చు. క్రమం తప్పకుండా చెకప్‌కు రండి.", "• కొన్ని రోజులు వేడి/చల్లటికి కొంచెం జివ్వుమనడం సాధారణం; ఎక్కువైతే కాల్ చేయండి."],
      hi: ["• नई फ़िलिंग पर 24 घंटे ज़ोर से न चबाएँ।", "• चाय, कॉफ़ी और तंबाकू से समय के साथ दाग़ लग सकते हैं; रोज़ ब्रश और फ़्लॉस करने से कम होते हैं।", "• किनारों पर फिर से कीड़ा लग सकता है — रोज़ अच्छी सफ़ाई करें।", "• छोटा टुकड़ा टूट जाए तो आमतौर पर ठीक हो जाता है। नियमित जाँच के लिए आएँ।", "• कुछ दिन ठंडा-गरम लगना सामान्य है; बढ़े तो कॉल करें।"],
    },
  },
  {
    id: "amalgam", group: "care",
    title: { en: "Silver (amalgam) filling", te: "సిల్వర్ ఫిల్లింగ్", hi: "सिल्वर फ़िलिंग" },
    keys: ["amalgam", "silver filling", "metal filling", "సిల్వర్", "అమాల్గమ్", "सिल्वर", "अमलगम"],
    a: {
      en: ["• The filling hardens over 24 hours — chew on the other side until tomorrow.", "• If the bite feels high, call soon to get it adjusted, otherwise the tooth can get sore.", "• Sensitivity to hot and cold is common and settles gradually. Pain that starts on its own may mean the nerve is affected — please call.", "• Avoid biting very hard things (ice, bones, hard candy).", "• Keep the edges clean with daily brushing and flossing."],
      te: ["• ఫిల్లింగ్ 24 గంటల్లో గట్టిపడుతుంది — రేపటి వరకు మరో వైపు నమలండి.", "• కొరికితే ఎత్తుగా అనిపిస్తే త్వరగా కాల్ చేసి సరిచేయించుకోండి, లేకపోతే పన్ను నొప్పిగా మారవచ్చు.", "• వేడి/చల్లటికి జివ్వుమనడం సాధారణం, మెల్లగా తగ్గుతుంది. దానంతటదే వచ్చే నొప్పి నరం ప్రభావితమైందని సూచించవచ్చు — కాల్ చేయండి.", "• చాలా గట్టివి (ఐస్, ఎముకలు, గట్టి మిఠాయిలు) కొరకకండి.", "• రోజూ బ్రష్, ఫ్లాస్‌తో అంచులు శుభ్రంగా ఉంచండి."],
      hi: ["• फ़िलिंग 24 घंटे में सख़्त होती है — कल तक दूसरी तरफ़ से चबाएँ।", "• काटने पर ऊँचा लगे तो जल्दी कॉल करके ठीक करवाएँ, वरना दाँत में दर्द हो सकता है।", "• ठंडा-गरम लगना आम है और धीरे-धीरे ठीक होता है। अपने आप दर्द शुरू हो तो नस प्रभावित हो सकती है — कॉल करें।", "• बहुत सख़्त चीज़ें (बर्फ़, हड्डी, सख़्त टॉफ़ी) न काटें।", "• रोज़ ब्रश और फ़्लॉस से किनारे साफ़ रखें।"],
    },
  },
  {
    id: "crownprep", group: "care",
    title: { en: "Temporary crown (after tooth preparation)", te: "తాత్కాలిక క్రౌన్", hi: "अस्थायी क्राउन" },
    keys: ["temporary crown", "temporary cap", "crown preparation", "tooth cutting", "crown cutting", "తాత్కాలిక క్రౌన్", "టెంపరరీ", "अस्थायी क्राउन", "टेम्पररी"],
    a: {
      en: ["• Do not chew until the numbness wears off.", "• Some sensitivity and gum soreness is normal until the final crown is fitted.", "• Avoid hard or sticky food (nuts, toffee, chewing gum, popcorn, raw carrot, biting apples).", "• If the temporary comes off, try to put it back and call the clinic to re-cement it.", "• Brush normally at least 3 times a day; when flossing, slide the floss out from the side instead of pulling it up.", "Call if the bite feels uneven or the pain persists."],
      te: ["• తిమ్మిరి తగ్గే వరకు నమలకండి.", "• శాశ్వత క్రౌన్ పెట్టే వరకు కొంచెం జివ్వుమనడం, చిగుళ్ళ నొప్పి సాధారణం.", "• గట్టి లేదా జిగట ఆహారం (గింజలు, టాఫీ, చూయింగ్ గమ్, పాప్‌కార్న్, పచ్చి క్యారెట్, ఆపిల్ కొరకడం) మానండి.", "• తాత్కాలిక క్రౌన్ ఊడితే తిరిగి పెట్టడానికి ప్రయత్నించి, మళ్ళీ అతికించడానికి క్లినిక్‌కు కాల్ చేయండి.", "• రోజుకు కనీసం 3 సార్లు బ్రష్ చేయండి; ఫ్లాస్ చేసేటప్పుడు పైకి లాగకుండా పక్కనుంచి బయటకు తీయండి.", "కొరికితే అసమానంగా ఉన్నా, నొప్పి తగ్గకపోయినా కాల్ చేయండి."],
      hi: ["• सुन्नपन जाने तक न चबाएँ।", "• पक्का क्राउन लगने तक थोड़ी सेंसिटिविटी और मसूड़ों में दर्द सामान्य है।", "• सख़्त या चिपचिपी चीज़ें (मेवे, टॉफ़ी, च्युइंग गम, पॉपकॉर्न, कच्ची गाजर, सेब काटना) न खाएँ।", "• अस्थायी क्राउन निकल जाए तो उसे वापस लगाने की कोशिश करें और दोबारा चिपकाने के लिए क्लिनिक को कॉल करें।", "• दिन में कम से कम 3 बार ब्रश करें; फ़्लॉस ऊपर खींचने की बजाय बगल से बाहर निकालें।", "काटने पर असमान लगे या दर्द बना रहे तो कॉल करें।"],
    },
  },
  {
    id: "crown", group: "care",
    title: { en: "Crown or bridge fitted", te: "క్రౌన్ / బ్రిడ్జ్ అమర్చిన తర్వాత", hi: "क्राउन / ब्रिज लगने के बाद" },
    keys: ["crown", "cap", "bridge", "fpd", "క్రౌన్", "క్యాప్", "బ్రిడ్జ్", "क्राउन", "कैप", "ब्रिज"],
    a: {
      en: ["• Do not chew on the new crown or bridge for the first 24 hours while the cement hardens.", "• Sensitivity to hot and cold can last days or a few weeks; visit if it continues.", "• If the bite feels uncomfortable, call so it can be adjusted.", "• Avoid very sticky or very hard food (ice, hard candy, raw carrot). If the crown comes off, bring it with you.", "• Brush and floss around it daily; check-ups at least twice a year (3 times if you have gum disease)."],
      te: ["• సిమెంట్ గట్టిపడే వరకు మొదటి 24 గంటలు కొత్త క్రౌన్/బ్రిడ్జ్‌పై నమలకండి.", "• వేడి/చల్లటికి జివ్వుమనడం కొన్ని రోజులు లేదా వారాలు ఉండవచ్చు; తగ్గకపోతే రండి.", "• కొరికితే అసౌకర్యంగా ఉంటే సరిచేయడానికి కాల్ చేయండి.", "• బాగా జిగట లేదా బాగా గట్టి ఆహారం (ఐస్, గట్టి మిఠాయి, పచ్చి క్యారెట్) మానండి. క్రౌన్ ఊడితే దాన్ని తీసుకుని రండి.", "• రోజూ దాని చుట్టూ బ్రష్, ఫ్లాస్ చేయండి; ఏడాదికి కనీసం 2 సార్లు చెకప్ (చిగుళ్ళ వ్యాధి ఉంటే 3 సార్లు)."],
      hi: ["• सीमेंट सख़्त होने तक पहले 24 घंटे नए क्राउन/ब्रिज पर न चबाएँ।", "• ठंडा-गरम लगना कुछ दिन या हफ़्ते रह सकता है; बना रहे तो दिखाएँ।", "• काटने पर असहज लगे तो ठीक करवाने के लिए कॉल करें।", "• बहुत चिपचिपी या बहुत सख़्त चीज़ें (बर्फ़, सख़्त टॉफ़ी, कच्ची गाजर) न खाएँ। क्राउन निकल जाए तो साथ लेकर आएँ।", "• रोज़ उसके आसपास ब्रश और फ़्लॉस करें; साल में कम से कम 2 बार जाँच (मसूड़ों की बीमारी हो तो 3 बार)।"],
    },
  },
  {
    id: "scaling", group: "care",
    title: { en: "Scaling / cleaning", te: "స్కేలింగ్ / క్లీనింగ్", hi: "स्केलिंग / सफ़ाई" },
    keys: ["scaling", "cleaning", "prophylaxis", "tartar", "gums bleeding", "స్కేలింగ్", "క్లీనింగ్", "గార", "स्केलिंग", "सफ़ाई", "सफाई", "टार्टर"],
    a: {
      en: ["• Mild discomfort and swelling may occur for a short time.", "• Avoid crunchy, spicy or very hot food for 24 hours.", "• Warm salt-water rinses (½ teaspoon salt in a glass of warm water) help healing.", "• Sensitivity to hot and cold is common and settles in a few weeks; ask us about a sensitivity toothpaste if it continues.", "• As the gums heal, a little more of the tooth may show — this is normal.", "• Brush and floss daily; check-up after about 4 weeks, then every 6 months."],
      te: ["• కొంతసేపు కొంచెం అసౌకర్యం, వాపు ఉండవచ్చు.", "• 24 గంటలు కరకరలాడే, కారం, బాగా వేడి ఆహారం మానండి.", "• గోరువెచ్చని ఉప్పు నీరు (ఒక గ్లాసులో అర చెంచా ఉప్పు) పుక్కిలిస్తే త్వరగా నయమవుతుంది.", "• వేడి/చల్లటికి జివ్వుమనడం సాధారణం, కొన్ని వారాల్లో తగ్గుతుంది; తగ్గకపోతే సెన్సిటివిటీ టూత్‌పేస్ట్ గురించి అడగండి.", "• చిగుళ్ళు నయమయ్యే కొద్దీ పన్ను కొంచెం ఎక్కువగా కనిపించవచ్చు — ఇది సాధారణం.", "• రోజూ బ్రష్, ఫ్లాస్ చేయండి; సుమారు 4 వారాల తర్వాత, ఆపై ప్రతి 6 నెలలకు చెకప్."],
      hi: ["• थोड़ी देर हल्की असुविधा और सूजन हो सकती है।", "• 24 घंटे कुरकुरा, मसालेदार या बहुत गर्म खाना न खाएँ।", "• गुनगुने नमक-पानी (एक गिलास में आधा चम्मच नमक) से कुल्ला करने से जल्दी आराम मिलता है।", "• ठंडा-गरम लगना आम है और कुछ हफ़्तों में ठीक होता है; बना रहे तो सेंसिटिविटी टूथपेस्ट के बारे में पूछें।", "• मसूड़े ठीक होने पर दाँत थोड़ा ज़्यादा दिख सकता है — यह सामान्य है।", "• रोज़ ब्रश और फ़्लॉस करें; लगभग 4 हफ़्ते बाद, फिर हर 6 महीने जाँच।"],
    },
  },
  {
    id: "gumsurgery", group: "care",
    title: { en: "Gum (flap) surgery / laser gum treatment", te: "చిగుళ్ళ (ఫ్లాప్) శస్త్రచికిత్స", hi: "मसूड़ों की (फ़्लैप) सर्जरी" },
    keys: ["flap", "gum surgery", "periodontal surgery", "curettage", "laser gum", "చిగుళ్ళ సర్జరీ", "ఫ్లాప్", "मसूड़ों की सर्जरी", "फ़्लैप", "फ्लैप"],
    a: {
      en: ["• Some swelling, mild bleeding and discomfort for a few days is normal; ice pack for the first 24 hours.", "• If a gum dressing was placed, do not disturb it.", "• Soft, lukewarm, non-spicy food; do not chew on the treated side.", "• Do not brush the operated area until the doctor says; clean the rest of the mouth normally and use the prescribed mouthwash.", "• No smoking, alcohol, straws or strong rinsing for at least 48 hours (no smoking for 2 weeks is best).", "• Stitches are removed after 7–10 days; gum check-ups every 3–6 months."],
      te: ["• కొన్ని రోజులు కొంచెం వాపు, స్వల్ప రక్తస్రావం, అసౌకర్యం సాధారణం; మొదటి 24 గంటలు ఐస్ ప్యాక్.", "• చిగుళ్ళపై డ్రెస్సింగ్ పెడితే దాన్ని కదిలించకండి.", "• మెత్తని, గోరువెచ్చని, కారం లేని ఆహారం; చికిత్స చేసిన వైపు నమలకండి.", "• డాక్టర్ చెప్పే వరకు ఆపరేషన్ చేసిన చోట బ్రష్ చేయకండి; మిగతా నోరు మామూలుగా శుభ్రం చేసి, సూచించిన మౌత్‌వాష్ వాడండి.", "• కనీసం 48 గంటలు పొగ, మద్యం, స్ట్రా, గట్టిగా పుక్కిలించడం వద్దు (2 వారాలు పొగ తాగకపోవడం ఉత్తమం).", "• కుట్లు 7–10 రోజుల తర్వాత తీస్తారు; ప్రతి 3–6 నెలలకు చిగుళ్ళ చెకప్."],
      hi: ["• कुछ दिन थोड़ी सूजन, हल्का खून और असुविधा सामान्य है; पहले 24 घंटे बर्फ़ की सिकाई।", "• मसूड़ों पर ड्रेसिंग लगी हो तो उसे न छेड़ें।", "• नरम, गुनगुना, बिना मसाले का खाना; इलाज वाली तरफ़ न चबाएँ।", "• डॉक्टर के कहने तक ऑपरेशन वाली जगह ब्रश न करें; बाकी मुँह सामान्य रूप से साफ़ करें और बताया गया माउथवॉश इस्तेमाल करें।", "• कम से कम 48 घंटे धूम्रपान, शराब, स्ट्रॉ या ज़ोर से कुल्ला नहीं (2 हफ़्ते धूम्रपान न करना सबसे अच्छा)।", "• टाँके 7–10 दिन बाद निकलते हैं; हर 3–6 महीने मसूड़ों की जाँच।"],
    },
  },
  {
    id: "biopsy", group: "care",
    title: { en: "Biopsy", te: "బయాప్సీ తర్వాత", hi: "बायोप्सी के बाद" },
    keys: ["biopsy", "excision", "బయాప్సీ", "बायोप्सी"],
    a: {
      en: ["• Bite on the gauze; change every 45 minutes until bleeding stops.", "• Ice pack for the first 24–36 hours; soft food and plenty of fluids.", "• Medicines exactly as prescribed; warm salt-water rinses 4–5 times a day from the next day.", "• Do not smoke, spit, rinse or use a straw for 24 hours; do not touch the area; rest for the day.", "The doctor will explain the biopsy report at your follow-up visit."],
      te: ["• గాజ్ కొరికి పట్టుకోండి; రక్తం ఆగే వరకు ప్రతి 45 నిమిషాలకు మార్చండి.", "• మొదటి 24–36 గంటలు ఐస్ ప్యాక్; మెత్తని ఆహారం, ఎక్కువ ద్రవాలు.", "• మందులు చెప్పినట్లే వాడండి; మరుసటి రోజు నుండి రోజుకు 4–5 సార్లు గోరువెచ్చని ఉప్పు నీటి పుక్కిలింపు.", "• 24 గంటలు పొగ తాగడం, ఉమ్మడం, పుక్కిలించడం, స్ట్రా వద్దు; ఆ చోటు తాకకండి; ఆ రోజు విశ్రాంతి తీసుకోండి.", "బయాప్సీ రిపోర్ట్‌ను డాక్టర్ ఫాలో-అప్‌లో వివరిస్తారు."],
      hi: ["• गॉज़ दबाए रखें; खून रुकने तक हर 45 मिनट पर बदलें।", "• पहले 24–36 घंटे बर्फ़ की सिकाई; नरम खाना और खूब तरल।", "• दवाइयाँ लिखे अनुसार लें; अगले दिन से दिन में 4–5 बार गुनगुने नमक-पानी से कुल्ला।", "• 24 घंटे धूम्रपान, थूकना, कुल्ला या स्ट्रॉ नहीं; जगह को न छुएँ; उस दिन आराम करें।", "बायोप्सी रिपोर्ट डॉक्टर फ़ॉलो-अप में समझाएँगे।"],
    },
  },
  {
    id: "implant", group: "care",
    title: { en: "Dental implant surgery", te: "ఇంప్లాంట్ శస్త్రచికిత్స", hi: "इम्प्लांट सर्जरी" },
    keys: ["implant", "ఇంప్లాంట్", "इम्प्लांट", "इंप्लांट"],
    a: {
      en: ["• Bite on the gauze for 30–45 minutes; slight oozing on the first day is normal.", "• Ice packs for 24–36 hours (15–20 minutes on, 10 off).", "• Soft, cool food for a few days; chew on the other side. No rinsing, spitting or straws for 24 hours, then gentle salt-water rinses.", "• Do not smoke for at least 2 weeks — smoking can stop the implant joining the bone.", "• Medicines exactly as prescribed; do not press on the area or wear a denture over it unless the doctor allows.", "• Stitches after 7–10 days; the implant heals about 3 months before the crown. Clean around the final crown daily and come for check-ups every 6 months."],
      te: ["• గాజ్‌ను 30–45 నిమిషాలు కొరికి పట్టుకోండి; మొదటి రోజు కొద్దిగా రక్తం కారడం సాధారణం.", "• 24–36 గంటలు ఐస్ ప్యాక్ (15–20 నిమిషాలు పెట్టి, 10 నిమిషాలు తీసేయండి).", "• కొన్ని రోజులు మెత్తని, చల్లని ఆహారం; మరో వైపు నమలండి. 24 గంటలు పుక్కిలించడం, ఉమ్మడం, స్ట్రా వద్దు; తర్వాత మెల్లగా ఉప్పు నీటి పుక్కిలింపు.", "• కనీసం 2 వారాలు పొగ తాగకండి — పొగ వల్ల ఇంప్లాంట్ ఎముకతో కలవకపోవచ్చు.", "• మందులు చెప్పినట్లే వాడండి; ఆ చోటుపై నొక్కకండి, డాక్టర్ అనుమతి లేకుండా దానిపై కట్టుడు పళ్ళు పెట్టకండి.", "• 7–10 రోజుల్లో కుట్లు; క్రౌన్‌కు ముందు ఇంప్లాంట్ సుమారు 3 నెలలు నయమవుతుంది. తుది క్రౌన్ చుట్టూ రోజూ శుభ్రం చేసి, ప్రతి 6 నెలలకు చెకప్‌కు రండి."],
      hi: ["• गॉज़ 30–45 मिनट दबाए रखें; पहले दिन थोड़ा रिसना सामान्य है।", "• 24–36 घंटे बर्फ़ की सिकाई (15–20 मिनट लगाएँ, 10 मिनट हटाएँ)।", "• कुछ दिन नरम, ठंडा खाना; दूसरी तरफ़ से चबाएँ। 24 घंटे कुल्ला, थूकना या स्ट्रॉ नहीं, फिर हल्के नमक-पानी से कुल्ला।", "• कम से कम 2 हफ़्ते धूम्रपान न करें — इससे इम्प्लांट हड्डी से नहीं जुड़ पाता।", "• दवाइयाँ लिखे अनुसार लें; जगह पर न दबाएँ और डॉक्टर की अनुमति के बिना उस पर डेंचर न पहनें।", "• 7–10 दिन में टाँके; क्राउन से पहले इम्प्लांट लगभग 3 महीने में भरता है। फ़ाइनल क्राउन के आसपास रोज़ सफ़ाई करें और हर 6 महीने जाँच के लिए आएँ।"],
    },
  },
  {
    id: "sinus", group: "care",
    title: { en: "Sinus lift surgery", te: "సైనస్ లిఫ్ట్ శస్త్రచికిత్స", hi: "साइनस लिफ़्ट सर्जरी" },
    keys: ["sinus", "sinus lift", "augmentation", "సైనస్", "साइनस"],
    a: {
      en: ["• Do NOT blow your nose for 4 weeks (or as advised). Sneeze with your mouth open.", "• Bite on the gauze for at least 30 minutes. A little clear or lightly bloody nasal discharge can occur; report heavy bleeding at once.", "• Do not rinse or spit for 72 hours; do not brush near the surgery for 48 hours.", "• Ice on the face for the first 48 hours; some swelling or bruising under the eyes is not unusual.", "• Take all medicines as prescribed, including the full antibiotic and decongestant course.", "• No smoking, straws, fizzy drinks or alcohol; do not stretch your lip to look at the area. Ask before wearing any denture over it."],
      te: ["• 4 వారాలు (లేదా చెప్పినంత కాలం) ముక్కు చీదకండి. తుమ్మేటప్పుడు నోరు తెరిచి తుమ్మండి.", "• కనీసం 30 నిమిషాలు గాజ్ కొరికి పట్టుకోండి. ముక్కు నుండి కొంచెం స్పష్టమైన లేదా లేత ఎరుపు స్రావం రావచ్చు; ఎక్కువ రక్తం వస్తే వెంటనే చెప్పండి.", "• 72 గంటలు పుక్కిలించకండి, ఉమ్మకండి; 48 గంటలు సర్జరీ చోట బ్రష్ చేయకండి.", "• మొదటి 48 గంటలు ముఖంపై ఐస్; కళ్ళ కింద కొంచెం వాపు లేదా నల్లబడడం అసాధారణం కాదు.", "• యాంటీబయాటిక్, డీకంజెస్టెంట్ కోర్సుతో సహా అన్ని మందులు చెప్పినట్లే వాడండి.", "• పొగ, స్ట్రా, కూల్‌డ్రింక్స్, మద్యం వద్దు; చూడడానికి పెదవిని లాగకండి. దానిపై కట్టుడు పళ్ళు పెట్టే ముందు అడగండి."],
      hi: ["• 4 हफ़्ते (या बताए अनुसार) नाक न छिनकें। छींक मुँह खोलकर लें।", "• कम से कम 30 मिनट गॉज़ दबाए रखें। नाक से थोड़ा साफ़ या हल्का लाल स्राव हो सकता है; ज़्यादा खून आए तो तुरंत बताएँ।", "• 72 घंटे कुल्ला या थूकना नहीं; 48 घंटे सर्जरी के पास ब्रश न करें।", "• पहले 48 घंटे चेहरे पर बर्फ़; आँखों के नीचे थोड़ी सूजन या नीलापन असामान्य नहीं है।", "• एंटीबायोटिक और डिकंजेस्टेंट का पूरा कोर्स समेत सभी दवाइयाँ लिखे अनुसार लें।", "• धूम्रपान, स्ट्रॉ, कोल्ड ड्रिंक और शराब नहीं; देखने के लिए होंठ न खींचें। उस पर डेंचर लगाने से पहले पूछें।"],
    },
  },
  {
    id: "cd", group: "care",
    title: { en: "New complete dentures", te: "కొత్త పూర్తి కట్టుడు పళ్ళు", hi: "नया पूरा डेंचर" },
    keys: ["complete denture", "full denture", "dentures", "false teeth", "కట్టుడు పళ్ళు", "డెంచర్", "नकली दाँत", "डेंचर", "बत्तीसी", "kattudu"],
    a: {
      en: ["• New dentures feel bulky at first; speech and chewing improve over a few weeks. Reading aloud helps.", "• Start with soft food in small pieces, chewing on both sides at the same time.", "• Sore spots in the first days are expected — come back for adjustment; do not adjust them yourself.", "• Remove them at night and keep them in clean water.", "• Clean daily with a denture brush and soap over a basin of water; no hot water. Brush gums and tongue gently.", "• Check-up at least once a year."],
      te: ["• కొత్త కట్టుడు పళ్ళు మొదట పెద్దగా అనిపిస్తాయి; కొన్ని వారాల్లో మాట్లాడడం, నమలడం మెరుగవుతాయి. గట్టిగా చదవడం సహాయపడుతుంది.", "• చిన్న ముక్కలుగా చేసిన మెత్తని ఆహారంతో మొదలుపెట్టి, రెండు వైపులా ఒకేసారి నమలండి.", "• మొదటి రోజుల్లో పుండ్లు రావడం సహజం — సరిచేయించుకోవడానికి రండి; మీరే సరిచేయకండి.", "• రాత్రి తీసి శుభ్రమైన నీటిలో ఉంచండి.", "• నీటి బేసిన్ పైన డెంచర్ బ్రష్, సబ్బుతో రోజూ శుభ్రం చేయండి; వేడి నీరు వద్దు. చిగుళ్ళు, నాలుకను మెల్లగా బ్రష్ చేయండి.", "• ఏడాదికి కనీసం ఒకసారి చెకప్."],
      hi: ["• नया डेंचर शुरू में भारी लगता है; कुछ हफ़्तों में बोलना और चबाना बेहतर होता है। ज़ोर से पढ़ने से मदद मिलती है।", "• छोटे टुकड़ों में नरम खाने से शुरू करें और दोनों तरफ़ एक साथ चबाएँ।", "• शुरुआती दिनों में छाले होना सामान्य है — ठीक करवाने आएँ; खुद ठीक न करें।", "• रात में निकालकर साफ़ पानी में रखें।", "• पानी भरे बेसिन के ऊपर डेंचर ब्रश और साबुन से रोज़ साफ़ करें; गर्म पानी नहीं। मसूड़े और जीभ धीरे से ब्रश करें।", "• साल में कम से कम एक बार जाँच।"],
    },
  },
  {
    id: "rpd", group: "care",
    title: { en: "Partial denture", te: "పాక్షిక కట్టుడు పళ్ళు", hi: "आंशिक डेंचर" },
    keys: ["partial denture", "rpd", "removable", "పాక్షిక", "పార్షియల్", "आंशिक", "पार्शियल"],
    a: {
      en: ["• It will feel strange for several days to a few weeks.", "• Sore spots in the first 24 hours are expected — come for adjustment after 24 hours and again after about a week.", "• Clean it daily with a denture brush and toothpaste over a basin of water; clean the parts touching your natural teeth carefully.", "• Use a fluoride toothpaste; brush your gums once a day with a soft brush.", "• Remove it at night and keep it in water or mouthwash — it becomes brittle if left dry.", "• Get it and your gums checked at least once a year."],
      te: ["• కొన్ని రోజుల నుండి కొన్ని వారాల వరకు వింతగా అనిపిస్తుంది.", "• మొదటి 24 గంటల్లో పుండ్లు రావడం సహజం — 24 గంటల తర్వాత, మళ్ళీ సుమారు వారం తర్వాత సరిచేయించుకోవడానికి రండి.", "• నీటి బేసిన్ పైన డెంచర్ బ్రష్, టూత్‌పేస్ట్‌తో రోజూ శుభ్రం చేయండి; సహజ పళ్ళను తాకే భాగాలు జాగ్రత్తగా శుభ్రం చేయండి.", "• ఫ్లోరైడ్ టూత్‌పేస్ట్ వాడండి; మెత్తని బ్రష్‌తో రోజుకు ఒకసారి చిగుళ్ళు బ్రష్ చేయండి.", "• రాత్రి తీసి నీటిలో లేదా మౌత్‌వాష్‌లో ఉంచండి — ఎండిపోతే పెళుసుగా మారుతుంది.", "• ఏడాదికి కనీసం ఒకసారి దాన్ని, చిగుళ్ళను చెక్ చేయించుకోండి."],
      hi: ["• कुछ दिनों से कुछ हफ़्तों तक अजीब लगेगा।", "• पहले 24 घंटे में छाले होना सामान्य है — 24 घंटे बाद और फिर लगभग एक हफ़्ते बाद ठीक करवाने आएँ।", "• पानी भरे बेसिन के ऊपर डेंचर ब्रश और टूथपेस्ट से रोज़ साफ़ करें; असली दाँतों को छूने वाले हिस्से ध्यान से साफ़ करें।", "• फ़्लोराइड टूथपेस्ट इस्तेमाल करें; मुलायम ब्रश से दिन में एक बार मसूड़े ब्रश करें।", "• रात में निकालकर पानी या माउथवॉश में रखें — सूखा रहने पर भुरभुरा हो जाता है।", "• साल में कम से कम एक बार इसकी और मसूड़ों की जाँच करवाएँ।"],
    },
  },
  {
    id: "braces", group: "care",
    title: { en: "Braces", te: "బ్రేసెస్ (క్లిప్పులు)", hi: "ब्रेसेस" },
    keys: ["braces", "brackets", "wire", "ortho", "bands", "బ్రేసెస్", "క్లిప్", "వైర్", "ब्रेसेस", "तार", "क्लिप"],
    a: {
      en: ["• Teeth are usually sore for 2–3 days after fitting or adjustment.", "• If a wire or bracket rubs, put a small piece of orthodontic wax (or wet tissue) on it; call if it continues.", "• Avoid hard and sticky food: chewing gum, toffee, hard sweets, popcorn, nuts, ice; cut apples and carrots into small pieces and chew with back teeth.", "• Brush carefully for about 3 minutes, especially along the gum line; clean between teeth daily; a fluoride mouthwash is recommended.", "• A loose bracket or broken wire is not an emergency unless it hurts — call the clinic.", "• Keep your appointments every 4–6 weeks."],
      te: ["• బ్రేసెస్ పెట్టిన లేదా బిగించిన తర్వాత 2–3 రోజులు పళ్ళు నొప్పిగా ఉంటాయి.", "• వైర్ లేదా బ్రాకెట్ గుచ్చుకుంటే చిన్న ఆర్థోడాంటిక్ వ్యాక్స్ (లేదా తడి టిష్యూ) ముక్క పెట్టండి; తగ్గకపోతే కాల్ చేయండి.", "• గట్టి, జిగట ఆహారం మానండి: చూయింగ్ గమ్, టాఫీ, గట్టి స్వీట్లు, పాప్‌కార్న్, గింజలు, ఐస్; ఆపిల్, క్యారెట్ చిన్న ముక్కలుగా చేసి వెనుక పళ్ళతో నమలండి.", "• సుమారు 3 నిమిషాలు జాగ్రత్తగా, ముఖ్యంగా చిగుళ్ళ దగ్గర బ్రష్ చేయండి; రోజూ పళ్ళ మధ్య శుభ్రం చేయండి; ఫ్లోరైడ్ మౌత్‌వాష్ మంచిది.", "• బ్రాకెట్ ఊడినా, వైర్ విరిగినా నొప్పి లేకపోతే అత్యవసరం కాదు — క్లినిక్‌కు కాల్ చేయండి.", "• ప్రతి 4–6 వారాల అపాయింట్‌మెంట్లు తప్పకుండా రండి."],
      hi: ["• ब्रेसेस लगने या कसने के बाद 2–3 दिन दाँतों में दर्द रहता है।", "• तार या ब्रैकेट चुभे तो ऑर्थोडॉन्टिक वैक्स (या गीले टिश्यू) का छोटा टुकड़ा लगाएँ; बना रहे तो कॉल करें।", "• सख़्त और चिपचिपी चीज़ें न खाएँ: च्युइंग गम, टॉफ़ी, सख़्त मिठाई, पॉपकॉर्न, मेवे, बर्फ़; सेब और गाजर छोटे टुकड़ों में काटकर पीछे के दाँतों से चबाएँ।", "• लगभग 3 मिनट ध्यान से ब्रश करें, खासकर मसूड़ों के पास; रोज़ दाँतों के बीच सफ़ाई करें; फ़्लोराइड माउथवॉश अच्छा है।", "• ढीला ब्रैकेट या टूटा तार दर्द न हो तो इमरजेंसी नहीं है — क्लिनिक को कॉल करें।", "• हर 4–6 हफ़्ते की अपॉइंटमेंट पर ज़रूर आएँ।"],
    },
  },
  {
    id: "aligners", group: "care",
    title: { en: "Clear aligners", te: "క్లియర్ అలైనర్స్", hi: "क्लियर अलाइनर" },
    keys: ["aligner", "invisible", "clear braces", "tray", "అలైనర్", "अलाइनर"],
    a: {
      en: ["• Wear them day and night (about 22 hours); remove only to eat, brush, or drink anything other than water.", "• Wash hands before handling; clean them with a separate soft brush and soap — not toothpaste, not hot water.", "• Insert by pressing over the front teeth, then on the back teeth until they snap in; do not bite them into place. Remove starting from the back.", "• Never wrap them in a napkin or keep them in a pocket — always use the case. Keep away from heat and pets.", "• Check U (upper) / L (lower) and the number before wearing. Speech becomes normal in a few days.", "• If an edge pinches the gum, call the clinic. Bring the aligners to every visit."],
      te: ["• పగలు, రాత్రి (సుమారు 22 గంటలు) వేసుకోండి; తినేటప్పుడు, బ్రష్ చేసేటప్పుడు, నీరు కాకుండా ఏదైనా తాగేటప్పుడు మాత్రమే తీయండి.", "• పట్టుకునే ముందు చేతులు కడుక్కోండి; వేరే మెత్తని బ్రష్, సబ్బుతో శుభ్రం చేయండి — టూత్‌పేస్ట్, వేడి నీరు వద్దు.", "• ముందు పళ్ళపై నొక్కి, తర్వాత వెనుక పళ్ళపై నొక్కి సరిగ్గా కూర్చోబెట్టండి; కొరికి పెట్టకండి. తీసేటప్పుడు వెనుక నుండి మొదలుపెట్టండి.", "• నాప్‌కిన్‌లో చుట్టకండి, జేబులో పెట్టకండి — ఎప్పుడూ కేస్ వాడండి. వేడికి, పెంపుడు జంతువులకు దూరంగా ఉంచండి.", "• వేసుకునే ముందు U (పై) / L (కింది), నంబర్ చూడండి. కొన్ని రోజుల్లో మాట మామూలవుతుంది.", "• అంచు చిగుళ్ళకు గుచ్చుకుంటే క్లినిక్‌కు కాల్ చేయండి. ప్రతి విజిట్‌కు అలైనర్స్ తీసుకురండి."],
      hi: ["• दिन-रात (लगभग 22 घंटे) पहनें; सिर्फ़ खाने, ब्रश करने या पानी के अलावा कुछ पीने के समय निकालें।", "• छूने से पहले हाथ धोएँ; अलग मुलायम ब्रश और साबुन से साफ़ करें — टूथपेस्ट या गर्म पानी नहीं।", "• पहले आगे के दाँतों पर, फिर पीछे के दाँतों पर दबाकर बैठाएँ; काटकर न बैठाएँ। निकालते समय पीछे से शुरू करें।", "• नैपकिन में न लपेटें, जेब में न रखें — हमेशा केस में रखें। गर्मी और पालतू जानवरों से दूर रखें।", "• पहनने से पहले U (ऊपर) / L (नीचे) और नंबर देखें। कुछ दिनों में बोलना सामान्य हो जाता है।", "• किनारा मसूड़े में चुभे तो क्लिनिक को कॉल करें। हर विज़िट पर अलाइनर साथ लाएँ।"],
    },
  },
  {
    id: "retainer", group: "care",
    title: { en: "Retainers", te: "రిటైనర్", hi: "रिटेनर" },
    keys: ["retainer", "after braces", "రిటైనర్", "रिटेनर"],
    a: {
      en: ["• First 10 weeks: wear it all the time, except when eating, brushing and playing sports.", "• Then at night for 6 months to 2 years, and after that a few nights a week, for life (or as advised).", "• Brush it daily with a toothbrush and soap; no harsh cleaners or hot water.", "• When it is out, keep it in its box with water so it does not dry and lose its fit.", "• Fixed (wire) retainer: avoid biting hard food, use a floss threader, and call at once if it feels loose.", "If it is lost, broken or does not fit, visit the clinic."],
      te: ["• మొదటి 10 వారాలు: తినేటప్పుడు, బ్రష్ చేసేటప్పుడు, ఆటలప్పుడు తప్ప ఎప్పుడూ వేసుకోండి.", "• తర్వాత 6 నెలల నుండి 2 సంవత్సరాల వరకు రాత్రిళ్ళు, ఆ తర్వాత జీవితాంతం వారానికి కొన్ని రాత్రులు (లేదా చెప్పినట్లు).", "• రోజూ టూత్‌బ్రష్, సబ్బుతో శుభ్రం చేయండి; గట్టి క్లీనర్లు, వేడి నీరు వద్దు.", "• తీసినప్పుడు ఎండిపోకుండా నీళ్ళు ఉన్న బాక్స్‌లో ఉంచండి.", "• ఫిక్స్‌డ్ (వైర్) రిటైనర్: గట్టి ఆహారం కొరకకండి, ఫ్లాస్ థ్రెడర్ వాడండి, వదులుగా అనిపిస్తే వెంటనే కాల్ చేయండి.", "పోయినా, విరిగినా, సరిగ్గా సరిపోకపోయినా క్లినిక్‌కు రండి."],
      hi: ["• पहले 10 हफ़्ते: खाना, ब्रश और खेल के समय छोड़कर हर समय पहनें।", "• फिर 6 महीने से 2 साल तक रात में, और उसके बाद जीवनभर हफ़्ते में कुछ रातें (या बताए अनुसार)।", "• रोज़ टूथब्रश और साबुन से साफ़ करें; कठोर क्लीनर या गर्म पानी नहीं।", "• निकालने पर पानी वाले डिब्बे में रखें ताकि सूखकर उसकी फ़िटिंग न बिगड़े।", "• फ़िक्स्ड (तार वाला) रिटेनर: सख़्त चीज़ न काटें, फ़्लॉस थ्रेडर इस्तेमाल करें, ढीला लगे तो तुरंत कॉल करें।", "खो जाए, टूट जाए या फ़िट न हो तो क्लिनिक आएँ।"],
    },
  },
  {
    id: "headgear", group: "care",
    title: { en: "Headgear / reverse headgear", te: "హెడ్‌గేర్ / రివర్స్ హెడ్‌గేర్", hi: "हेडगियर / रिवर्स हेडगियर" },
    keys: ["headgear", "reverse headgear", "facemask", "face mask", "హెడ్‌గేర్", "हेडगियर"],
    a: {
      en: ["• Wear it 12–14 hours every day (night sleep plus 4–6 hours while awake). It works only when worn consistently.", "• The first 3 days are the hardest as teeth feel sore; wear it as continuously as possible then.", "• Putting it on an hour before bedtime makes night wear easier.", "• Wash the pads by hand in warm soapy water and let them air-dry.", "• Never play or swim with it on. If it gets bent, tell the doctor and visit.", "• Make up missed hours the next day, bring it to every appointment, and tell the clinic straight away if you cannot wear it."],
      te: ["• రోజూ 12–14 గంటలు వేసుకోండి (రాత్రి నిద్ర + మెలకువగా ఉన్నప్పుడు 4–6 గంటలు). క్రమం తప్పకుండా వేసుకుంటేనే పనిచేస్తుంది.", "• మొదటి 3 రోజులు పళ్ళు నొప్పిగా ఉండి కష్టంగా ఉంటుంది; అప్పుడు వీలైనంత ఎక్కువ సేపు వేసుకోండి.", "• నిద్రకు గంట ముందు వేసుకుంటే రాత్రి అలవాటు సులభమవుతుంది.", "• ప్యాడ్‌లను గోరువెచ్చని సబ్బు నీటిలో చేతితో కడిగి గాలికి ఆరబెట్టండి.", "• వేసుకుని ఆడకండి, ఈతకు వెళ్ళకండి. వంగిపోతే డాక్టర్‌కు చెప్పి క్లినిక్‌కు రండి.", "• మిస్ అయిన గంటలు మరుసటి రోజు పూర్తి చేయండి, ప్రతి అపాయింట్‌మెంట్‌కు తీసుకురండి, వేసుకోలేకపోతే వెంటనే క్లినిక్‌కు చెప్పండి."],
      hi: ["• रोज़ 12–14 घंटे पहनें (रात की नींद + जागते हुए 4–6 घंटे)। नियमित पहनने पर ही काम करता है।", "• पहले 3 दिन दाँतों में दर्द के कारण सबसे मुश्किल होते हैं; तब जितना हो सके लगातार पहनें।", "• सोने से एक घंटा पहले पहनने से रात में आदत आसान होती है।", "• पैड गुनगुने साबुन-पानी में हाथ से धोकर हवा में सुखाएँ।", "• पहनकर न खेलें, न तैरें। मुड़ जाए तो डॉक्टर को बताकर क्लिनिक आएँ।", "• छूटे घंटे अगले दिन पूरे करें, हर अपॉइंटमेंट पर साथ लाएँ, और न पहन पाएँ तो तुरंत क्लिनिक को बताएँ।"],
    },
  },
  {
    id: "twinblock", group: "care",
    title: { en: "Twin block appliance", te: "ట్విన్ బ్లాక్ అప్లయన్స్", hi: "ट्विन ब्लॉक अप्लायंस" },
    keys: ["twin block", "twinblock", "functional appliance", "ట్విన్ బ్లాక్", "ट्विन ब्लॉक"],
    a: {
      en: ["• Wear it all the time, except for swimming and cleaning — it only works if worn as directed.", "• Clean it with a toothbrush and soap after every meal.", "• To put in: press with the index fingers so the back clasps fit around the molars. To remove: push on the back clasps, never pull the front wire.", "• Some discomfort of the teeth and face muscles in the first 1–2 weeks is normal.", "• Usually worn full-time for 9–12 months before braces.", "• Breakage or loss means a laboratory charge for repair or replacement — please take care of it."],
      te: ["• ఈత, శుభ్రం చేసేటప్పుడు తప్ప ఎప్పుడూ వేసుకోండి — చెప్పినట్లు వేసుకుంటేనే పనిచేస్తుంది.", "• ప్రతి భోజనం తర్వాత టూత్‌బ్రష్, సబ్బుతో శుభ్రం చేయండి.", "• పెట్టడానికి: వెనుక క్లాస్ప్‌లు దవడ పళ్ళను చుట్టుకునేలా చూపుడు వేళ్ళతో నొక్కండి. తీయడానికి: వెనుక క్లాస్ప్‌లపై నొక్కండి, ముందు వైర్‌ను ఎప్పుడూ లాగకండి.", "• మొదటి 1–2 వారాలు పళ్ళు, ముఖ కండరాలలో కొంచెం అసౌకర్యం సాధారణం.", "• సాధారణంగా బ్రేసెస్‌కు ముందు 9–12 నెలలు పూర్తి సమయం వేసుకోవాలి.", "• విరిగినా, పోయినా రిపేర్/కొత్తదానికి ల్యాబ్ ఛార్జ్ ఉంటుంది — జాగ్రత్తగా ఉంచండి."],
      hi: ["• तैरने और सफ़ाई के समय को छोड़कर हर समय पहनें — बताए अनुसार पहनने पर ही काम करता है।", "• हर भोजन के बाद टूथब्रश और साबुन से साफ़ करें।", "• लगाने के लिए: तर्जनी उँगलियों से दबाएँ ताकि पीछे के क्लैस्प दाढ़ों पर बैठ जाएँ। निकालने के लिए: पीछे के क्लैस्प पर दबाएँ, आगे का तार कभी न खींचें।", "• पहले 1–2 हफ़्ते दाँतों और चेहरे की मांसपेशियों में थोड़ी असुविधा सामान्य है।", "• आमतौर पर ब्रेसेस से पहले 9–12 महीने पूरे समय पहना जाता है।", "• टूटने या खोने पर मरम्मत/नए के लिए लैब शुल्क लगता है — ध्यान से रखें।"],
    },
  },
  {
    id: "tmd", group: "care",
    title: { en: "Jaw joint (TMD) care", te: "దవడ కీలు (TMD) జాగ్రత్తలు", hi: "जबड़े के जोड़ (TMD) की देखभाल" },
    keys: ["tmd", "tmj", "jaw pain", "jaw joint", "clicking", "grinding", "దవడ నొప్పి", "దవడ", "जबड़े", "जबड़ा दर्द", "jaw"],
    a: {
      en: ["• Eat soft food cut into small pieces and chew with the back teeth; avoid chewing gum and hard or chewy food.", "• Warm and cold packs: 10 minutes on, 5 minutes off, repeated.", "• Rest your tongue on the roof of your mouth; keep lips together and teeth apart.", "• Limit mouth opening (yawning, laughing) to about a thumb's width; avoid movements that make the joint click.", "• Good posture; sleep on your back; do not rest your jaw on your hand or bite nails or pens.", "• Wear the night guard if prescribed. Take only the medicines the doctor prescribes."],
      te: ["• చిన్న ముక్కలుగా చేసిన మెత్తని ఆహారం తిని, వెనుక పళ్ళతో నమలండి; చూయింగ్ గమ్, గట్టి లేదా ఎక్కువ నమలాల్సిన ఆహారం మానండి.", "• వెచ్చని, చల్లని ప్యాక్‌లు: 10 నిమిషాలు పెట్టి, 5 నిమిషాలు తీసి, మళ్ళీ పెట్టండి.", "• నాలుకను అంగిలికి ఆనించి ఉంచండి; పెదవులు కలిపి, పళ్ళు దూరంగా ఉంచండి.", "• ఆవలింత, నవ్వు సమయంలో నోరు బొటనవేలు మందం వరకే తెరవండి; కీలు శబ్దం చేసే కదలికలు మానండి.", "• సరైన భంగిమ; వెల్లకిలా పడుకోండి; దవడను చేతిపై ఆనించకండి, గోళ్ళు లేదా పెన్నులు కొరకకండి.", "• నైట్ గార్డ్ సూచిస్తే వేసుకోండి. డాక్టర్ రాసిన మందులు మాత్రమే వాడండి."],
      hi: ["• छोटे टुकड़ों में नरम खाना खाएँ और पीछे के दाँतों से चबाएँ; च्युइंग गम और सख़्त या ज़्यादा चबाने वाली चीज़ें न खाएँ।", "• गर्म और ठंडी सिकाई: 10 मिनट लगाएँ, 5 मिनट हटाएँ, फिर दोहराएँ।", "• जीभ तालू पर टिकाकर रखें; होंठ मिले और दाँत अलग रखें।", "• जम्हाई या हँसते समय मुँह लगभग अँगूठे की मोटाई तक ही खोलें; जोड़ से आवाज़ करने वाली हरकतें न करें।", "• सही मुद्रा रखें; पीठ के बल सोएँ; जबड़ा हाथ पर न टिकाएँ, नाखून या पेन न चबाएँ।", "• नाइट गार्ड बताया हो तो पहनें। सिर्फ़ डॉक्टर की लिखी दवाइयाँ लें।"],
    },
  },
  {
    id: "veneers", group: "care",
    title: { en: "Veneers / laminates", te: "వెనీర్స్ / లామినేట్స్", hi: "विनियर / लैमिनेट" },
    keys: ["veneer", "laminate", "వెనీర్", "లామినేట్", "विनियर", "लैमिनेट"],
    a: {
      en: ["• Mild sensitivity to hot and cold for a few days is normal.", "• Do not bite very hard things (ice, nut shells, bones) or open packets with your teeth.", "• Brush and floss normally with a non-abrasive toothpaste.", "• Tea, coffee and tobacco can stain the edges over time; regular cleaning keeps them looking good.", "• If you grind your teeth, wear the night guard given to you.", "Call if a veneer feels rough or loose, or the bite feels high."],
      te: ["• కొన్ని రోజులు వేడి/చల్లటికి కొంచెం జివ్వుమనడం సాధారణం.", "• చాలా గట్టివి (ఐస్, గింజల పెంకులు, ఎముకలు) కొరకకండి, పళ్ళతో ప్యాకెట్లు తెరవకండి.", "• గరుకు లేని టూత్‌పేస్ట్‌తో మామూలుగా బ్రష్, ఫ్లాస్ చేయండి.", "• టీ, కాఫీ, పొగాకు వల్ల కాలక్రమేణా అంచుల్లో మరకలు పడవచ్చు; క్రమం తప్పని క్లీనింగ్ అందంగా ఉంచుతుంది.", "• పళ్ళు కొరికే అలవాటు ఉంటే ఇచ్చిన నైట్ గార్డ్ వేసుకోండి.", "వెనీర్ గరుకుగా లేదా వదులుగా అనిపించినా, కొరికితే ఎత్తుగా ఉన్నా కాల్ చేయండి."],
      hi: ["• कुछ दिन ठंडा-गरम हल्का लगना सामान्य है।", "• बहुत सख़्त चीज़ें (बर्फ़, मेवों के छिलके, हड्डी) न काटें और दाँतों से पैकेट न खोलें।", "• बिना घिसने वाले टूथपेस्ट से सामान्य रूप से ब्रश और फ़्लॉस करें।", "• चाय, कॉफ़ी और तंबाकू से समय के साथ किनारों पर दाग़ लग सकते हैं; नियमित सफ़ाई से सुंदर रहते हैं।", "• दाँत पीसने की आदत हो तो दिया गया नाइट गार्ड पहनें।", "विनियर खुरदुरा या ढीला लगे, या काटने पर ऊँचा लगे तो कॉल करें।"],
    },
  },
  {
    id: "laser", group: "care",
    title: { en: "Laser therapy (LLLT)", te: "లేజర్ థెరపీ", hi: "लेज़र थेरेपी" },
    keys: ["laser", "lllt", "లేజర్", "लेज़र", "लेजर"],
    a: {
      en: ["• Low-level laser therapy does not cut or heat the tissue, so no special care is needed after a session.", "• Continue the medicines or mouthwash the doctor prescribed.", "• Several short sessions are often needed — attend all of them.", "• Tell the clinic if the pain increases or a new swelling appears."],
      te: ["• లో-లెవెల్ లేజర్ థెరపీ కణజాలాన్ని కోయదు, వేడి చేయదు — సెషన్ తర్వాత ప్రత్యేక జాగ్రత్తలు అవసరం లేదు.", "• డాక్టర్ సూచించిన మందులు లేదా మౌత్‌వాష్ కొనసాగించండి.", "• తరచుగా కొన్ని చిన్న సెషన్లు అవసరం — అన్నిటికీ రండి.", "• నొప్పి పెరిగినా, కొత్త వాపు వచ్చినా క్లినిక్‌కు చెప్పండి."],
      hi: ["• लो-लेवल लेज़र थेरेपी ऊतक को न काटती है न गर्म करती है, इसलिए सेशन के बाद कोई खास देखभाल नहीं चाहिए।", "• डॉक्टर की बताई दवाइयाँ या माउथवॉश जारी रखें।", "• अक्सर कई छोटे सेशन लगते हैं — सभी में आएँ।", "• दर्द बढ़े या नई सूजन आए तो क्लिनिक को बताएँ।"],
    },
  },
];

/* Offline matching: pick the topic whose keywords best match the question. */
export function matchTopic(text) {
  const q = ` ${String(text || "").toLowerCase()} `;
  let best = null, bestScore = 0;
  for (const t of TOPICS) {
    let score = 0;
    for (const k of t.keys) if (q.includes(k.toLowerCase())) score += k.length;
    for (const v of Object.values(t.title)) if (q.includes(v.toLowerCase())) score += 20;
    if (score > bestScore) { best = t; bestScore = score; }
  }
  return bestScore >= 3 ? best : null;
}