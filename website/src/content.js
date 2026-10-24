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
  mapQuery: "17.3680732,78.5326468",   // the clinic pin on Google Maps
  hours: [
    ["Monday – Saturday", "11:00 am – 7:00 pm"],
    ["Sunday", "Holiday"],
  ],
  hoursNote: "By appointment only. Please call or WhatsApp before you come.",
  registration: "",      // Dental Council registration no. (shown in the footer once filled in)
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
      "Implants, dentures and full-mouth rehabilitation",
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
  ["Root canal treatment", "Single- and multiple-visit root canals with rotary instruments and electronic length measurement; re-treatment of old root canals."],
  ["Crowns and bridges", "Metal-ceramic, zirconia and all-ceramic crowns; bridges to replace missing teeth."],
  ["Dental implants", "Single and multiple implants, planned on a 3-D CBCT scan, with the crown or denture on top."],
  ["Artificial teeth and dentures", "Complete and partial dentures, flexible dentures and implant-supported dentures."],
  ["Oral rehabilitation", "Full-mouth rehabilitation for worn, broken or missing teeth, restoring chewing and bite together."],
  ["Wisdom teeth and extractions", "Simple and surgical extractions, including impacted wisdom teeth, under local anaesthesia."],
  ["Oral medicine and diagnosis", "Check-ups for white or red patches, non-healing ulcers and lumps in the mouth (oral cancer screening), burning mouth and facial pain."],
  ["Dental X-rays and scans", "IOPA, OPG and CBCT scans taken when needed and read by a specialist in oral radiology, with the findings explained to you."],
  ["Gum treatment", "Deep cleaning, gum surgery and maintenance for bleeding, swollen or loose gums."],
  ["Braces and aligners", "Fixed metal and ceramic braces and clear aligners for crooked or gapped teeth."],
  ["Teeth reshaping and smile design", "Reshaping, bonding, veneers and teeth whitening to improve the look of your smile."],
  ["Children's dentistry", "Gentle first visits, fillings, pulp treatment for milk teeth and space maintainers."],
  ["Sensitivity, bad breath and jaw pain", "Sensitive teeth, bad breath and jaw-joint (TMJ) pain; night guards for teeth grinding."],
  ["Dental emergencies", "Tooth pain, swelling, broken or knocked-out teeth. Call us for the earliest appointment."],
];

/* Technology we use every day. `what` = what it is, `why` = what it changes for you. */
export const technology = [
  {
    name: "Digital X-rays (RVG)",
    what: "A small sensor replaces film; the picture appears on screen in seconds.",
    why: "Much lower radiation than film, and we can zoom in and show you the picture on the screen.",
  },
  {
    name: "OPG — full-mouth X-ray",
    what: "One panoramic picture of all teeth, both jaws and the joints.",
    why: "Shows wisdom teeth, bone levels and hidden problems in a single view.",
  },
  {
    name: "CBCT 3-D scan",
    what: "A 3-D scan of the jaw that we can slice in any direction.",
    why: "Used before implants and complex root canals to see bone width, nerves and sinus — so surgery is planned, not guessed.",
  },
  {
    name: "Intra-oral camera",
    what: "A pen-sized camera that photographs the inside of your mouth.",
    why: "You see exactly what we see — cracks, decay, worn fillings — before deciding on treatment.",
  },
  {
    name: "Rotary endodontics and apex locator",
    what: "Motor-driven nickel-titanium files and an electronic device that measures root length.",
    why: "Root canals that are quicker and more consistent, with fewer X-rays during treatment.",
  },
  {
    name: "Digital patient records",
    what: "Every visit, prescription, X-ray and scan is stored in one record for each patient.",
    why: "Nothing is lost between visits, and the doctor can share your records with you through the patient portal.",
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
      "Single-use items — needles, gloves, suction tips, cups — are used once and discarded.",
    ],
  },
  {
    title: "Your first visit",
    steps: [
      "Medical history, allergies and current medicines are recorded.",
      "Full examination of teeth, gums, tongue and jaw joint.",
      "X-rays or a scan only if they are needed for a diagnosis.",
      "We explain what we found, the treatment options and the cost before starting anything.",
      "A written prescription and a date for the next visit.",
    ],
  },
  {
    title: "Root canal treatment",
    steps: [
      "X-ray to see the root shape and the infection.",
      "Local anaesthesia and isolation of the tooth to keep it clean and dry.",
      "Cleaning and shaping of the canals with rotary files; length checked with the apex locator.",
      "Disinfection and sealing of the canals.",
      "Post-treatment X-ray and, where advised, a crown to protect the tooth.",
    ],
  },
  {
    title: "Dental implant",
    steps: [
      "CBCT 3-D scan and planning of implant size and position.",
      "Implant placement under local anaesthesia.",
      "Healing period of about 3 months while the implant joins the bone.",
      "Impression and fitting of the crown.",
      "Review visits and cleaning to keep the implant healthy.",
    ],
  },
];

export const portalSteps = [
  ["The doctor switches on your portal", "At your visit, the doctor turns on online access for your registered mobile number."],
  ["The doctor chooses what to share", "Visit summaries, prescriptions, X-rays, scans and receipts — only what the doctor shares appears online."],
  ["You log in with your mobile number", "We send a 6-digit code by SMS. No password to remember."],
];