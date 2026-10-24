# Sri Satya Sai Oral Health Center & Dental Clinic — website + patient portal

* `/` — the clinic website (all text is in `src/content.js`)
* `/portal` — patient login (mobile number + SMS code)
* `/portal/record/<id>` — what the doctor has shared with that patient

## Run on your computer
    npm install
    npm run dev

## Render (Static Site)
* Build command: `npm install && npm run build`
* Publish directory: `dist`
* Environment: `VITE_API_URL = https://dental-backend-xojn.onrender.com/api`
* Redirects/Rewrites: Source `/*` → Destination `/index.html` → Action **Rewrite**
