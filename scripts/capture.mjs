// Uitsluitend opgegeven ploegkalenders. Geen reekskalenders als fallback.
import fs from 'node:fs';
import path from 'node:path';
import {fileURLToPath} from 'node:url';
import {spawnSync} from 'node:child_process';
import {createHash} from 'node:crypto';
import puppeteer from 'puppeteer';
import {calendarJobs,matchURL,mergeFixtures,score,isLeagueFixture} from './calendar_helpers.mjs';
const root=path.resolve(path.dirname(fileURLToPath(import.meta.url)),'..');
process.chdir(root);
if(process.platform==='linux' && !process.env.DISPLAY && !process.env.CLUBSCOUT_XVFB){
  const r=spawnSync('xvfb-run',['-a',process.execPath,process.argv[1],...process.argv.slice(2)],{stdio:'inherit',env:{...process.env,CLUBSCOUT_XVFB:'1'}});
  if(r.error)console.error('Installeer xvfb of start vanuit een desktopomgeving.',r.error.message);
  process.exit(r.status??1);
}
const jobs=calendarJobs(JSON.parse(fs.readFileSync('config/clubs.json','utf8')));
const temp=fs.mkdtempSync(path.join(root,'.capture-'));
fs.cpSync(path.join(root,'config'),path.join(temp,'config'),{recursive:true});
fs.cpSync(path.join(root,'data_raw'),path.join(temp,'data_raw'),{recursive:true});
for(const dir of ['data_raw/calendars','data_raw/reports','public/data'])fs.mkdirSync(path.join(temp,dir),{recursive:true});
const diagnostics={startedAt:new Date().toISOString(),calendars:[],reports:[],status:'running'};
const pause=ms=>new Promise(r=>setTimeout(r,ms));
let browser;
let page;

function readCards(){
  // Werkelijk waargenomen ploegpagina: game-container met a.team-score.
  return Array.from(document.querySelectorAll('a.team-score[href*="/nl/wedstrijd/"]')).map(a=>{
    let el=a.closest('.game-container, .game-item')||a.parentElement;
    for(let parent=el;parent;parent=parent.parentElement){
      const urls=new Set(Array.from(parent.querySelectorAll('a.team-score[href*="/nl/wedstrijd/"]')).map(n=>n.pathname));
      if(urls.size>1)break;
      if(parent.querySelector('.game-type-name')){el=parent;break;}
    }
    return {url:a.href,scoreText:a.querySelector('.score')?.textContent.trim()??'',
      competition:el.querySelector('.game-type-name')?.textContent.trim()??'',
      competition_id:Array.from(el.querySelectorAll('a[href]')).map(n=>n.getAttribute('href').match(/CHP_\d+/)?.[0]).find(Boolean)??null,
      text:el.textContent.replace(/\s+/g,' ').trim()};
  });
}

