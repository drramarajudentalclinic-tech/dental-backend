/* ═══════════════════════════════════════════════════════════════════
   ALL WEBSITE TEXT LIVES HERE.
   Change words, phone numbers, timings, equipment and protocols in this
   one file — the pages pick them up automatically.

   Anything written inside square brackets, like [this], is a placeholder that is
   waiting for the clinic's real details. The site shows a small yellow
   "draft" strip at the top while any placeholder is left.

   Dental Council of India advertising rules: keep everything factual.
   No "best", "No.1", "painless guarantee", prices-as-offers, patient
   testimonials or before/after photos of identifiable patients.
   ═══════════════════════════════════════════════════════════════════ */

import * as photos from "./photos";

export const clinic = {
  name: "Sri Satya Sai Oral Health Center & Dental Clinic",
  shortName: "Sri Satya Sai Dental",
  motto: "Oral health for healthy life",
  tagline: "Complete dental care in Chaitanyapuri, Hyderabad, led by a specialist in oral medicine and radiology with 30 years of experience. Every treatment is explained before we begin.",
  phone: "+91 99088 94449",
  whatsapp: "+91 99088 94449",
  email: "drramarajudentalclinic@gmail.com",
  address: [
    "G-15, Ground Floor, Rajanigandha Apartments",
    "Opposite Metro Pillar No. 1563, Chaitanyapuri",
    "Hyderabad – 500060, Telangana",
  ],
  landmark: "Near Dilsukhnagar, opposite Metro Pillar No. 1563",
  mapsLink: "https://maps.app.goo.gl/F8Zp631MJP9MvKtk7",
  mapQuery: "Sri Satya Sai Oral Health Center and Dental Clinic, Chaitanyapuri, Hyderabad",
  mapCenter: "17.3680732,78.5326468",   // the clinic pin on Google Maps
  hours: [
    ["Monday – Saturday", "11:00 am – 7:00 pm"],
    ["Sunday", "Holiday"],
  ],
  hoursNote: "By appointment only. Please call or WhatsApp before you come.",
  registration: "A-1096",      // Dental Council registration no. (footer and doctor card)
};

export const doctors = [
  {
    name: "Dr. D. Rama Raju",
    initials: "RR",
    qualification: "BDS, MDS (Oral Medicine & Radiology)",
    title: "Dentist and specialist in Oral Medicine & Radiology",
    stats: [
      ["30", "years in practice"],
      ["MDS", "Oral Medicine & Radiology"],
      ["IDA", "Member, Indian Dental Association"],
    ],
    about: [
      "Dr. D. Rama Raju holds a master's degree in Oral Medicine and Radiology, the speciality that deals with diagnosing diseases of the mouth, jaws and face and with reading dental X-rays and scans. He has practised dentistry for 30 years and runs Sri Satya Sai Oral Health Center & Dental Clinic in Chaitanyapuri, near Dilsukhnagar, Hyderabad.",
      "Patients see him for everything from check-ups, fillings and root canals to extractions, implants, dentures, braces and full-mouth rehabilitation. Every treatment starts with a clear diagnosis, and the options and the cost are explained before anything begins.",
    ],
    focus: [
      "Diagnosis of mouth ulcers, patches and lumps; oral cancer screening",
      "Reading dental X-rays, OPG and CBCT scans",
      "Root canals, crowns and bridges",
      "Implants with surgical guides, dentures and full-mouth rehabilitation",
      "Extractions, including wisdom teeth",
      "Braces, aligners and smile design",
    ],
    timeline: [
      ["1996", "BDS", "Osmania Medical College, Hyderabad"],
      ["2000", "MDS, Oral Medicine & Radiology", "Osmania Medical College, Hyderabad"],
      ["Today", "30 years in practice", "Sri Satya Sai Oral Health Center & Dental Clinic, Chaitanyapuri"],
    ],
  },
];

