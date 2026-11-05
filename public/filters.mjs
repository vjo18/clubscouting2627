export function ageOf(player,ageYear){
  return player.birth_year==null?null:(player.age??ageYear-player.birth_year);
}
export function minuteTeams(player,club,reference='A'){
  return club.teams.filter(t=>t.include&&t.minutes_enabled&&
    (reference==='all'||reference==='A'&&t.role==='A'||reference===t.rbfa_team_id))
    .map(t=>({team:t,stats:player.teams[t.rbfa_team_id]}))
    .filter(x=>x.stats&&x.stats.listed>0&&x.stats.minutes_pct!=null);
}
export function matchesPreset(player,club,mode,threshold=25,reference='A',ageYear=new Date().getFullYear()){
  if(mode==='all')return true;
  if(mode==='multi')return player.multiple_teams;
  const age=ageOf(player,ageYear);
  if(age==null || mode==='young'&&age>20 || mode==='experienced'&&age<23)return false;
  return minuteTeams(player,club,reference).some(({stats:s})=>{
    const pct=s.minutes!=null&&s.possible_minutes>0?s.minutes*100/s.possible_minutes:s.minutes_pct;
    return pct<Number(threshold);
  });
}
export function numberSummary(stats){
  return Object.entries(stats.number_counts??{}).sort((a,b)=>b[1]-a[1]||a[0].localeCompare(b[0],undefined,{numeric:true}))
    .map(([n,count])=>`${n} (${count}×)`).join(', ');
}
