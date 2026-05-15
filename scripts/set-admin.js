// Run once to set admin: true claim on a Firebase user.
// Usage: node scripts/set-admin.js ravenshroud@gmail.com

const admin = require('firebase-admin');
const serviceAccount = require('../config/careguide-adminsdk.json');

admin.initializeApp({ credential: admin.credential.cert(serviceAccount) });

const email = process.argv[2];
if (!email) { console.error('Usage: node scripts/set-admin.js <email>'); process.exit(1); }

admin.auth().getUserByEmail(email)
  .then(user => admin.auth().setCustomUserClaims(user.uid, { admin: true }).then(() => user))
  .then(user => {
    console.log(`✓ admin:true set on ${email} (uid: ${user.uid})`);
    console.log('Sign out and back in on the site to pick up the new claim.');
    process.exit(0);
  })
  .catch(e => { console.error(e.message); process.exit(1); });