async function readCalendar(page,job){
  console.log(`Ploegkalender: ${job.club.name} / ${job.team.label} — ${job.url}`);
  await page.goto(job.url,{waitUntil:'networkidle2',timeout:60000});
  await page.waitForSelector('.game-item, a[href*="/nl/wedstrijd/"]',{timeout:45000});
  const rows=[];
  const collect=async()=>{
    for(const row of await page.evaluate(readCards))rows.push({...row,url:matchURL(row.url),score:score(row.scoreText)});
  };
  await collect();
  // Seizoenfilters blijven op de huidige keuze om andere seizoenen te vermijden.
  const selects=await page.$$eval('select',els=>els.map((el,index)=>({index,
    options:Array.from(el.options).map(o=>({value:o.value,text:o.textContent.trim(),disabled:o.disabled})),
    label:(el.getAttribute('aria-label')||'')+' '+(el.closest('label')?.textContent||'')
  })).filter(s=>s.options.length>1 && !s.options.every(o=>/^(nl|fr|en|nederlands|fran[cç]ais|english)$/i.test(o.text))));
  for(const s of selects){
    if(/seizoen|season|saison/i.test(s.label) || s.options.some(o=>/20\d{2}\s*[-/]\s*20\d{2}/.test(o.text)))continue;
    const opts=s.options.filter(o=>o.value && !o.disabled);
    if(opts.length>80)throw Error('Onverwacht groot kalenderfilter; handmatige controle nodig');
    for(const option of opts){
      await page.evaluate(({index,value})=>{
        const select=document.querySelectorAll('select')[index];
        if(!select)throw Error('Kalenderfilter verdwenen');
        select.value=value;select.dispatchEvent(new Event('change',{bubbles:true}));
      },{index:s.index,value:option.value});
      await page.waitForNetworkIdle({idleTime:800,timeout:20000});
      await page.waitForSelector('.game-item, a[href*="/nl/wedstrijd/"]',{timeout:20000});await collect();
    }
  }
  for(let i=0;i<100;i++){
    const clicked=await page.evaluate(()=>{
      const el=Array.from(document.querySelectorAll('button,a')).find(n=>{
        const label=(n.getAttribute('aria-label')||n.textContent).trim();
        return /^(meer (laden|wedstrijden|tonen)|toon meer|laad meer|load more|volgende|next|volgende pagina)$/i.test(label) &&
          !n.disabled && n.getAttribute('aria-disabled')!=='true' && n.getClientRects().length;
      });
      if(!el)return false;el.click();return true;
    });
    if(!clicked)break;
    await page.waitForNetworkIdle({idleTime:800,timeout:20000});await collect();
    if(i===99)throw Error('Pagineringlimiet bereikt; kalender niet aanvaarden');
  }
  const unique=mergeFixtures([],rows);
  if(!unique.length)throw Error('Geen herkenbare wedstrijden op ploegkalender');
  return unique;
}

