import { test } from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs';
import ts from 'typescript';
import { createRequire } from 'node:module';
const require=createRequire(new URL('../package.json',import.meta.url));
function load(path, dependencies={}) {
 const mod={exports:{}};
 const source=ts.transpileModule(fs.readFileSync(new URL(path,import.meta.url),'utf8'),{compilerOptions:{module:ts.ModuleKind.CommonJS,jsx:ts.JsxEmit.ReactJSX}}).outputText;
 new Function('exports','module','require',source)(mod.exports,mod,id=>dependencies[id]??require(id));
 return mod.exports;
}
const grouping=load('../src/lib/seat-groups.ts');
const theme=load('../src/components/seat/seat-theme.ts');
const {HallMap}=load('../src/components/seat/hall-map.tsx',{'@/lib/seat-groups':grouping,'@/lib/utils':{cn:(...values)=>values.filter(Boolean).join(' ')},'./seat-theme':theme});
const React=require('react');const {renderToStaticMarkup}=require('react-dom/server');
const seats=[7,8].map((position,index)=>({seat_id:`s${position}`,physical_position:position,priority_rank:2-index,side:'LEFT',is_blocked:false,tier:'EMPEROR'}));
const props={floor:{rows:[{row_number:1,seats}],aisle_after_position:8},names:{s7:'陳思恩',s8:'陳思恩'},owners:{s7:'pair',s8:'pair'},primaryNames:{pair:'陳思恩'}};
const render=(extra={})=>renderToStaticMarkup(React.createElement(HallMap,{...props,...extra}));
test('default Emperor pair renders one named card spanning two physical tracks',()=>{
 const html=render();assert.equal((html.match(/<button/g)||[]).length,1);assert.match(html,/data-pair-display="merged"/);assert.match(html,/grid-column:8 \/ span 2/);assert.match(html,/陳思恩/);
});
test('legacy partner names still render one payer card',()=>{
 const html=render({splitPairs:{pair:true},names:{s7:'林慧婷',s8:'陳思恩'}});assert.equal((html.match(/<button/g)||[]).length,1);assert.match(html,/data-pair-display="merged"/);assert.doesNotMatch(html,/林慧婷/);assert.match(html,/陳思恩/);
});
test('selection of either cell outlines the complete pair wrapper',()=>{
 for(const selectedSeat of ['s7','s8']){const html=render({splitPairs:{pair:true},names:{s7:"林慧婷",s8:"陳思恩"},selectedSeat});assert.match(html,/data-pair-display="merged" class="[^"]*ring-2 ring-ring/);}
});
test('single-seat registration occupies one track',()=>{
 const html=render({owners:{s8:'single'},tiers:{single:'MERIT'}});assert.doesNotMatch(html,/data-pair-display=/);assert.match(html,/grid-column:9 \/ span 1/);
});
test('pair grouping never crosses an aisle or groups different registrations',()=>{
 const across=[{...seats[0],physical_position:8},{...seats[1],physical_position:9,side:'RIGHT'}];assert.equal(grouping.seatGroups(across,props.owners).length,2);assert.equal(grouping.seatGroups(seats,{s7:'one',s8:'two'}).length,2);
});

for (const [first,second] of [["陳思恩"," \t陳\u3000思\n恩 "],["Lee Shin","Lee\u00a0Shin"],["Darius Lee","\uFEFFDarius\u200BLee"],["陳思恩","陳思恩"]]) {
 test(`edited pair merges when names match ignoring whitespace: ${JSON.stringify(second)}`,()=>{
  const html=render({splitPairs:{pair:true},primaryNames:{pair:first},names:{s7:first,s8:second}});
  assert.match(html,/data-pair-display="merged"/);assert.equal((html.match(/<button/g)||[]).length,1);
 });
}
test('venue presentation keeps Chinese names without admin labels or location indices',()=>{
 const html=render({presentation:true});
 const visible=html.replace(/<[^>]*>/g,'');
 assert.match(visible,/陳思恩/);
 assert.doesNotMatch(visible,/PAIR|FRONT|WEST|EAST|BACK|1·7|1·8/);
 assert.doesNotMatch(html,/seat-metadata/);
});
test('venue names reject identifiers and placeholders without inventing occupants',()=>{
 const {chineseVenueName}=load('../src/lib/venue-names.ts');
 for(const name of ['synthetic-001','Synthetic participant 1','P0001',null,undefined,'陳思恩 P0001']) assert.equal(chineseVenueName(name),'');
 for(const name of ['陳思恩','林慧婷','歐陽文華']) assert.equal(chineseVenueName(name),name);
});

test('specified aisle positions render no seat or structural block while other blocks remain',()=>{
 const rows=[6,7,8,9].map(row=>({row_number:row,seats:Array.from({length:16},(_,i)=>({
  seat_id:`R${row}-S${i+1}`,physical_position:i+1,side:i<8?'LEFT':'RIGHT',is_blocked:i>=4&&i<12
 }))}));
 for(const presentation of [false,true]){
  const html=render({floor:{rows,aisle_after_position:8},owners:{},presentation});
  for(const row of [6,8]) for(let pos=5;pos<=12;pos++) assert.doesNotMatch(html,new RegExp(`data-seat="R${row}-S${pos}"`));
  for(const row of [7,9]) assert.match(html,new RegExp(`data-seat="R${row}-S5"`));
  assert.match(html,/grid-column:15 \/ span 1/);
 }
});
