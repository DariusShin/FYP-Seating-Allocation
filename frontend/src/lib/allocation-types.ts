export type TierName = "EMPEROR" | "BODHI" | "MERIT";
export type ZoneName =
  | "LEFT_OUTER"
  | "LEFT_CENTER"
  | "RIGHT_CENTER"
  | "RIGHT_OUTER";
export type OccupancyStatus = "OCCUPIED" | "EMPTY" | "BLOCKED";
export type CategoryName =
  | "MONASTIC"
  | "COMMITTEE"
  | "VOLUNTEER"
  | "GENERAL_DEVOTEE";

export interface SeatCell {
  seat_id: string;
  physical_position: number;
  priority_rank: number;
  side: "LEFT" | "RIGHT";
  zone: ZoneName;
  is_accessible: boolean;
  is_blocked: boolean;
  occupancy_status: OccupancyStatus;
  participant_id: string | null;
  display_name: string | null;
}

export interface FloorPlanRow {
  row_number: number;
  tier_band: TierName | null;
  seats: SeatCell[];
}

export interface PenaltyComponents {
  priority_seat: number;
  category_zone: number;
  movement: number;
  activeness: number;
}

export interface AssignmentSeat {
  seat_id: string;
  row_number: number;
  physical_position: number;
  priority_rank: number;
  zone: ZoneName;
  display_name: string;
}

export interface Assignment {
  participant_id: string;
  full_name: string;
  contribution_tier: TierName;
  contribution_amount_rm: number;
  participant_category: CategoryName;
  is_monk: boolean;
  is_elderly: boolean;
  requires_accessible_seat: boolean;
  events_joined_last_2_years: number;
  allocation_type: "SINGLE" | "EMPEROR_PAIR";
  seat_ids: string[];
  seats: AssignmentSeat[];
  pair_priority: number | null;
  previous_seat_ids: string[];
  moved: boolean | null;
  penalty: {
    unweighted: PenaltyComponents;
    normalized: PenaltyComponents;
    weighted: PenaltyComponents & { total: number };
  };
}

export interface SolverWeights {
  priority_seat_weight: number;
  category_zone_weight: number;
  movement_weight: number;
  activeness_weight: number;
}

export interface ConstraintConfig {
  enforce_front_fill: boolean;
  enforce_middle_fill: boolean;
  normalize_penalties: boolean;
  normalization_scale: number;
  component_maxima: PenaltyComponents;
}

export interface AllocationResult {
  schema_version: string;
  run_id: string;
  generated_at: string;
  case_study: string;
  status: "success";
  input_summary: {
    primary_participant_count: number;
    emperor_count: number;
    bodhi_count: number;
    merit_count: number;
    required_seat_count: number;
    total_seat_count: number;
    empty_seat_count: number;
  };
  weights: SolverWeights;
  constraint_config: ConstraintConfig;
  solver: {
    engine: string;
    status: string;
    objective_value: number;
    main_penalty: number;
    tie_break_penalty: number;
    main_objective_scale: number;
    best_objective_bound: number;
    optimality_gap: number;
    wall_time_seconds: number;
    num_conflicts: number;
    num_branches: number;
    num_boolean_variables: number;
    num_integer_variables: number;
    num_constraints: number;
  };
  penalty_summary: {
    unweighted: PenaltyComponents;
    normalized: PenaltyComponents;
    weighted: PenaltyComponents & { tie_break: number; total: number };
  };
  floor_plan: {
    row_count: number;
    seats_per_row: number;
    total_seats: number;
    aisle_after_position: number;
    rows: FloorPlanRow[];
  };
  assignments: Assignment[];
  empty_seat_ids: string[];
  unassigned_participants: string[];
  hard_constraint_validation: Record<string, boolean | number>;
}
