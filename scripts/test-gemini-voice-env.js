// Simulates Gemini CLI child process environment after gemini-voice.ps1
const { execSync, spawn } = require('child_process');
const soxDir = 'C:\\Users\\rmbsa\\AppData\\Local\\Microsoft\\WinGet\\Packages\\ChrisBagwell.SoX_Microsoft.Winget.Source_8wekyb3d8bbwe\\sox-14.4.2';

function loadEnv() {
  const fs = require('fs');
  const path = require('path');
  const envPath = path.join(process.env.USERPROFILE, '.gemini', '.env');
  if (!fs.existsSync(envPath)) return;
  for (const line of fs.readFileSync(envPath, 'utf8').split(/\r?\n/)) {
    const m = line.match(/^\s*GEMINI_API_KEY\s*=\s*(.+)\s*$/);
    if (m) process.env.GEMINI_API_KEY = m[1].trim();
  }
}

process.env.AUDIODRIVER = 'waveaudio';
process.env.Path = soxDir + ';' + (process.env.APPDATA + '\\npm') + ';' + process.env.Path;
loadEnv();

let ok = true;
try {
  execSync('where rec', { stdio: 'pipe' });
  console.log('OK: where rec');
} catch {
  console.log('FAIL: where rec');
  ok = false;
}

if (!process.env.GEMINI_API_KEY) {
  console.log('FAIL: GEMINI_API_KEY missing');
  ok = false;
} else {
  console.log('OK: GEMINI_API_KEY length', process.env.GEMINI_API_KEY.length);
}

const recPath = soxDir + '\\rec.exe';
let bytes = 0;
const p = spawn(recPath, ['-q', '-V0', '-e', 'signed', '-c', '1', '-b', '16', '-r', '16000', '-t', 'raw', '-'], {
  env: process.env,
});
p.stdout.on('data', (d) => { bytes += d.length; });
setTimeout(() => {
  p.kill('SIGTERM');
  setTimeout(() => {
    console.log(bytes > 500 ? 'OK: raw mic capture ' + bytes + ' bytes' : 'FAIL: raw capture ' + bytes + ' bytes');
    process.exit(ok && bytes > 500 ? 0 : 1);
  }, 500);
}, 1500);
