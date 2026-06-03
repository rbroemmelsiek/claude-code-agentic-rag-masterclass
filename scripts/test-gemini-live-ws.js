/**
 * Tests Gemini Live transcription WebSocket (same as gemini-cli voice backend).
 * Run: node scripts/test-gemini-live-ws.js
 */
const fs = require('fs');
const path = require('path');

function loadApiKey() {
  const envPath = path.join(process.env.USERPROFILE, '.gemini', '.env');
  if (!fs.existsSync(envPath)) throw new Error('Missing ~/.gemini/.env');
  for (const line of fs.readFileSync(envPath, 'utf8').split(/\r?\n/)) {
    const m = line.match(/^\s*GEMINI_API_KEY\s*=\s*(.+)\s*$/);
    if (m) return m[1].trim();
  }
  throw new Error('GEMINI_API_KEY not in .env');
}

const apiKey = loadApiKey();
const modelName = 'gemini-3.1-flash-live-preview';
const baseUrl =
  'wss://generativelanguage.googleapis.com/ws/google.ai.generativelanguage.v1beta.GenerativeService.BidiGenerateContent';
const url = `${baseUrl}?key=${apiKey}`;

const timeout = setTimeout(() => {
  console.error('FAIL: timeout waiting for setupComplete (15s)');
  process.exit(1);
}, 15000);

const ws = new WebSocket(url, { maxPayload: 1 << 20 });

ws.addEventListener('open', () => {
  ws.send(
    JSON.stringify({
      setup: {
        model: `models/${modelName}`,
        generation_config: { response_modalities: ['audio'] },
        input_audio_transcription: {},
      },
    }),
  );
});

ws.addEventListener('message', (event) => {
  try {
    const msg = JSON.parse(event.data.toString());
    if (msg.setupComplete) {
      clearTimeout(timeout);
      console.log('OK: Live API setupComplete');
      ws.close();
      process.exit(0);
    }
    if (msg.error) {
      clearTimeout(timeout);
      console.error('FAIL: server error', JSON.stringify(msg.error));
      process.exit(1);
    }
  } catch (e) {
    clearTimeout(timeout);
    console.error('FAIL: parse', e.message);
    process.exit(1);
  }
});

ws.addEventListener('error', () => {
  clearTimeout(timeout);
  console.error('FAIL: WebSocket error (check API key / network / model access)');
  process.exit(1);
});

ws.addEventListener('close', (event) => {
  if (event.code !== 1000 && event.code !== 1005) {
    clearTimeout(timeout);
    const reason = event.reason || '(no reason)';
    console.error(`FAIL: WebSocket closed code=${event.code}`);
    console.error(`Reason: ${reason}`);
    if (/generativelanguage|not been used|disabled/i.test(reason)) {
      console.error(
        'Enable Generative Language API: https://console.cloud.google.com/apis/library/generativelanguage.googleapis.com',
      );
    }
    process.exit(1);
  }
});
