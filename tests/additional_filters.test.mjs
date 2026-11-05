import test from 'node:test';
import assert from 'node:assert/strict';
import {matchesExtraFilters} from '../public/filters.mjs';

const p={birth_year:2006,age:20,player_type:'goalkeeper',teams:{
  '100':{number_counts:{'1':3,'12':1}},
  '101':{number_counts:{'22':1}}
}};
test('minimum and maximum age are inclusive and combinable',()=>{
  assert.equal(matchesExtraFilters(p,{minAge:'20',maxAge:'20'},2026),true);
  assert.equal(matchesExtraFilters(p,{minAge:'21'},2026),false);
  assert.equal(matchesExtraFilters(p,{maxAge:'19'},2026),false);
  assert.equal(matchesExtraFilters({...p,birth_year:null,age:null},{minAge:'15'},2026),false);
});
test('rugnummer matches exactly across registered teams',()=>{
  assert.equal(matchesExtraFilters(p,{number:'12'},2026),true);
  assert.equal(matchesExtraFilters(p,{number:'22'},2026),true);
  assert.equal(matchesExtraFilters(p,{number:'2'},2026),false);
});
test('type uses recorded goalkeeper marker, not shirt number',()=>{
  assert.equal(matchesExtraFilters(p,{playerType:'goalkeeper'},2026),true);
  assert.equal(matchesExtraFilters(p,{playerType:'outfield'},2026),false);
  assert.equal(matchesExtraFilters({...p,player_type:'unknown'},{playerType:'outfield'},2026),false);
  assert.equal(matchesExtraFilters({...p,player_type:'unknown'},{playerType:'all'},2026),true);
});
