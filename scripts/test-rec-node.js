const { execSync } = require('child_process');
try {
  const out = execSync('where rec', { encoding: 'utf8' });
  console.log('NODE where rec: OK\n' + out.trim().split('\n')[0]);
  process.exit(0);
} catch (e) {
  console.log('NODE where rec: FAIL', e.message);
  process.exit(1);
}
