// Pure functies; ook zonder browser te testen.
export function isLeagueFixture(team, match) {
  const normalize=value=>String(value??'').trim().toLocaleLowerCase('nl').replace(/\s+/g,' ');
  if(team.competition_id && match.competition_id)return team.competition_id===match.competition_id;
  const name=normalize(match.competition);
  return Boolean(name) && (team.league_competitions??[]).some(c=>normalize(c)===name);
}

export function teamCalendar(url, clubId, teamId) {
  const u=new URL(url);
  if(u.protocol!=='https:' || !['rbfa.be','www.rbfa.be'].includes(u.hostname) ||
     u.pathname!==`/nl/club/${clubId}/ploeg/${teamId}/kalender` || u.search || u.hash || u.port || u.username || u.password)
    throw Error('Kalender hoort niet bij de ingestelde RBFA-club en ploeg: '+url);
  return u.href;
}

export function matchURL(url) {
  const u=new URL(url,'https://www.rbfa.be');
  if(u.protocol!=='https:' || !['rbfa.be','www.rbfa.be'].includes(u.hostname) ||
     !/^\/nl\/wedstrijd\/\d+\/?$/.test(u.pathname) || u.port || u.username || u.password)
    throw Error('Ongeldige RBFA-wedstrijd-URL: '+url);
  return 'https://www.rbfa.be'+u.pathname.replace(/\/$/,'');
}

export function score(text) {
  const m=String(text??'').trim().match(/^(\d+)\s*[-–]\s*(\d+)$/);
  return m?[Number(m[1]),Number(m[2])]:null;
}

export function mergeFixtures(existing, incoming) {
  const result=new Map(existing.map(m=>[matchURL(m.url),{...m,url:matchURL(m.url)}]));
  for(const row of incoming){
    const m={...row,url:matchURL(row.url)},previous=result.get(m.url);
    if(previous?.score && m.score && previous.score.join('-')!==m.score.join('-'))
      throw Error('Tegenstrijdige eindscore voor '+m.url);
    result.set(m.url,{...previous,...m,score:m.score??previous?.score??null});
  }
  return [...result.values()];
}

export function calendarJobs(config) {
  const seen=new Set(),jobs=[];
  for(const club of config.clubs)for(const team of club.teams){
    if(!team.include)continue;
    const id=team.rbfa_team_id;
    if(!id || !club.rbfa_club_id || !team.calendar_url)throw Error('Ontbrekende ploegconfiguratie: '+club.name+' / '+team.label);
    if(seen.has(id))throw Error('Ploeg-ID meermaals geconfigureerd: '+id);
    seen.add(id);
    jobs.push({club,team,url:teamCalendar(team.calendar_url,club.rbfa_club_id,id)});
  }
  if(!jobs.length)throw Error('Geen gevolgde ploegen');
  return jobs;
}

