"use client";
import { useState } from "react";
import { Button } from "@/components/ui/button";
export function GenerateDraft() {
	const [busy, setBusy] = useState(false);
	const [error, setError] = useState("");
	return (
		<main className="mx-auto max-w-xl space-y-4 p-8">
			<h1 className="text-xl font-semibold">PJKIT seating workspace</h1>
			<p>
				No production draft exists yet. Generate a draft for review. Guest seats
				will remain unpublished.
			</p>
			<Button
				disabled={busy}
				onClick={async () => {
					setBusy(true);
					setError("");
					try {
						const response = await fetch("/api/solve", {
							method: "POST",
							headers: { "Content-Type": "application/json" },
							body: JSON.stringify({
								generation_mode: "INITIAL",
								preference_profile_version: "ranked-v1",
								preferences: [
									"contribution_seat",
									"activeness",
									"category_zone",
								].map((key) => ({ key, enabled: true })),
							}),
						});
						const value = await response.json();
						if (!response.ok)
							throw new Error(value.error?.message ?? "Generation failed");
						window.location.reload();
					} catch (e) {
						setError(String(e));
					} finally {
						setBusy(false);
					}
				}}
			>
				{busy ? "Generating draft…" : "Generate draft"}
			</Button>
			{error && <p role="alert">{error}</p>}
		</main>
	);
}
