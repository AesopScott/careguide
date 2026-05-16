import admin from 'firebase-admin';
import { readFileSync } from 'fs';

// Uses Application Default Credentials (firebase CLI login)
admin.initializeApp({
  credential: admin.credential.applicationDefault(),
  projectId: 'careguide-def76',
});

const uid   = process.argv[2];
const claims = JSON.parse(process.argv[3]);

if (!uid) {
  console.error('Usage: node set-claims.mjs <uid> \'{"practitioner":true}\'');
  process.exit(1);
}

await admin.auth().setCustomUserClaims(uid, claims);
console.log(`✓ Custom claims set on ${uid}:`, claims);

// Also update Firestore status to active
const db = admin.firestore();
await db.collection('users').doc(uid).update({ status: 'active' });
console.log(`✓ Firestore status set to active`);

process.exit(0);
