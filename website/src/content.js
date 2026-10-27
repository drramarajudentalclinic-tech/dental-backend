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
  tagline: "Complete dental care in Chaitanyapuri, Hyderabad, led by a specialist in oral medicine and radiology with 25 years of experience. Every treatment is explained before we begin.",
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
      ["25", "years in practice"],
      ["MDS", "Oral Medicine & Radiology"],
      ["IDA", "Member, Indian Dental Association"],
    ],
    about: [
      "Dr. D. Rama Raju holds a master's degree in Oral Medicine and Radiology, the speciality that deals with diagnosing diseases of the mouth, jaws and face and with reading dental X-rays and scans. He has practised dentistry for 25 years and runs Sri Satya Sai Oral Health Center & Dental Clinic in Chaitanyapuri, near Dilsukhnagar, Hyderabad.",
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
      ["Today", "25 years in practice", "Sri Satya Sai Oral Health Center & Dental Clinic, Chaitanyapuri"],
    ],
  },
];

/* What patients come for — shown as a plain list, no prices. */
export const services = [
  ["Check-ups and cleaning", "Examination, scaling and polishing (oral prophylaxis), fluoride application and pit-and-fissure sealants.", "Oral prophylaxis (scaling and polishing)"],
  ["Fillings", "Tooth-coloured composite and glass-ionomer (GIC) fillings matched to the shade of your tooth.", "Composite (tooth-coloured) fillings"],
  ["Root canal treatment", "Single- and multiple-visit root canals with rotary files, apex locator and warm 3-D gutta-percha filling; re-treatment of old root canals.", "Root canal treatment"],
  ["Crowns and bridges", "Zirconia, all-ceramic and metal-ceramic crowns and bridges, made from a digital scan of your teeth.", "Crowns and bridges"],
  ["Dental implants", "Single and multiple implants planned on a CBCT scan and placed with a surgical guide; Straumann, Nobel Biocare, Osstem, DIO, Neo Biotech, Noris, Adin and Alpha-Bio systems.", "Dental implant with a surgical guide"],
  ["Complete dentures", "Full dentures for patients with no teeth, made from accurate impressions and a measured bite; implant-supported dentures for a firmer hold.", "Complete dentures"],
  ["Partial dentures", "Cast metal, flexible and acrylic partial dentures that replace some missing teeth.", "Partial dentures"],
  ["Veneers and laminates", "Thin porcelain or composite shells bonded to the front of the teeth to improve shape, colour and gaps, with little or no shaping of the tooth.", "Veneers and laminates"],
  ["Braces and aligners", "Fixed metal and ceramic braces, and clear aligners planned from a digital scan.", "Braces and clear aligners"],
  ["Tooth extraction", "Gentle removal of teeth that cannot be saved, with socket grafting from your own tooth when an implant is planned.", "Tooth extraction"],
  ["Wisdom tooth removal", "Removal of impacted or decayed wisdom teeth, with PRF from your own blood where healing needs support.", "Wisdom tooth removal"],
  ["Gum treatment and flap surgery", "Curettage, flap surgery and laser-assisted flap surgery for bleeding, swollen or loose gums, with bone grafts and PRF where bone is lost.", "Flap surgery"],
  ["Laser dentistry", "Laser gum treatment and low-level laser therapy for painful ulcers, sensitivity, jaw pain and healing after surgery.", "Low-level laser therapy (LLLT)"],
  ["Oral lesions and oral cancer screening", "Check-ups for white or red patches, non-healing ulcers and lumps with the DrOroscope; burning mouth and facial pain.", "Oral lesions (patches, ulcers and lumps)"],
  ["Bone grafts and PRF", "Bone grafts made from your own extracted tooth (Tooth Titan) and platelet-rich fibrin (PRF) from your own blood, for sockets, implants and gum surgery."],
  ["Oral rehabilitation", "Full-mouth rehabilitation for worn, broken or missing teeth, restoring chewing and bite together."],
  ["Dental X-rays and scans", "Digital X-rays at the clinic; OPG and CBCT scans at an imaging centre when needed, read and explained by the doctor, a specialist in oral radiology."],
  ["Children's dentistry", "Gentle first visits, fillings, pulp treatment for milk teeth and space maintainers."],
  ["Bite problems, jaw pain and sensitivity", "Digital bite analysis with the Teeth Tracer for jaw-joint (TMJ) pain, headaches, teeth grinding and wear; night guards; sensitive teeth and bad breath."],
  ["Teeth whitening and smile design", "Whitening, reshaping and bonding to improve the look of your smile."],
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
        why: "Healthy lining glows green while suspicious areas look darker, so early changes in patches, ulcers and lumps are found without cutting, and it helps decide which areas need a biopsy. The photos are kept in your record to compare at the next visit.",
      },
      {
        name: "Digital X-rays (RVG)",
        photo: photos.rvg,
        art: "rvg",
        what: "A small sensor replaces film; the picture appears on screen in seconds.",
        why: "Much lower radiation than film, and we zoom in and show you the picture on the screen.",
      },
      {
        name: "Intra-oral camera",
        photo: photos.camera,
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
        photo: photos.apex,
        art: "apex",
        what: "An electronic device that measures the exact length of each root canal.",
        why: "Accurate cleaning to the tip of the root, with fewer X-rays during treatment.",
      },
      {
        name: "Endo motor and rotary files",
        photo: photos.endoMotor,
        art: "rotary",
        what: "A cordless endo motor that turns nickel-titanium files at a controlled speed and force to clean and shape the canals.",
        why: "Quicker, more even cleaning of curved canals than hand files alone.",
      },
      {
        name: "Obturation pen",
        photo: photos.obturationPen,
        art: "obturationPen",
        what: "A heated tip that softens gutta-percha (the rubber-like root filling) and presses it down the canal.",
        why: "The warm filling flows into side canals and gaps, so the root is sealed in three dimensions.",
      },
      {
        name: "Cicada DT Fill thermal obturator",
        photo: photos.cicada,
        art: "obturationGun",
        what: "A cordless gun that fills the rest of the canal with warm, flowing gutta-percha (gutta-percha backfill).",
        why: "A dense, gap-free seal from the tip of the root to the top, which helps keep bacteria out.",
      },
    ],
  },
  {
    treatment: "Comfortable injections",
    items: [
      {
        name: "Anaesthesia booster",
        photo: photos.anaesthesia,
        art: "anaesthesia",
        what: "A cordless device that delivers the local anaesthetic from the cartridge in a slow, steady flow.",
        why: "Makes numbing gentler and more comfortable, especially for anxious patients and children.",
      },
    ],
  },
  {
    treatment: "Crowns, bridges, aligners and dentures",
    items: [
      {
        name: "Runyes 3DS V3 Pro intra-oral scanner",
        photo: photos.runyes,
        art: "scanner",
        what: "A wand that takes a 3-D digital scan of your teeth instead of a putty impression.",
        why: "No gagging on impression trays; an accurate digital model is sent to the lab for crowns, bridges, clear aligners and dentures.",
      },
      {
        name: "Aluminium-oxide micro-blaster",
        photo: photos.blaster,
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
        photo: photos.guide,
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
        photo: photos.implant,
        art: "implant",
        what: "Straumann (Switzerland), Nobel Biocare NobelActive and NobelReplace, Osstem, DIO and Neo Biotech (South Korea), and Noris Medical, Adin and Alpha-Bio Tec (Israel).",
        why: "The implant is chosen for your bone, the position of the tooth and your budget, and the parts stay available for years.",
      },
    ],
  },
  {
    treatment: "Gum treatment and laser",
    items: [
      {
        name: "Dental laser",
        art: "laser",
        what: "A dental laser that works as a fine beam of light: at higher power for gum treatment, at low power for laser therapy.",
        why: "Laser gum treatment removes infected tissue with less bleeding, and low-level laser therapy helps ulcers, sensitivity and soreness after surgery heal more comfortably.",
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
        why: "Used where needed: teeth that hit too hard show up on the screen, which helps find causes of jaw-joint (TMJ) pain, headaches and tooth wear, and fine-tune the bite in complex cases.",
      },
    ],
  },
  {
    treatment: "Your records",
    items: [
      {
        name: "Digital patient records and patient portal",
        photo: photos.records,
        art: "records",
        what: "Every visit, prescription, X-ray and scan is stored in one record for each patient.",
        why: "Nothing is lost between visits, and the doctor can share your records with you online.",
      },
    ],
  },
];

