export type TaskStatus = 'PENDING' | 'RUNNING' | 'DONE' | 'FAILED';

export interface Task {
  task_id: string;
  description: string;
  status: TaskStatus;
  created_at: string;
  stream_url?: string;
}

export interface AgentStep {
  type: 'AGENT_START' | 'AGENT_DONE' | 'FINAL' | 'ERROR';
  agent: 'researcher' | 'writer' | 'coder' | 'critic' | 'finalize';
  output?: string;
  duration_ms?: number;
  token_count?: number;
  timestamp: string;
}

export interface RunResult {
  run_id: string;
  status: TaskStatus;
  critic_score?: number;
  revision_count?: number;
  final_output?: string;
  steps: AgentStep[];
}
