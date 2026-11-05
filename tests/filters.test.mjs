import test from 'node:test';
import assert from 'node:assert/strict';
import {matchesPreset,numberSummary} from '../public/filters.mjs';
const club={teams:[{rbfa_team_id:'a',role:'A',include:true,minutes_enabled:true},{rbfa_team_id:'r',role:'reserves',include:true,minutes_enabled:false}]};
const p={birth_year:2006,age:20,multiple_teams:true,teams:{a:{listed:4,minutes:30,possible_minutes:360,minutes_pct:8.3},r:{listed:8,minutes_pct:null}}};
test('Jong tot en met 20 en ervaren vanaf 23, grens aanpasbaar',()=>{
 assert.equal(matchesPreset(p,club,'young',10,'A',2026),true);
 assert.equal(matchesPreset(p,club,'young',5,'A',2026),false);
 assert.equal(matchesPreset({...p,age:21},club,'young',25,'A',2026),false);
 assert.equal(matchesPreset({...p,age:23},club,'experienced',25,'A',2026),true);
 assert.equal(matchesPreset({...p,age:22},club,'experienced',25,'A',2026),false);
});
test('Onbekende leeftijd, ontbrekende minuten en geen selectie tellen niet als weinig minuten',()=>{
 assert.equal(matchesPreset({...p,birth_year:null},club,'young',25),false);
 assert.equal(matchesPreset({...p,teams:{a:{listed:4,minutes_pct:null}}},club,'young',25),false);
 assert.equal(matchesPreset({...p,teams:{r:p.teams.r}},club,'young',25),false);
 assert.equal(matchesPreset({...p,teams:{a:{listed:0,minutes_pct:0}}},club,'young',25),false);
 assert.equal(matchesPreset(p,club,'young',25,'r'),false);
});
test('Grens is strikt minder dan; rugnummers behouden de aantallen',()=>{
 const player={...p,teams:{a:{listed:4,minutes:90,possible_minutes:360,minutes_pct:25}}};
 assert.equal(matchesPreset(player,club,'young',25),false);
 assert.equal(matchesPreset(player,club,'young',26),true);
 assert.equal(numberSummary({number_counts:{'18':2,'7':4}}),'7 (4×), 18 (2×)');
});
