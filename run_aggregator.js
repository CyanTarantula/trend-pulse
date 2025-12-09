const { spawn } = require('child_process');
const path = require('path');
require('dotenv').config({ path: path.join(__dirname, 'src/web/.env.local') });

console.log("Loaded Env from src/web/.env.local");
console.log("SHEET_ID present:", !!process.env.SHEET_ID);
console.log("CREDS_JSON present:", !!process.env.GOOGLE_SERVICE_ACCOUNT_JSON);

if (process.env.GOOGLE_SERVICE_ACCOUNT_JSON) {
    console.log("CREDS_JSON length:", process.env.GOOGLE_SERVICE_ACCOUNT_JSON.length);
}

const python = spawn('python', ['src/scripts/get_trends.py'], {
    stdio: 'inherit',
    env: { ...process.env } // Pass loaded env to python
});

python.on('close', (code) => {
    console.log(`Python script exited with code ${code}`);
});
