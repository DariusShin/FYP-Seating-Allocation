import {test} from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs';
import ts from 'typescript';
function compile(file, load = () => ({})) {
  const source=fs.readFileSync(new URL(file,import.meta.url),'utf8');
  const code=ts.transpileModule(source,{compilerOptions:{module:ts.ModuleKind.CommonJS,target:ts.ScriptTarget.ES2022}}).outputText;
  const mod={exports:{}};
  new Function('require','module','exports',code)(load,mod,mod.exports);
  return mod.exports;
}
const {groupFindings}=compile('../src/lib/verification.ts');
test('51 pair findings collapse into registration cards without losing pair identities',()=>{
  const findings=Array.from({length:51},(_,i)=>({finding_id:`C13:${i}`,resolution_hint:{actor_participant_id:i<26?'root':`P${i-26}`}}));
  const groups=groupFindings(findings);
  assert.equal(groups.length,26);
  assert.equal(groups[0][1].length,26);
  assert.deepEqual(groups.flatMap(([,items])=>items),findings);
});
test('workspace API admits authenticated staff and binds identity and event server-side',async()=>{
  const calls=[];
  let role='staff';
  const api=compile('../src/app/api/workspace/route.ts',name=>name==='next/server'?{NextResponse:{json:(body,opts={})=>({body,status:opts.status??200})}}:{
    identity:async()=>({actor:'staff-1',role,event_id:'event-1'}),sameOrigin:()=>true,
    runProduction:async body=>{calls.push(body);return {review_status:'IN_PROGRESS'};}
  });
  const request={url:'http://localhost/api/workspace',json:async()=>({command:'workspace_ack',revision:3,plan_version_id:'plan',finding_id:'C13:A:B',status:'ACKED',note:'Reviewed',actor:'forged',event_id:'other'})};
  assert.equal((await api.POST(request)).status,200);
  assert.equal(calls[0].actor,'staff-1');assert.equal(calls[0].event_id,'event-1');
  assert.equal(calls[0].finding_id,'C13:A:B');assert.equal(calls[0].note,'Reviewed');
  role='participant';assert.equal((await api.POST(request)).status,403);
  role='staff';assert.equal((await api.POST({...request,url:'http://localhost/api/workspace?event_id=other'})).status,403);
  assert.equal(calls.length,1);
});

const {participantSeats,findingSeats,reviewSeatHighlights,followSelectedSeat}=compile('../src/lib/verification.ts');
test('review borders and selected-seat styling follow registrations immediately before recheck',()=>{
 const before={items:{emperor:{seat_ids:['old1','old2']},merit1:{seat_ids:['east1']},merit2:{seat_ids:['east2']}}};
 const after={items:{emperor:{seat_ids:['east1','east2']},merit1:{seat_ids:['old1']},merit2:{seat_ids:['old2']}}};
 const finding={finding_id:'C12:emperor:merit1',rule_id:'C12',severity:'RED',status:'OPEN',participants:[{participant_id:'emperor',seat_ids:['old1','old2']},{participant_id:'merit1',seat_ids:['east1']}],involved_seat_ids:['old1','old2','east1']};
 const review={findings:[finding],attribution:{groups:[{participant_ids:['emperor'],finding_ids:[finding.finding_id],focus_seat_ids:['old1','old2']}]}};
 assert.deepEqual(reviewSeatHighlights(review,after),{east1:'RED',east2:'RED'});
 assert.deepEqual(participantSeats(['emperor'],after),['east1','east2']);
 assert.equal(followSelectedSeat('old2',before,after),'east1');
 assert.deepEqual(new Set(findingSeats(finding,after)),new Set(['east1','east2','old1']));
 assert.equal(followSelectedSeat('old1',before,{items:{...after.items,emperor:{seat_ids:[]}}}),null);
});
test('unattributed borders follow people while packing gaps stay attached to empty seats',()=>{
 const finding={finding_id:'gap',severity:'YELLOW',status:'OPEN',participants:[{participant_id:'A',seat_ids:['old']}],involved_seat_ids:['old','gap']};
 const state={items:{A:{seat_ids:['new']},B:{seat_ids:['elsewhere']}}};
 assert.deepEqual(reviewSeatHighlights({findings:[finding]},state),{new:'YELLOW',gap:'YELLOW'});
 state.items.B.seat_ids=['gap'];assert.deepEqual(reviewSeatHighlights({findings:[finding]},state),{new:'YELLOW'});
 assert.deepEqual(reviewSeatHighlights({findings:[{...finding,status:'ACKED'}]},state),{});
});
