import test from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs';
import {calendarJobs,teamCalendar,matchURL,score,mergeFixtures,isLeagueFixture} from '../scripts/calendar_helpers.mjs';

test('De 49 opgegeven ploegen gebruiken uitsluitend hun eigen kalender',()=>{
  const c=JSON.parse(fs.readFileSync(new URL('../config/clubs.json',import.meta.url)));
  const jobs=calendarJobs(c);
  assert.equal(jobs.length,49);
  assert.equal(c.clubs.length,13);
  assert.equal(jobs.filter(j=>j.team.minutes_enabled).length,25);
  assert.equal(jobs.filter(j=>j.club.rbfa_club_id==='2656').length,3);
  assert.equal(jobs.filter(j=>j.club.rbfa_club_id==='1185').length,6);
  assert.ok(jobs.every(j=>j.url===`https://www.rbfa.be/nl/club/${j.club.rbfa_club_id}/ploeg/${j.team.rbfa_team_id}/kalender`));
});
test('Verkeerde club/ploeg en reekskalender worden geweigerd',()=>{
  for(const url of ['https://www.rbfa.be/nl/club/1185/ploeg/364285/kalender','https://www.rbfa.be/nl/competitie/CHP_1/kalender','https://example.com/nl/club/2656/ploeg/360196/kalender'])
    assert.throws(()=>teamCalendar(url,'2656','360196'));
});
test('Uitgesloten ploegen worden niet opgehaald; dubbele ploeg-ID is fout',()=>{
  const c=JSON.parse(fs.readFileSync(new URL('../config/clubs.json',import.meta.url)));
  assert.equal(calendarJobs(c).some(j=>j.team.role==='U21'),true);
  c.clubs[0].teams.push({...c.clubs[0].teams[0]});
  assert.throws(()=>calendarJobs(c));
});
test('Kalender-URL-varianten van dezelfde wedstrijd worden eenmaal verwerkt',()=>{
  const rows=mergeFixtures([],[{url:'/nl/wedstrijd/123',score:[3,5]},{url:'https://rbfa.be/nl/wedstrijd/123/?x=1',score:[3,5]}]);
  assert.equal(rows.length,1);assert.equal(rows[0].url,'https://www.rbfa.be/nl/wedstrijd/123');
});
test('Bestaande wedstrijden en eindscores blijven behouden bij gedeeltelijke kalender',()=>{
  const rows=mergeFixtures([{url:'/nl/wedstrijd/1',score:[1,0]},{url:'/nl/wedstrijd/2',score:[0,0]}],[{url:'/nl/wedstrijd/1',score:null}]);
  assert.equal(rows.length,2);assert.deepEqual(rows[0].score,[1,0]);
  assert.throws(()=>mergeFixtures(rows,[{url:'/nl/wedstrijd/1',score:[2,0]}]));
});
test('Geen score afleiden uit aftrapuur, uitstel of een leeg veld',()=>{
  assert.deepEqual(score('3 - 5'),[3,5]);assert.deepEqual(score('0–0'),[0,0]);
  for(const value of ['20:15','uitgesteld','-','',null])assert.equal(score(value),null);
  assert.throws(()=>matchURL('https://example.com/nl/wedstrijd/1'));
});


test('Competitiefilter weigert beker, oefenwedstrijden en onbekende labels',()=>{
  const t={league_competitions:['2 Provinciaal Wvl A']};
  assert.equal(isLeagueFixture(t,{competition:'2 Provinciaal Wvl A'}),true);
  for(const name of ['',null,'BvW Heren Groep 3 P1/P2','1e Ploegen 1-2 Prov','Croky Cup'])assert.equal(isLeagueFixture(t,{competition:name}),false);
});