/* What patients come for — shown as a plain list, no prices. */
export const services = [
  ["Check-ups and cleaning", "Examination, scaling and polishing, fluoride application and pit-and-fissure sealants."],
  ["Fillings", "Tooth-coloured composite and glass-ionomer fillings matched to the shade of your tooth."],
  ["Root canal treatment", "Single- and multiple-visit root canals with rotary files, apex locator and warm 3-D gutta-percha filling; re-treatment of old root canals."],
  ["Crowns and bridges", "Zirconia, all-ceramic and metal-ceramic crowns and bridges, made from a digital scan of your teeth."],
  ["Dental implants", "Single and multiple implants planned on a CBCT scan and placed with a surgical guide; Straumann, Nobel Biocare, Osstem, DIO, Neo Biotech, Noris, Adin and Alpha-Bio systems."],
  ["Artificial teeth and dentures", "Complete and partial dentures, flexible dentures and implant-supported dentures."],
  ["Bone grafts and PRF", "Bone grafts made from your own extracted tooth (Tooth Titan) and platelet-rich fibrin (PRF) from your own blood, for sockets, implants and gum surgery."],
  ["Oral rehabilitation", "Full-mouth rehabilitation for worn, broken or missing teeth, restoring chewing and bite together."],
  ["Wisdom teeth and extractions", "Simple and surgical extractions, including impacted wisdom teeth, with PRF from your own blood to help healing where needed."],
  ["Oral medicine and oral cancer screening", "Check-ups for white or red patches, non-healing ulcers and lumps in the mouth with the DrOroscope screening light; burning mouth and facial pain."],
  ["Dental X-rays and scans", "Digital X-rays at the clinic; OPG and CBCT scans at an imaging centre when needed, read and explained by the doctor, a specialist in oral radiology."],
  ["Gum treatment", "Deep cleaning, gum surgery and maintenance for bleeding, swollen or loose gums."],
  ["Braces and aligners", "Fixed metal and ceramic braces, and clear aligners planned from a digital scan."],
  ["Teeth reshaping and smile design", "Reshaping, bonding, veneers and teeth whitening to improve the look of your smile."],
  ["Children's dentistry", "Gentle first visits, fillings, pulp treatment for milk teeth and space maintainers."],
  ["Bite problems, jaw pain and sensitivity", "Digital bite analysis with the Teeth Tracer for jaw-joint (TMJ) pain, headaches, teeth grinding and wear; night guards; sensitive teeth and bad breath."],
  ["Dental emergencies", "Tooth pain, swelling, broken or knocked-out teeth. Call us for the earliest appointment."],
];

/* Technology we use, grouped by the treatment it is used for.
   `what` = what it is, `why` = what it changes for you. */
export const technology = [
  {
    treatment: "Check-ups, diagnosis and oral cancer screening",
    items: [
      {
        name: "DrOroscope",
        photo: photos.oroscope,
        art: "oroscope",
        what: "A hand-held oral screening camera made in India by Raamah Biocare. A slim head with a 5-megapixel camera reaches the back of the mouth and photographs each area under white, blue and fluorescence light; the pictures appear on a tablet.",
        why: "Healthy lining glows green while suspicious areas look darker, so early changes in patches, ulcers and lumps are found without cutting. The photos are kept in your record to compare at the next visit.",
      },
      {
        name: "Digital X-rays (RVG)",
        art: "rvg",
        what: "A small sensor replaces film; the picture appears on screen in seconds.",
        why: "Much lower radiation than film, and we zoom in and show you the picture on the screen.",
      },
      {
        name: "Intra-oral camera",
        art: "camera",
        what: "A pen-sized camera that photographs the inside of your mouth.",
        why: "You see what we see (cracks, decay, worn fillings) before deciding on treatment.",
      },
    ],
  },
  {
    treatment: "Root canal treatment",
    items: [
      {
        name: "Apex locator",
        art: "apex",
        what: "An electronic device that measures the exact length of each root canal.",
        why: "Accurate cleaning to the tip of the root, with fewer X-rays during treatment.",
      },
      {
        name: "Rotary endodontics",
        art: "rotary",
        what: "Motor-driven nickel-titanium files that clean and shape the canals.",
        why: "Quicker, more even cleaning of curved canals than hand files alone.",
      },
      {
        name: "Obturation pen",
        art: "obturationPen",
        what: "A heated tip that softens gutta-percha (the rubber-like root filling) and presses it down the canal.",
        why: "The warm filling flows into side canals and gaps, so the root is sealed in three dimensions.",
      },
      {
        name: "Cicada thermal obturator and gutta-percha gun",
        art: "obturationGun",
        what: "A cordless gun that fills the rest of the canal with warm, flowing gutta-percha.",
        why: "A dense, gap-free seal from the tip of the root to the top, which helps keep bacteria out.",
      },
    ],
  },
  {
    treatment: "Comfortable injections",
    items: [
      {
        name: "Anaesthesia booster",
        art: "anaesthesia",
        what: "A device used with the local anaesthetic injection.",
        why: "Makes numbing gentler and more comfortable, especially for anxious patients and children.",
      },
    ],
  },
  {
    treatment: "Crowns, bridges, aligners and dentures",
    items: [
      {
        name: "Runyes intra-oral scanner",
        art: "scanner",
        what: "A wand that takes a 3-D digital scan of your teeth instead of a putty impression.",
        why: "No gagging on impression trays; an accurate digital model is sent to the lab for crowns, bridges, clear aligners and dentures.",
      },
      {
        name: "Aluminium-oxide micro-blaster",
        art: "blaster",
        what: "A fine sand-blaster used on the inside of zirconia and metal crowns before they are cemented.",
        why: "Cleans the crown and roughens it slightly so the cement holds it more firmly.",
      },
    ],
  },
  {
    treatment: "Dental implants, extractions and gum surgery",
    items: [
      {
        name: "Surgical guide for implants",
        art: "guide",
        what: "A 3-D printed guide made from your CBCT scan and digital scan, which fits over your teeth during surgery.",
        why: "The implant goes in the planned position, depth and angle, away from nerves and the sinus, often with a smaller cut.",
      },
      {
        name: "PRFuge centrifuge (PRF)",
        photo: photos.prfuge,
        art: "centrifuge",
        what: "A centrifuge made in India by Raamah Biocare that spins a small sample of your own blood at a fixed force (about 400 g) and a fixed 33° tube angle, to make platelet-rich fibrin (PRF).",
        why: "The same standard spin every time gives a consistent PRF clot, which is placed in extraction sockets, around implants and with bone grafts to support healing. Nothing artificial is added.",
      },
      {
        name: "Tooth Titan",
        photo: photos.toothTitan,
        art: "toothTitan",
        what: "A chairside machine made in India by Raamah Biocare that grinds and filters a tooth that has just been taken out into graft particles of three sizes, in a sealed chamber.",
        why: "Your own tooth becomes the bone-graft material for the socket or the implant site in the same appointment: no donor bone, and nothing foreign to your body.",
      },
      {
        name: "Implant systems",
        art: "implant",
        what: "Straumann (Switzerland), Nobel Biocare NobelActive and NobelReplace, Osstem, DIO and Neo Biotech (South Korea), and Noris Medical, Adin and Alpha-Bio Tec (Israel).",
        why: "The implant is chosen for your bone, the position of the tooth and your budget, and the parts stay available for years.",
      },
    ],
  },
  {
    treatment: "Bite, jaw joint and tooth wear",
    items: [
      {
        name: "Teeth Tracer",
        photo: photos.teethTracer,
        art: "teethTracer",
        what: "A digital bite-force analyser made in India by Raamah Biocare. You bite on a wafer-thin sensor strip, and a computer shows where, how hard and in what order your teeth touch.",
        why: "Teeth that hit too hard show up on the screen, so new crowns, bridges, dentures and implants are adjusted precisely, and causes of jaw-joint (TMJ) pain, headaches and tooth wear are found.",
      },
    ],
  },
  {
    treatment: "Your records",
    items: [
      {
        name: "Digital patient records and patient portal",
        art: "records",
        what: "Every visit, prescription, X-ray and scan is stored in one record for each patient.",
        why: "Nothing is lost between visits, and the doctor can share your records with you online.",
      },
    ],
  },
];

