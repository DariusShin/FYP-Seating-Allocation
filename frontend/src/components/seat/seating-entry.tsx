"use client";
import { useState } from "react";
import { useRouter } from "next/navigation";
import { Button } from "@/components/ui/button";
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogDescription } from "@/components/ui/dialog";
import type { AllocationResult } from "@/lib/allocation-types";
import { GenerateDraft } from "./generate-draft";

export function SeatingEntry({ eventId, hasPlan, floor, registrations }: {
    eventId: string;
    hasPlan: boolean;
    floor: AllocationResult["floor_plan"];
    registrations: number;
}) {
    const router = useRouter();
    const [action, setAction] = useState<"new" | "load" | null>(hasPlan ? null : "new");
    return <>
        <GenerateDraft key={action ?? "choose"} eventId={eventId} floor={floor} registrations={registrations}
            autoStart={action !== null} entryAction={action ?? "new"} showGenerateButton={action !== null}
            generationMode={hasPlan ? "REGENERATE_DRAFT" : "INITIAL"}/>
        <Dialog open={action === null} onOpenChange={open => { if (!open) router.push("/event"); }}>
            <DialogContent>
                <DialogHeader>
                    <DialogTitle>Open seating allocation</DialogTitle>
                    <DialogDescription>Continue with the latest saved seating version, or generate a new draft for this event. Published seating stays unchanged.</DialogDescription>
                </DialogHeader>
                <div className="grid gap-3 pt-2 sm:grid-cols-2">
                    <Button onClick={() => setAction("load")}>Load latest draft</Button>
                    <Button variant="outline" onClick={() => setAction("new")}>Generate new draft</Button>
                </div>
            </DialogContent>
        </Dialog>
    </>;
}