async function pool(items,work,concurrency=3){
  const result=new Array(items.length);let cursor=0;
  await Promise.all(Array.from({length:Math.min(concurrency,items.length)},async()=>{
    while(cursor<items.length){const i=cursor++;result[i]=await work(items[i]);}
  }));return result;
}
try{
  browser=await puppeteer.launch({headless:false,args:['--no-sandbox','--disable-setuid-sandbox']});
  const fixtures=new Map(),warnings=[],teamById=new Map(jobs.map(j=>[j.team.rbfa_team_id,j.team]));
  await pool(jobs,async job=>{
    const p=await browser.newPage();
    try{
      const fetched=await readCalendar(p,job);
      const file=path.join(temp,'data_raw/calendars',job.team.rbfa_team_id+'.json');
      const old=fs.existsSync(file)?JSON.parse(fs.readFileSync(file,'utf8')):null;
      const merged=mergeFixtures(old?.matches??[],fetched);
      console.log('Kalenderreeksen '+job.team.rbfa_team_id+': '+JSON.stringify([...new Set(fetched.map(m=>m.competition))]));
      if(!merged.some(m=>isLeagueFixture(job.team,m)))throw Error('Geen wedstrijd met opgegeven competitie; gevonden: '+[...new Set(fetched.map(m=>m.competition))].join(', '));
      const calendar={team_id:job.team.rbfa_team_id,url:job.url,fetched_at:new Date().toISOString(),completeness:'unverified',observed_now:fetched.length,preserved:merged.length-fetched.length,matches:merged};
      fs.writeFileSync(file,JSON.stringify(calendar,null,2));
      diagnostics.calendars.push({team:job.team.rbfa_team_id,observed:fetched.length,preserved:calendar.preserved});
      for(const match of merged){
        if(!isLeagueFixture(job.team,match)||!match.score)continue;
        const fixture=fixtures.get(match.url)??{teams:new Set(),score:match.score};
        if(fixture.score.join('-')!==match.score.join('-'))throw Error('Tegenstrijdige score tussen kalenders');
        fixture.teams.add(job.team.rbfa_team_id);fixtures.set(match.url,fixture);
      }
    }catch(e){
      const warning={team_id:job.team.rbfa_team_id,club:job.club.name,team:job.team.label,url:job.url,error:e.message};
      warnings.push(warning);console.error('Kalender niet bijgewerkt: '+JSON.stringify(warning));
    }finally{await p.close();}
  });
  if(!diagnostics.calendars.length)throw Error('Geen enkele ploegkalender succesvol bijgewerkt; dataset behouden.');
  await pool([...fixtures],async([url,fixture])=>{
    let p;
    try{
      const cachedFile=path.join(temp,'data_raw/reports',createHash('sha256').update(url).digest('hex')+'.json');
      const cached=fs.existsSync(cachedFile)?JSON.parse(fs.readFileSync(cachedFile,'utf8')):null;
      const needsMinutes=[...fixture.teams].some(tid=>teamById.get(tid).minutes_enabled);
      if(cached&&!process.argv.includes('--refresh-reports')&&(!needsMinutes||cached.parser_version===2)){
        if(cached.score?.join('-')!==fixture.score.join('-'))throw Error('Bewaarde score verschilt van kalender');
        if([...fixture.teams].some(id=>!cached.teams.some(t=>t.team_rbfa_id===id)))throw Error('Verkeerde ploeg-ID in bewaard verslag');
        diagnostics.reports.push({url,status:'cached'});return;
      }
      p=await browser.newPage();
      console.log('Wedstrijdblad: '+url);
      await p.goto(url,{waitUntil:'networkidle2',timeout:60000});
      await p.waitForSelector('.event-summary',{timeout:30000});
      const ids=await p.$$eval('.event-summary a[href]',els=>els.map(a=>a.getAttribute('href').match(/\/ploeg\/(\d+)/)?.[1]).filter(Boolean));
      if([...fixture.teams].some(id=>!ids.includes(id)))throw Error('Verkeerde ploeg-ID op wedstrijdblad');
      const actualScore=score(await p.$eval('.event-summary .score',el=>el.textContent));
      if(!actualScore||actualScore.join('-')!==fixture.score.join('-'))throw Error('Score verschilt van kalender');
      const hasPlayers=await p.waitForSelector('.opstelling-tabel .player .name',{timeout:8000}).then(()=>true,()=>false);
      if(!hasPlayers){warnings.push({url,error:'Geen openbare spelerslijst'});diagnostics.reports.push({url,status:'no_player_list'});return;}
      const htmlPath=path.join(temp,createHash('sha256').update(url).digest('hex')+'.html');fs.writeFileSync(htmlPath,await p.content());
      const r=spawnSync('python3',[path.join(root,'scripts/import_report.py'),htmlPath,'--source',url,'--expected-score',fixture.score.join('-'),'--output-dir',path.join(temp,'data_raw/reports')],{cwd:root,stdio:'inherit'});
      if(r.status!==0)throw Error('Parser weigerde verslag');
      diagnostics.reports.push({url,status:'ok'});
    }catch(e){warnings.push({url,error:e.message});diagnostics.reports.push({url,status:'failed',error:e.message});console.error(url,e.message);
    }finally{if(p)await p.close();await pause(350);}
  });
  fs.writeFileSync(path.join(temp,'data_raw/scrape_status.json'),JSON.stringify({updated_at:new Date().toISOString(),warnings},null,2));
  const r=spawnSync('python3',[path.join(root,'scripts/commit_capture.py'),temp],{stdio:'inherit',cwd:root});
  if(r.status!==0)throw Error('Validatie mislukt; dashboard behouden');
  diagnostics.status=warnings.length?'partial':'success';diagnostics.warnings=warnings;
}catch(e){diagnostics.status='failed';diagnostics.error=e.message;process.exitCode=1;console.error(e.stack);
}finally{
  diagnostics.finishedAt=new Date().toISOString();fs.mkdirSync('diagnostics',{recursive:true});
  fs.writeFileSync('diagnostics/last-capture.json',JSON.stringify(diagnostics,null,2));
  if(browser)await browser.close();fs.rmSync(temp,{recursive:true,force:true});
}
