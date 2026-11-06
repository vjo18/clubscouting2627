import test from 'node:test';
import assert from 'node:assert/strict';
import {missingBirthyearsCsv} from '../public/birthyear_csv.mjs';

test('Ontbrekende geboortejaren: hetzelfde formaat als scouting2627',()=>{
 const clubs=[{id:'a',name:'Sportkring Roeselare'}];
 const players=[{club_id:'a',name:'Matthias Deforche',birth_year:null},{club_id:'a',name:'Emiel Vanacker',birth_year:null},{club_id:'a',name:'Andere',birth_year:2001}];
 const csv=missingBirthyearsCsv(clubs,players);
 assert.ok(csv.startsWith('\uFEFFClubRBFA;Naam;Geboortejaar\r\n'));
 assert.ok(csv.includes('Sportkring Roeselare;Matthias Deforche;'));
 assert.ok(csv.includes('Sportkring Roeselare;Emiel Vanacker;'));
 assert.ok(!csv.includes('"Matthias Deforche"'));
 assert.ok(!csv.includes('Andere'));
});
test('Alleen cellen met scheidingstekens of quotes krijgen quotes',()=>{
 const csv=missingBirthyearsCsv([{id:'a',name:'FC; Voorbeeld'}],[{club_id:'a',name:'Jan "De Test"',birth_year:null}]);
 assert.ok(csv.includes('"FC; Voorbeeld";"Jan ""De Test""";'));
});
