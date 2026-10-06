import Link from "next/link";
import { CircleAlert, LoaderCircle } from "lucide-react";
import { Button } from "@/components/ui/button";
import type { GenerationPhase } from "./types";

export function MapLoadingOverlay({
  phase,
  error,
  onRetry,
  draftCreated,
  title,
}: {
  title?: string;
  phase: GenerationPhase;
  error: string;
  onRetry: () => void;
  draftCreated: boolean;
}) {
  const failed = phase === "error";
  return (
    <div className="absolute inset-0 z-40 flex items-center justify-center bg-black/55 p-6 backdrop-blur-sm">
      <div className="w-full max-w-sm rounded-xl border bg-background p-6 text-center shadow-lg">
        {failed ? (
          <CircleAlert
            aria-hidden="true"
            className="mx-auto size-9 text-destructive"
          />
        ) : (
          <LoaderCircle
            aria-hidden="true"
            className="animate-spin mx-auto size-9 text-primary"
          />
        )}
        <div role={failed ? "alert" : "status"} aria-atomic="true">
          <h2 className="mt-4 text-base font-semibold">
            {title ??
              (failed
                ? draftCreated
                  ? "Your draft is saved, but could not be opened"
                  : "Unable to create your seating plan"
                : phase === "loading-workspace"
                  ? "Opening your seating draft…"
                  : "Creating your seating plan…")}
          </h2>
          <p className="mt-2 text-sm leading-6 text-muted-foreground">
            {failed
              ? error
              : phase === "loading-workspace"
                ? "Preparing the assigned seating map for review."
                : "This usually takes about a minute. Keep this page open."}
          </p>
        </div>
        {failed && (
          <div className="mt-5 flex flex-wrap items-center justify-center gap-4">
            <Button onClick={onRetry}>
              {draftCreated ? "Retry opening draft" : "Retry generation"}
            </Button>
            <Link
              href="/event"
              className="text-sm underline underline-offset-4"
            >
              Return to event
            </Link>
          </div>
        )}
      </div>
    </div>
  );
}
