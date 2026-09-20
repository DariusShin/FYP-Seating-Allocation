/** Participant-scoped response; never accepts the administrative allocation payload. */
export interface PublishedAllocation {
	status: string;
	message?: string;
	plan_version_id?: string;
	event_id?: string;
	event_details?: {
		name: string;
		date: string | null;
		time: string | null;
		timezone: string;
		venue: string | null;
	};
	assignment?: {
		participant_id: string;
		full_name: string;
		seat_ids: string[];
		seats: {
			seat_id: string;
			row_number: number;
			physical_position: number;
			display_name: string;
		}[];
	} | null;
	floor_plan?: {
		aisle_after_position: number;
		seats_per_row: number;
		rows: {
			row_number: number;
			seats: {
				seat_id: string;
				physical_position: number;
				priority_rank: number;
				occupancy_status: string;
			}[];
		}[];
	};
}
