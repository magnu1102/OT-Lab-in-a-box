export interface ProcessState {
  tank_level: number;
  pump_running: boolean;
  inflow_rate: number;
  outflow_rate: number;
  temperature: number;
  alarm: boolean;
  last_updated: string;
}

export interface Reading {
  id: number;
  timestamp: string;
  tank_level: number;
  pump_running: boolean;
  temperature: number;
  alarm: boolean;
}

export type ScenarioName = "normal" | "high_tank";