/* Treatment protocols — real sequences, so they are shown as numbered steps.
   `group` sorts them in the list.
   `uses`: [equipment, what it is used for in this treatment, true = only where needed]. */
export const protocols = [
  {
    group: "Before any treatment",
    title: "Sterilisation of every instrument",
    uses: [],
    steps: [
      "Used instruments are soaked in disinfectant and cleaned.",
      "They are packed in sealed sterilisation pouches with an indicator strip.",
      "The pouches go through a steam autoclave cycle.",
      "Pouches are opened in front of you, at the chair, for your treatment.",
      "Single-use items (needles, gloves, suction tips, cups) are used once and discarded.",
    ],
  },
  {
    group: "Before any treatment",
    title: "Your first visit",
    uses: [
      ["Intra-oral camera", "Photos of your teeth on the screen, so you see what the doctor sees"],
      ["Digital X-ray (RVG)", "X-rays where needed, with low radiation"],
      ["DrOroscope", "Oral cancer screening if you have a risk factor or a suspicious area", true],
    ],
    steps: [
      "Medical history, allergies and current medicines are recorded.",
      "Examination of teeth, gums, tongue and jaw joint, with intra-oral camera photos you can see on the screen.",
      "Where needed (for example, if you use tobacco or have a patch or ulcer), oral cancer screening with the DrOroscope.",
      "Digital X-rays where needed; an OPG or CBCT scan at an imaging centre only if it is needed for a diagnosis.",
      "We explain what we found, the treatment options and the cost before starting anything.",
      "A written prescription where needed, and a date for the next visit.",
    ],
  },

  {
    group: "Saving your teeth",
    title: "Root canal treatment",
    uses: [
      ["Digital X-ray (RVG)", "Shows the root shape and infection; checks the length and the final seal"],
      ["Anaesthesia booster", "Gives the numbing injection slowly and steadily"],
      ["Apex locator", "Measures the exact length of each canal"],
      ["Endo motor", "Turns the rotary files that clean and shape the canals"],
      ["Obturation pen", "Packs warm gutta-percha at the root tip"],
      ["Cicada DT Fill", "Fills the rest of the canal with warm gutta-percha"],
      ["Runyes scanner", "Digital scan for the crown, where a crown is advised", true],
      ["Micro-blaster", "Cleans the inside of the crown before cementing", true],
    ],
    steps: [
      "Digital X-ray (RVG) to see the root shape, the number of canals and the infection.",
      "Local anaesthesia given slowly with the anaesthesia booster; the tooth is isolated to keep it clean and dry.",
      "The canals are opened and their exact length is measured with the apex locator, confirmed on an X-ray.",
      "Cleaning and shaping with nickel-titanium rotary files on the endo motor, with disinfecting rinses between files.",
      "Three-dimensional sealing: the obturation pen packs warm gutta-percha at the root tip, and the Cicada DT Fill fills the rest of the canal.",
      "A final X-ray to check the seal, and a filling to close the tooth.",
      "Where advised, a crown: a digital scan with the Runyes scanner, and the crown cleaned with the micro-blaster before cementing.",
    ],
  },
  {
    group: "Saving your teeth",
    title: "Crowns and bridges",
    uses: [
      ["Intra-oral camera", "Photos to match the shade"],
      ["Anaesthesia booster", "Numbing before the tooth is shaped"],
      ["Runyes scanner", "3-D digital scan instead of an impression tray"],
      ["Micro-blaster", "Cleans and roughens the inside of the crown so the cement holds firmly"],
    ],
    steps: [
      "The tooth is checked on an X-ray and, if needed, treated first (filling or root canal).",
      "The tooth is shaped under local anaesthesia, given with the anaesthesia booster.",
      "A 3-D digital scan with the Runyes intra-oral scanner (no impression trays), and the shade is matched with photos.",
      "A temporary crown protects the tooth while the lab makes the final crown or bridge.",
      "Try-in to check fit, bite and shade.",
      "The inside of the crown is cleaned with the aluminium-oxide micro-blaster so the cement holds firmly.",
      "The crown is cemented and the bite is checked and adjusted.",
    ],
  },

  {
    group: "Saving your teeth",
    title: "Composite (tooth-coloured) fillings",
    uses: [
      ["Intra-oral camera", "Photos of the decay and of the finished filling"],
      ["Digital X-ray (RVG)", "Shows how deep the decay goes", true],
      ["Anaesthesia booster", "Numbing for deeper cavities", true],
    ],
    steps: [
      "The tooth is examined with intra-oral camera photos and, where needed, a digital X-ray to see how deep the decay goes.",
      "The shade is matched to your tooth before treatment starts.",
      "Local anaesthesia where needed, given slowly with the anaesthesia booster.",
      "The decay is removed and the cavity shaped, keeping as much healthy tooth as possible.",
      "The tooth is kept dry; it is etched, rinsed, and a bonding agent is applied and hardened with a curing light.",
      "Composite is placed in thin layers, each hardened with the curing light, and shaped like the natural tooth.",
      "The bite is checked and adjusted, and the filling polished smooth.",
    ],
  },
  {
    group: "Saving your teeth",
    title: "Glass-ionomer (GIC) fillings",
    uses: [
      ["Intra-oral camera", "Photos of the tooth before and after"],
      ["Digital X-ray (RVG)", "Shows how deep the decay goes", true],
    ],
    steps: [
      "Used for milk teeth, cavities near the gum line or on the roots, as a base under other fillings, and as a temporary filling.",
      "The tooth is examined, with a digital X-ray where needed.",
      "The decay is removed; small cavities often need little or no anaesthesia.",
      "The cavity is cleaned with a conditioner so the glass-ionomer bonds to the tooth.",
      "The glass-ionomer is placed and shaped; it sets on its own (or with a curing light for the resin-modified type).",
      "A protective coat is applied and the bite is checked.",
      "Avoid eating for about an hour. Glass-ionomer releases fluoride, which helps protect the tooth from new decay.",
    ],
  },
  {
    group: "Gum treatment and laser",
    title: "Oral prophylaxis (scaling and polishing)",
    uses: [
      ["Intra-oral camera", "Shows you the tartar and the areas to brush better"],
    ],
    steps: [
      "Examination of teeth, gums and the lining of the mouth.",
      "Ultrasonic scaling removes tartar and stains above and just below the gum line.",
      "Hand instruments clean the areas the ultrasonic tip cannot reach.",
      "Polishing makes the tooth surfaces smooth, so plaque collects less.",
      "Fluoride application where advised, especially for children and sensitive teeth.",
      "Brushing and flossing advice for your teeth, with photos to show the problem areas.",
      "A recall visit, usually every 6 months.",
    ],
  },
  {
    group: "Gum treatment and laser",
    title: "Curettage (deep cleaning of gum pockets)",
    uses: [
      ["Digital X-ray (RVG)", "Checks the bone around the teeth"],
      ["Anaesthesia booster", "Numbing before cleaning the pockets"],
      ["Dental laser", "Removes the infected lining of the pocket", true],
    ],
    steps: [
      "Gum pockets are measured and recorded, with X-rays to check the bone.",
      "Scaling and root planing first, to clean the root surfaces.",
      "Local anaesthesia with the anaesthesia booster.",
      "The infected inner lining of the gum pocket is gently removed, by hand or with the dental laser.",
      "The pocket is rinsed clean and the gum pressed back against the tooth.",
      "Mouthwash and home-care instructions; a review visit to re-measure the pockets.",
    ],
  },
  {
    group: "Gum treatment and laser",
    title: "Flap surgery",
    uses: [
      ["Digital X-ray (RVG)", "Checks the bone loss before and after"],
      ["Anaesthesia booster", "Numbing before surgery"],
      ["PRFuge", "PRF from your own blood to support healing and grafts", true],
      ["Tooth Titan", "Graft from your own tooth, when a tooth is being removed", true],
    ],
    steps: [
      "Gum pockets are measured and X-rays taken; scaling and root planing are done first, and the gums re-checked after a few weeks.",
      "If deep pockets remain, surgery is planned under local anaesthesia, given with the anaesthesia booster.",
      "The gum is gently lifted (a flap) so the roots and bone can be seen and cleaned thoroughly.",
      "Infected tissue is removed and the bone is smoothed.",
      "Where bone has been lost, a bone graft with PRF (made from your own blood with the PRFuge) helps it heal; graft from your own tooth (Tooth Titan) is used when a tooth is being removed.",
      "The gum is stitched back in place.",
      "Medicines and care instructions; stitches removed after 7–10 days; gum maintenance every 3–6 months.",
    ],
  },
  {
    group: "Gum treatment and laser",
    title: "Flap surgery with laser",
    uses: [
      ["Digital X-ray (RVG)", "Checks the bone loss before and after"],
      ["Anaesthesia booster", "Numbing before surgery"],
      ["Dental laser", "Removes infected tissue, reduces bacteria and helps control bleeding"],
      ["PRFuge", "PRF from your own blood with bone grafts", true],
    ],
    steps: [
      "The same assessment as for flap surgery: pocket measurements, X-rays and scaling first.",
      "Local anaesthesia with the anaesthesia booster.",
      "The dental laser removes the infected lining of the pocket and reduces bacteria on the gum and root surfaces.",
      "The roots are cleaned and smoothed; bone grafting with PRF where needed.",
      "The gum is placed back and stitched where needed; the laser also helps control bleeding.",
      "Low-level laser therapy after surgery may be used for comfort and healing.",
      "Care instructions, a review visit and regular gum maintenance.",
    ],
  },
  {
    group: "Gum treatment and laser",
    title: "Low-level laser therapy (LLLT)",
    uses: [
      ["Dental laser", "Low-power light that supports healing and eases pain, without cutting"],
    ],
    steps: [
      "Used for painful mouth ulcers, soreness after extraction or surgery, sensitive teeth, jaw-joint (TMJ) pain and pain from braces.",
      "The cause is diagnosed first; laser therapy supports other treatment rather than replacing it.",
      "You and the team wear protective glasses.",
      "The laser is used at a low power over the area for a short time. It does not cut or heat the tissue.",
      "Several short sessions may be needed, a few days apart.",
      "The area is reviewed at each visit to see how it is healing.",
    ],
  },

  {
    group: "Replacing missing teeth",
    title: "Dental implant with a surgical guide",
    uses: [
      ["Runyes scanner", "Digital scan for planning, and later for the crown"],
      ["Surgical guide", "Places the implant in the planned position, depth and angle"],
      ["Implant systems", "The implant chosen for your bone and budget"],
      ["Anaesthesia booster", "Numbing before the implant is placed"],
      ["PRFuge", "PRF from your own blood to support healing", true],
      ["Tooth Titan", "Graft from your own extracted tooth where bone is thin", true],
      ["Micro-blaster", "Cleans the inside of a cemented crown (not needed for screw-retained crowns)", true],
      ["Teeth Tracer", "Fine-tunes the bite on the implant crown", true],
    ],
    steps: [
      "Examination, medical history, a CBCT scan at an imaging centre and a digital scan of your teeth with the Runyes scanner.",
      "Digital planning of implant size, position and angle, and a 3-D printed surgical guide.",
      "The implant system is chosen for your bone and budget (Straumann, Nobel Biocare, Osstem, DIO, Neo Biotech, Noris, Adin or Alpha-Bio).",
      "Local anaesthesia with the anaesthesia booster, and the implant placed through the guide.",
      "Only where bone is thin or healing needs support: a graft from your own extracted tooth (Tooth Titan) and PRF from your own blood (PRFuge).",
      "Healing period of about 3 months while the implant joins the bone (longer if grafted).",
      "A digital scan of the implant, then the crown is fitted: a screw-retained crown is screwed onto the implant, while a cemented crown is first cleaned inside with the micro-blaster. The bite is checked, with the Teeth Tracer where needed.",
      "Review visits and cleaning to keep the implant healthy.",
    ],
  },
  {
    group: "Replacing missing teeth",
    title: "Complete dentures",
    uses: [],
    steps: [
      "Examination of the gums and jaw ridges.",
      "First impressions, from which custom trays are made for your mouth.",
      "Final impressions that record the edges of the denture accurately, for a better fit.",
      "Bite record: the height and position of your jaws are measured so the dentures look natural and you chew comfortably.",
      "Tooth shade and shape are chosen with you.",
      "Wax try-in: you see and check the teeth before the denture is finished.",
      "The finished dentures are fitted, sore spots adjusted and the bite balanced.",
      "Review visits for adjustments, and advice on cleaning and night-time care. Implant-supported dentures are an option for a firmer hold.",
    ],
  },
  {
    group: "Replacing missing teeth",
    title: "Partial dentures",
    uses: [
      ["Digital X-ray (RVG)", "Checks the teeth that will hold the denture"],
      ["Runyes scanner", "Digital scan for the denture design", true],
    ],
    steps: [
      "The remaining teeth and gums are checked with X-rays; decay and gum problems are treated first.",
      "The type is chosen with you: cast metal, flexible or acrylic.",
      "Impressions or a digital scan with the Runyes scanner, and the design (clasps and rests) planned with the lab.",
      "For a cast partial denture, the metal framework is tried in first.",
      "Teeth try-in to check look, fit and bite.",
      "The denture is fitted, and the fit and bite are adjusted.",
      "Review visits, and advice on cleaning the denture and the teeth that hold it.",
    ],
  },

  {
    group: "Smile and alignment",
    title: "Veneers and laminates",
    uses: [
      ["Intra-oral camera", "Smile photos for planning and shade"],
      ["Runyes scanner", "Digital scan sent to the lab"],
      ["Anaesthesia booster", "Numbing if the teeth need shaping", true],
    ],
    steps: [
      "Smile assessment with photos, and a check that teeth and gums are healthy.",
      "Shade and shape are planned with you; a trial smile (mock-up) shows the result before any tooth is touched.",
      "Minimal shaping of the front surface of the teeth, often within the enamel; laminates need very little or no shaping.",
      "A digital scan with the Runyes scanner is sent to the lab; temporaries are placed if needed.",
      "Try-in to check colour and fit with you.",
      "The inside of each veneer is prepared, the tooth surface is conditioned, and the veneers are bonded in place.",
      "The bite is checked and the edges polished; a night guard is advised if you grind your teeth.",
    ],
  },
  {
    group: "Smile and alignment",
    title: "Braces and clear aligners",
    uses: [
      ["Intra-oral camera", "Photos to plan and follow progress"],
      ["Runyes scanner", "Digital scan for the treatment plan and the aligners"],
    ],
    steps: [
      "Consultation with face and teeth photos, and X-rays (OPG and cephalogram at an imaging centre).",
      "A digital scan with the Runyes scanner; the treatment plan and expected time are explained.",
      "Cleaning and treatment of any decay or gum problems before starting.",
      "Braces: brackets are bonded to the teeth and wires fitted, with adjustments about every 4–6 weeks.",
      "Clear aligners: a digital plan from your scan, and a series of aligners changed every 1–2 weeks, with regular check-ups.",
      "When the teeth are in place, the bite is checked and fine-tuned.",
      "Retainers keep the teeth from moving back; regular review visits.",
    ],
  },

  {
    group: "Oral surgery",
    title: "Tooth extraction",
    uses: [
      ["Digital X-ray (RVG)", "Shows the roots and nearby structures"],
      ["Anaesthesia booster", "Numbing before removal"],
      ["Tooth Titan", "Graft from the same tooth to preserve bone for a future implant", true],
      ["PRFuge", "PRF from your own blood to support healing", true],
    ],
    steps: [
      "X-ray of the tooth, and a check of your medical history and medicines (for example, blood thinners or diabetes).",
      "Local anaesthesia with the anaesthesia booster.",
      "The tooth is loosened and removed gently, keeping the surrounding bone.",
      "Only where needed, for example when an implant is planned: the socket is filled with graft made from the same tooth (Tooth Titan) and PRF from your own blood (PRFuge).",
      "Gauze pressure to stop bleeding, with written care instructions and medicines.",
      "A review visit if needed.",
    ],
  },
  {
    group: "Oral surgery",
    title: "Wisdom tooth removal",
    uses: [
      ["Digital X-ray (RVG)", "Shows the position of the tooth and its roots"],
      ["Anaesthesia booster", "Numbing before surgery"],
      ["PRFuge", "PRF from your own blood to support healing", true],
      ["Tooth Titan", "Graft from the tooth where bone needs rebuilding", true],
    ],
    steps: [
      "X-ray or OPG to see the position of the tooth; a CBCT scan at an imaging centre if the roots are close to the nerve.",
      "Local anaesthesia with the anaesthesia booster.",
      "A small opening in the gum; some bone may be removed and the tooth divided into pieces to take it out gently.",
      "The socket is cleaned. Where needed, PRF (PRFuge) is placed to support healing, and graft from the tooth (Tooth Titan) where bone needs rebuilding.",
      "Stitches, care instructions and medicines for pain and swelling.",
      "Review and stitch removal after about 7 days.",
    ],
  },

  {
    group: "Oral medicine",
    title: "Oral lesions (patches, ulcers and lumps)",
    uses: [
      ["DrOroscope", "Fluorescence screening and photos of the lesion"],
      ["Intra-oral camera", "Photos to compare at follow-up visits"],
      ["Dental laser", "Low-level laser therapy for painful ulcers", true],
    ],
    steps: [
      "History of the lesion and of habits such as tobacco, gutka, pan or alcohol.",
      "Examination of the whole mouth, tongue and neck.",
      "DrOroscope screening under white, blue and green-amber light; photos record the size and site.",
      "Possible causes are removed: a sharp tooth smoothed, an ill-fitting denture adjusted, habit counselling.",
      "A review in about 2 weeks to see whether the lesion is healing.",
      "If it persists or looks suspicious, a biopsy of the exact spot is advised to confirm the diagnosis.",
      "Treatment for the diagnosis (medicines, low-level laser therapy for painful ulcers, or referral), and follow-up photos compared at each visit.",
    ],
  },
];



