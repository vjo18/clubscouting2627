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


const MONTHS={januari:1,februari:2,maart:3,april:4,mei:5,juni:6,juli:7,augustus:8,september:9,oktober:10,november:11,december:12};
export function fixtureDate(match,season='2026-2027'){
  // RBFA toont dag en maand zonder jaartal; de competitie loopt van zomer tot zomer.
  const text=String(match.text??'').toLocaleLowerCase('nl-BE');
  const found=text.match(/\b(\d{1,2})\s+(januari|februari|maart|april|mei|juni|juli|augustus|september|oktober|november|december)\b/);
  if(!found)return null;
  const month=MONTHS[found[2]],day=Number(found[1]),startYear=Number(String(season).match(/^\d{4}/)?.[0]);
  if(!startYear||day<1||day>31)return null;
  const year=month>=7?startYear:startYear+1;
  const date=new Date(Date.UTC(year,month-1,day));
  return date.getUTCFullYear()===year&&date.getUTCMonth()===month-1&&date.getUTCDate()===day?date.toISOString().slice(0,10):null;
}
export function isFutureFixture(match,season='2026-2027',today=new Intl.DateTimeFormat('sv-SE',{timeZone:'Europe/Brussels',year:'numeric',month:'2-digit',day:'2-digit'}).format(new Date())){
  const date=fixtureDate(match,season);
  return date!==null&&date>today;
}
