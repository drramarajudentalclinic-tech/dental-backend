/* Makes the website's photos smaller so pages open faster on mobile data.
   - looks at every .jpg / .jpeg / .png / .webp in website/src and website/public
   - shrinks very large photos to at most 1600 px wide/high
   - re-saves them in the SAME name and format (so no code changes are needed)
   - keeps a file only if it really got smaller
   - copies every original to E:\website-image-backup first (outside the git folder)

   Run once from E:\backend\website :
     npm install --save-dev sharp
     node scripts/optimize-images.mjs
*/
import { readdir, stat, readFile, writeFile, mkdir } from "node:fs/promises";
import path from "node:path";
import { fileURLToPath } from "node:url";
import sharp from "sharp";

const ROOT = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "..");
const BACKUP = path.resolve(ROOT, "..", "..", "website-image-backup");
const FOLDERS = ["src", "public"].map((f) => path.join(ROOT, f));
const EXT = new Set([".jpg", ".jpeg", ".png", ".webp"]);
const MAX_SIDE = 1600;
const MIN_BYTES = 60 * 1024; // leave small files (icons, logos) alone

async function* walk(dir) {
  let items = [];
  try { items = await readdir(dir, { withFileTypes: true }); } catch { return; }
  for (const it of items) {
    const p = path.join(dir, it.name);
    if (it.isDirectory()) { if (it.name !== "node_modules" && !it.name.startsWith(".")) yield* walk(p); }
    else if (EXT.has(path.extname(it.name).toLowerCase())) yield p;
  }
}

const kb = (n) => (n / 1024).toFixed(0) + " KB";
let before = 0, after = 0, changed = 0;

for (const folder of FOLDERS) {
  for await (const file of walk(folder)) {
    const size = (await stat(file)).size;
    if (size < MIN_BYTES) continue;
    const input = await readFile(file);
    const ext = path.extname(file).toLowerCase();
    let img = sharp(input, { failOn: "none" }).rotate().resize({ width: MAX_SIDE, height: MAX_SIDE, fit: "inside", withoutEnlargement: true });
    if (ext === ".png") img = img.png({ compressionLevel: 9, adaptiveFiltering: true, palette: true, quality: 90, effort: 10 });
    else if (ext === ".webp") img = img.webp({ quality: 80, effort: 6 });
    else img = img.jpeg({ quality: 80, mozjpeg: true, progressive: true });
    const out = await img.toBuffer();
    const rel = path.relative(ROOT, file);
    if (out.length < size * 0.9) {
      const back = path.join(BACKUP, rel);
      await mkdir(path.dirname(back), { recursive: true });
      await writeFile(back, input);
      await writeFile(file, out);
      before += size; after += out.length; changed++;
      console.log(`smaller  ${rel}  ${kb(size)} -> ${kb(out.length)}`);
    } else {
      console.log(`kept     ${rel}  ${kb(size)} (already small enough)`);
    }
  }
}
console.log(`\nDone. ${changed} images made smaller: ${kb(before)} -> ${kb(after)}.`);
if (changed) console.log(`Originals copied to ${BACKUP}`);