export const portalSteps = [
  ["The doctor switches on your portal", "At your visit, the doctor turns on online access for your registered mobile number."],
  ["The doctor chooses what to share", "Visit summaries, prescriptions, X-rays, scans and receipts — only what the doctor shares appears online."],
  ["You log in with your mobile number", "We send a 6-digit code by SMS. No password to remember."],
];

/* Oral cancer screening with the DrOroscope — facts from the published studies. */
export const screening = {
  title: "Oral cancer screening with the DrOroscope",
  lead: "Oral cancer often starts as a painless white or red patch. Found early, these changes can be treated before they become cancer. Not every patient needs this test: when you have a risk factor or a suspicious area, the lining of your mouth is checked with the DrOroscope, a hand-held fluorescence camera made in India.",
  who: [
    "You use or have used tobacco, gutka, khaini, pan or betel nut, or you smoke",
    "You drink alcohol regularly",
    "A white or red patch, a lump, or a rough area in the mouth",
    "An ulcer or sore that has not healed in 2 weeks",
    "Burning in the mouth with spicy food, or the mouth opening less widely than before",
    "You are over 40 and would like a screening (ask at your visit)",
  ],
  how: [
    "A normal photo of each area of the mouth with the 5-megapixel camera, under white light.",
    "Blue light (400–460 nm) makes healthy lining glow green; areas with abnormal cells lose the glow and look dark.",
    "Green and amber light show the small blood vessels, which change in abnormal tissue.",
    "The pictures appear on a tablet, where software with artificial-intelligence features helps assess them. The doctor, a specialist in oral medicine and radiology, reads them with you.",
    "If an area looks suspicious, a biopsy of exactly that spot is advised to confirm it.",
    "The photos are saved in your record, so the same area is compared at your next visit.",
  ],
  benefits: [
    ["No pain, no cutting", "Light and a camera only. It takes a few minutes."],
    ["Earlier detection", "Changes in the lining show up before they are easy to see by eye."],
    ["The right spot for a biopsy", "When a biopsy is needed, the screening shows which area to test."],
    ["A record you can follow", "Photos from each visit are compared, so slow changes are not missed."],
  ],
  tech: [
    "Autofluorescence imaging with three light modes (white, blue, and green-amber)",
    "Slim 5-megapixel intra-oral camera that reaches the back of the mouth",
    "Tablet software with artificial-intelligence features, reports and stored records",
    "Made in India by Raamah Biocare, with a granted design patent",
  ],
  study: {
    stats: [["100%", "of the dysplasia confirmed by biopsy was picked up"], ["90%", "overall accuracy compared with biopsy"], ["40", "patients with red and white oral lesions, Hyderabad"]],
    text: "In a 2024 study of 40 patients with lesions such as leukoplakia and oral submucous fibrosis, every lesion was also biopsied. The DrOroscope picked up every case with dysplasia (sensitivity 100%) and was correct in 90% of patients overall. A larger study of 200 people reported 92.7% sensitivity and 88.5% accuracy.",
    caution: "The DrOroscope is a screening aid. Some areas it marks turn out to be harmless, so a biopsy is still the test that confirms a diagnosis.",
    sources: [
      ["Yeladandi M et al. Journal of Pharmacology and Pharmacotherapeutics, 2024", "https://journals.sagepub.com/doi/10.1177/0976500X241300758"],
      ["Illuminating Dysplasia: a prospective cohort study. Biomedical & Pharmacology Journal, 2025", "https://biomedpharmajournal.org/vol18no2/illuminating-dysplasia-a-novel-approach-using-droroscope-for-early-non-invasive-detection-a-prospective-cohort-study/"],
    ],
  },
};

