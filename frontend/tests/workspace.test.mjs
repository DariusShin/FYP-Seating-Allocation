import { test } from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs';
import ts from 'typescript';
const mod={exports:{}};
new Function('exports','module',ts.transpileModule(fs.readFileSync(new URL('../src/lib/workspace.ts',import.meta.url),'utf8'),{compilerOptions:{module:ts.ModuleKind.CommonJS}}).outputText)(mod.exports,mod);
const {move,dock}=mod.exports;
const cells=Array.from({length:16},(_,i)=>({seat_id:`s${i+1}`,physical_position:i+1,side:i<8?'LEFT':'RIGHT',is_blocked:false,is_accessible:[0,1,14,15].includes(i)}));
const base={floor_plan:{rows:[{row_number:1,seats:cells}]}};
function state(){return {participants:[{participant_id:'pair',contribution_tier:'EMPEROR',registration_status:'CONFIRMED',requires_accessible_seat:false},{participant_id:'single',contribution_tier:'MERIT',registration_status:'CONFIRMED',requires_accessible_seat:false}],items:{pair:{seat_ids:['s7','s8'],display_names:['陳思恩','林慧婷'],locked:false,companion_absent:false,note:'pair note'},single:{seat_ids:['s6'],display_names:['黃志華'],locked:false,companion_absent:false}}};}
test('dock round trip retains names, notes and provenance',()=>{const s=state();const held=dock(s,'pair');assert.deepEqual(held.items.pair.previous_seat_ids,['s7','s8']);assert.deepEqual(held.items.pair.seat_ids,[]);const next=move(held,base,'pair','s9');assert.deepEqual(next.items.pair.seat_ids,['s9','s10']);assert.deepEqual(next.items.pair.display_names,s.items.pair.display_names);assert.equal(next.items.pair.note,'pair note');assert.deepEqual(s.items.pair.seat_ids,['s7','s8']);});
test('unlinked Emperor behaves as an individual and released seat can be reassigned',()=>{const s=state();s.items.pair.companion_absent=true;s.items.pair.seat_ids=['s8'];const assigned=move(s,base,'single','s7');assert.deepEqual(assigned.items.single.seat_ids,['s7']);const swapped=move(assigned,base,'pair','s7');assert.deepEqual(swapped.items.pair.seat_ids,['s7']);assert.deepEqual(swapped.items.single.seat_ids,['s8']);assert.equal(swapped.participants[0].contribution_tier,'EMPEROR');});
test('locked source and destination cannot move or dock',()=>{const s=state();s.items.pair.locked=true;assert.throws(()=>dock(s,'pair'),/Unlock/);assert.throws(()=>move(s,base,'pair','s1'),/Unlock/);assert.throws(()=>move(s,base,'single','s7'),/Unlock/);});
test('pair cannot overwrite a single and stays on one side of aisle',()=>{const s=state();assert.throws(()=>move(s,base,'single','s7'),/Swap/);const next=move(s,base,'pair','s9');assert.deepEqual(next.items.pair.seat_ids,['s9','s10']);});
test('dock occupant is displaced atomically without losing registration',()=>{const s=state();s.items.pair.companion_absent=true;s.items.pair.seat_ids=[];const next=move(s,base,'pair','s6');assert.deepEqual(next.items.single.seat_ids,[]);assert.equal(next.items.single.dock_reason,'Displaced during assignment');assert.equal(next.participants.length,2);});