/* Protocols — these really are sequences, so they are shown as numbered steps. */
export const protocols = [
  {
    title: "Sterilisation of every instrument",
    steps: [
      "Used instruments are soaked in disinfectant and cleaned.",
      "They are packed in sealed sterilisation pouches with an indicator strip.",
      "The pouches go through a steam autoclave cycle.",
      "Pouches are opened in front of you, at the chair, for your treatment.",
      "Single-use items (needles, gloves, suction tips, cups) are used once and discarded.",
    ],
  },
  {
    title: "Your first visit",
    steps: [
      "Medical history, allergies and current medicines are recorded.",
      "Examination of teeth, gums, tongue and jaw joint, with intra-oral camera photos.",
      "Screening of the lining of the mouth with the DrOroscope.",
      "Digital X-rays, and an OPG or CBCT scan only if it is needed for a diagnosis.",
      "We explain what we found, the treatment options and the cost before starting anything.",
      "A written prescription and a date for the next visit.",
    ],
  },
  {
    title: "Root canal treatment",
    steps: [
      "Digital X-ray to see the root shape and the infection.",
      "Local anaesthesia with the anaesthesia booster, and isolation of the tooth to keep it clean and dry.",
      "Cleaning and shaping of the canals with rotary files; the length is checked with the apex locator.",
      "Disinfection of the canals with irrigating solutions.",
      "Three-dimensional sealing with warm gutta-percha (obturation pen and Cicada thermal obturator).",
      "Post-treatment X-ray and, where advised, a crown made from a digital scan to protect the tooth.",
    ],
  },
  {
    title: "Crowns and bridges",
    steps: [
      "The tooth is shaped under local anaesthesia.",
      "A 3-D digital scan with the Runyes intra-oral scanner (no impression trays).",
      "A temporary crown while the lab makes the final crown.",
      "Try-in to check fit, bite and shade.",
      "The inside of the crown is cleaned with the aluminium-oxide micro-blaster.",
      "The crown is cemented and the bite is checked with the Teeth Tracer.",
    ],
  },
  {
    title: "Dental implant with a surgical guide",
    steps: [
      "Examination, a CBCT scan at an imaging centre and a digital scan of your teeth.",
      "Digital planning of implant size and position, and a 3-D printed surgical guide.",
      "Implant placement through the guide under local anaesthesia, with PRF or a graft from your own tooth (Tooth Titan) where it helps healing.",
      "Healing period of about 3 months while the implant joins the bone.",
      "A digital scan of the implant and fitting of the crown.",
      "Review visits and cleaning to keep the implant healthy.",
    ],
  },
];


export const portalSteps = [
  ["The doctor switches on your portal", "At your visit, the doctor turns on online access for your registered mobile number."],
  ["The doctor chooses what to share", "Visit summaries, prescriptions, X-rays, scans and receipts — only what the doctor shares appears online."],
  ["You log in with your mobile number", "We send a 6-digit code by SMS. No password to remember."],
];