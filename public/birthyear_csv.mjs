// Dezelfde ontbrekende-geboortejaren-export als scouting2627.
export function missingBirthyearsCsv(clubs,players,clubDisplayName=c=>c.name){
 const byId=new Map(clubs.map(c=>[c.id,c]));
 const missing=players.filter(p=>p.birth_year==null).sort((a,b)=>{
   const ac=clubDisplayName(byId.get(a.club_id)),bc=clubDisplayName(byId.get(b.club_id));
   return ac.localeCompare(bc,'nl')||a.name.localeCompare(b.name,'nl');
 });
 const quote=v=>String(v??'').includes(';')||String(v??'').includes('"')?'"'+String(v).replaceAll('"','""')+'"':String(v??'');
 const rows=[['ClubRBFA','Naam','Geboortejaar'],...missing.map(p=>[clubDisplayName(byId.get(p.club_id)),p.name,''])];
 return String.fromCharCode(0xFEFF)+rows.map(row=>row.map(quote).join(';')).join(String.fromCharCode(13,10));
}