/* Common questions — plain, factual answers. */
export const faqs = [
  ["Do I need an appointment?", "Yes. The clinic works by appointment only, Monday to Saturday, 11 am to 7 pm. Call or WhatsApp +91 99088 94449 to book a time. Sunday is a holiday."],
  ["Is root canal treatment painful?", "The tooth is numbed with local anaesthesia before treatment, so you should feel pressure but not pain. Some soreness for a day or two afterwards is common, and the doctor prescribes medicine for it."],
  ["How long does a dental implant take?", "The implant is placed in one sitting under local anaesthesia. It then needs about 3 months to join the bone before the crown is fitted. If a bone graft is needed, healing can take longer; the doctor explains the timeline for your case."],
  ["Is the oral cancer screening painful?", "No. The DrOroscope only shines light and takes photos of the inside of your mouth. It takes a few minutes, and is done when the doctor advises it or you ask for it."],
  ["What should I bring to my first visit?", "A list of the medicines you take, any medical reports, and any old dental X-rays or scans. If you have diabetes, blood pressure or heart problems, or are pregnant, please tell the doctor."],
  ["Can I see my X-rays and prescriptions later?", "Yes. When the doctor switches on your patient portal and shares them, you can see your visit summaries, prescriptions, X-rays and receipts on your phone."],
  ["How are instruments kept clean?", "Instruments are cleaned, sealed in sterilisation pouches and steam-autoclaved. The pouch is opened in front of you, and needles, gloves and suction tips are used once and thrown away."],
  ["When should a child first see a dentist?", "By the first birthday, or when the first tooth comes in. Early visits help catch decay in milk teeth and get children comfortable at the dentist."],
];