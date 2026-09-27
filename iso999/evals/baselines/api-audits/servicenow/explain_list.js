// Reproduces `now-sdk explain --list --format raw` (sdk-cli/dist/command/explain/index.js printTopicList)
// without the CLI wrapper, so no telemetry is sent. Uses the SDK's own scanDocs.
const fs=require('fs');
const docs=require('<scratch>/snsdk/node_modules/@servicenow/sdk-api/dist/docs.js');
const dir='<scratch>/snsdk/node_modules/@servicenow/sdk/docs';
const ad={readdirSync:p=>fs.readdirSync(p),statSync:p=>fs.statSync(p),readFileSync:p=>fs.readFileSync(p,'utf-8')};
const all=docs.scanDocs(dir,ad);
const mode=process.argv[2]||'list';
const sorted=[...all].sort((a,b)=>a.name.localeCompare(b.name));
if(mode==='list'){ console.log('# Available topics:'); for(const d of sorted){const t=d.tags.length?` [${d.tags.join(', ')}]`:''; console.log(d.name+t);} console.log('# Use `now-sdk explain <name>` with a topic name to expand.'); }
if(mode==='json'){ console.log(JSON.stringify(all.map(d=>({name:d.name,file:d.filePath.slice(dir.length+1),tags:d.tags})),null,1)); }
