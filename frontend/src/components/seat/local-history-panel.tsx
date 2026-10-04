"use client";
import { useState } from "react";
import { Button } from "@/components/ui/button";
import { equal, type ManualHistory } from "@/lib/manual-history";
import type { Workspace, WorkingState } from "@/lib/workspace";
export function LocalHistoryPanel({ history, workspace, current, disabled, onRestore, onDelete }: {
  history: ManualHistory; workspace: Workspace; current: WorkingState; disabled: boolean;
  onRestore: (state: WorkingState) => void; onDelete: () => Promise<void>;
}) {
  const [selection, setSelection] = useState<string | null>(null);
  const [error, setError] = useState("");
  const [deleting, setDeleting] = useState(false);
  const entries = [
    ...history.versions.map(v => ({ id: v.id, state: v.state, fingerprint: v.fingerprint, label: `Saved revision ${v.revision} · ${new Date(v.saved_at).toLocaleString()}` })),
    ...history.conflicts.map(s => ({ id: s.id, state: s.state, fingerprint: s.fingerprint, label: `Retained branch · ${new Date(s.updated_at).toLocaleString()}` })),
  ];
  const selected = entries.find(v => v.id === selection);
  const changed = selected ? [...new Set([...Object.keys(selected.state.items), ...Object.keys(current.items)])].filter(pid =>
    !equal(selected.state.items[pid], current.items[pid]) ||
    !equal(selected.state.participants.find(p => p.participant_id === pid), current.participants.find(p => p.participant_id === pid))
  ) : [];
  return <div className="space-y-3 text-sm">
    <p>Saved snapshots and edit recovery stay in this browser, for this account and plan. They are not shared server plan versions.</p>
    <p>{history.session?.active.length ?? 0} active edits · {history.session?.sequence ?? 0} recorded operations</p>
    {error && <p role="alert">{error}</p>}
    <select aria-label="Local saved version or branch" className="w-full rounded border p-2" value={selection ?? ""} onChange={e => setSelection(e.target.value)}>
      <option value="">Inspect a saved version or retained branch</option>
      {entries.map(v => <option key={v.id} value={v.id}>{v.label}</option>)}
    </select>
    {selected && <><p>{changed.length} registrations differ from the current draft.</p>
      <div className="max-h-64 space-y-2 overflow-auto">{changed.map(pid => <div key={pid} className="rounded border p-2">
        <strong>{selected.state.items[pid]?.display_names[0] ?? current.items[pid]?.display_names[0]} · {pid}</strong>
        <p>Selected: {selected.state.items[pid] ? selected.state.items[pid].seat_ids.join(" + ") || "Holding dock" : "Not registered in this version"}</p>
        <p>Current: {current.items[pid] ? current.items[pid].seat_ids.join(" + ") || "Holding dock" : "Not registered in this version"}</p>
        <p>Selected name / note: {selected.state.items[pid]?.display_names.join(" / ") ?? "Not registered"} · {selected.state.items[pid]?.note || "None"}</p>
        {!equal(selected.state.participants.find(p => p.participant_id === pid), current.participants.find(p => p.participant_id === pid)) && <p>Registration inputs differ between these versions.</p>}
        <p>Current name / note: {current.items[pid]?.display_names.join(" / ")} · {current.items[pid]?.note || "None"}</p>
      </div>)}</div>
      {selected.fingerprint !== history.session?.fingerprint && <p>Layout or registrations changed. This branch can be compared but cannot be restored.</p>}
      <Button disabled={disabled || !changed.length || selected.fingerprint !== history.session?.fingerprint} onClick={() => onRestore(structuredClone(selected.state))}>Restore as a new draft edit</Button>
    </>}
    <details><summary className="cursor-pointer">Active edit records</summary><ol className="max-h-52 overflow-auto">{history.session?.active.map((e,i) => <li key={e.operation_id} className="border-b py-2">{i+1}. {e.kind} · {new Date(e.timestamp).toLocaleString()}{e.changes.map(c => <p key={c.participant_id}>{c.after.display_names[0]}: {c.before.seat_ids.join(" + ") || "Dock"} → {c.after.seat_ids.join(" + ") || "Dock"}</p>)}</li>)}</ol></details>
    <details><summary className="cursor-pointer">All recorded operations, including undone edits</summary><ol className="max-h-52 overflow-auto">{history.journal.map(e => <li key={e.operation_id} className="border-b py-2">{e.sequence}. {e.kind} · {new Date(e.timestamp).toLocaleString()}{e.reference && <p>References edit {e.reference}</p>}{e.changes.map(c => <p key={c.participant_id}>{c.after.display_names[0]}: {c.before.seat_ids.join(" + ") || "Dock"} → {c.after.seat_ids.join(" + ") || "Dock"}</p>)}</li>)}</ol></details>
    <details><summary className="cursor-pointer">Delete local history for this plan</summary><p className="my-2">This removes this account’s local versions and branches for this plan. Save current changes first. The server draft stays saved.</p><Button variant="outline" disabled={disabled || deleting || !equal(current, workspace.state)} onClick={async () => { setDeleting(true); try { await onDelete(); } catch(e) { setError(String(e)); } finally { setDeleting(false); } }}>Delete local history</Button></details>
  </div>;
}
