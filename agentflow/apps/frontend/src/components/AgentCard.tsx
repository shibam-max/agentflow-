'use client';

import { AgentStep } from '@/lib/types';

const AGENT_META: Record<string, { label: string; color: string }> = {
  researcher: { label: 'Researcher', color: '#7F77DD' },
  writer:     { label: 'Writer',     color: '#1D9E75' },
  coder:      { label: 'Coder',      color: '#BA7517' },
  critic:     { label: 'Critic',     color: '#D85A30' },
  finalize:   { label: 'Finalize',   color: '#888780' },
};

interface Props {
  step: AgentStep;
  index: number;
}

export function AgentCard({ step, index }: Props) {
  const meta = AGENT_META[step.agent] ?? { label: step.agent, color: '#888' };
  const isDone = step.type === 'AGENT_DONE' || step.type === 'FINAL';

  return (
    <div style={{
      border: `1px solid ${meta.color}40`,
      borderLeft: `4px solid ${meta.color}`,
      borderRadius: 8,
      padding: '16px 20px',
      marginBottom: 12,
      background: 'var(--color-background-secondary)',
      animation: 'fadeIn 0.3s ease',
    }}>
      <div style={{ display: 'flex', alignItems: 'center', gap: 10, marginBottom: 8 }}>
        <span style={{
          background: `${meta.color}20`,
          color: meta.color,
          padding: '2px 10px',
          borderRadius: 12,
          fontSize: 12,
          fontWeight: 500,
        }}>
          {meta.label}
        </span>
        {isDone && step.duration_ms && (
          <span style={{ fontSize: 12, color: 'var(--color-text-tertiary)' }}>
            {(step.duration_ms / 1000).toFixed(1)}s
          </span>
        )}
        {step.type === 'AGENT_START' && (
          <span style={{ fontSize: 12, color: 'var(--color-text-tertiary)' }}>
            Running...
          </span>
        )}
      </div>

      {step.output && (
        <pre style={{
          fontSize: 13,
          lineHeight: 1.6,
          whiteSpace: 'pre-wrap',
          wordBreak: 'break-word',
          color: 'var(--color-text-secondary)',
          margin: 0,
          maxHeight: 200,
          overflow: 'auto',
        }}>
          {step.output.slice(0, 600)}{step.output.length > 600 ? '…' : ''}
        </pre>
      )}
    </div>
  );
}
