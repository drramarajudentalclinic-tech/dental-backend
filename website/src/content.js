/* ═══════════════════════════════════════════════════════════════════
   ALL WEBSITE TEXT LIVES HERE.
   Change words, phone numbers, timings, equipment and protocols in this
   one file — the pages pick them up automatically.

   Anything written inside [square brackets] is a placeholder that is
   waiting for the clinic's real details. The site shows a small yellow
   "draft" strip at the top while any placeholder is left.

   Dental Council of India advertising rules: keep everything factual.
   No "best", "No.1", "painless guarantee", prices-as-offers, patient
   testimonials or before/after photos of identifiable patients.
   ═══════════════════════════════════════════════════════════════════ */

export const clinic = {
  name: "Sri Satya Sai Oral Health Center & Dental Clinic",
  shortName: "Sri Satya Sai Dental",
  tagline: "General and specialist dental care, planned with digital records and explained before we begin.",
  phone: "[+91 00000 00000]",
  whatsapp: "[+91 00000 00000]",
  email: "drramarajudentalclinic@gmail.com",
  address: ["[Door no., street]", "[Area, town]", "[District, Andhra Pradesh – PIN]"],
  mapsLink: "",          // paste the Google Maps "Share → Copy link" here
  hours: [
    ["Monday – Saturday", "[10:00 am – 1:30 pm, 5:00 pm – 9:00 pm]"],
    ["Sunday", "[By appointment]"],
  ],
  registration: "[Dental Council registration no.]",
};

export const doctors = [
  {
    name: "Dr. Rama Raju",
    qualification: "[BDS, MDS – speciality]",
    role: "[Chief dental surgeon]",
    about: "[Two or three factual lines: years in practice, areas of special interest, training.]",
  },
];

/* What patients come for — shown as a plain list, no prices. */
export const services = [
  ["Check-ups and cleaning", "Examination, scaling and polishing, fluoride and sealants for children."],
  ["Fillings", "Tooth-coloured composite fillings matched to the shade of your tooth."],
  ["Root canal treatment", "Single- and multiple-visit root canals with rotary instruments and electronic length measurement."],
  ["Crowns and bridges", "Metal-ceramic, zirconia and all-ceramic crowns; bridges to replace missing teeth."],
  ["Dental implants", "Implant planning on a 3-D CBCT scan before surgery, then the crown on top."],
  ["Extractions and minor surgery", "Including wisdom teeth, under local anaesthesia."],
  ["Gum treatment", "Deep cleaning, gum surgery and maintenance for bleeding or loose gums."],
  ["Braces and aligners", "Fixed braces and clear aligners for teeth alignment."],
  ["Dentures", "Complete and partial dentures, flexible dentures, implant-supported dentures."],
  ["Children's dentistry", "Gentle first visits, fillings and pulp treatment for milk teeth."],
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
  {
    name: "[Add or remove equipment]",
    what: "[e.g. dental laser, intra-oral scanner, piezo surgery unit, digital shade guide]",
    why: "[What it changes for the patient, in one line.]",
  },
];

/* Protocols — these really are sequences, so they are shown as numbered steps. */
export const protocols = [
  {
    title: "Sterilisation of every instrument",
    steps: [
      "Used instruments are soaked in disinfectant and cleaned [in an ultrasonic cleaner].",
      "They are packed in sealed sterilisation pouches with an indicator strip.",
      "The pouches go through a [Class B vacuum] autoclave cycle.",
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
      "Local anaesthesia and isolation of the tooth [with a rubber dam].",
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
      "Healing period of about [3 months] while the implant joins the bone.",
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
