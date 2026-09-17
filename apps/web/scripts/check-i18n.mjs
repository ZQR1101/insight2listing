import fs from "fs";
import path from "path";

const messages = {
  en: JSON.parse(fs.readFileSync("messages/en.json", "utf8")),
  "zh-CN": JSON.parse(fs.readFileSync("messages/zh.json", "utf8")),
};

function collect(dir) {
  return fs.readdirSync(dir, { withFileTypes: true }).flatMap((e) => {
    const p = path.join(dir, e.name);
    if (e.isDirectory()) return collect(p);
    if (!/\.(tsx|ts)$/.test(e.name)) return [];
    return [p];
  });
}

function lookup(msgs, dotted) {
  return dotted.split(".").reduce((acc, part) => (acc == null ? undefined : acc[part]), msgs);
}

let problems = 0;
for (const file of [...collect("components"), ...collect("app"), ...collect("hooks")]) {
  const src = fs.readFileSync(file, "utf8");
  const bindings = [...src.matchAll(/const\s+(\w+)\s*=\s*useTranslations\("([^"]+)"\)/g)];
  if (!bindings.length) continue;
  for (const [, varName, ns] of bindings) {
    const callRe = new RegExp(`\b${varName}\("([a-zA-Z0-9_.]+)"\)`, "g");
    for (const [, key] of src.matchAll(callRe)) {
      const full = `${ns}.${key}`;
      for (const [locale, msgs] of Object.entries(messages)) {
        if (lookup(msgs, full) === undefined) {
          console.log(`MISSING ${locale}: ${full}  (${file})`);
          problems++;
        }
      }
    }
  }
}
console.log(problems ? `${problems} missing key(s)` : "all translation keys resolved in both locales");
process.exit(problems ? 1 : 0);
