'use client';

import { useState } from 'react';
import { api } from '@/lib/api';
import { AgentCard } from '@/components/AgentCard';
import { useAgentStream } from '@/lib/useAgentStream';
import { Task } from '@/lib/types';

export default function Home() {
  const [description, setDescription] = useState('');
  const [task, setTask] = useState<Task | null>(null);
  const [loading, setLoading] = useState(false);
  const { steps, isComplete, error, reset } = useAgentStream(task?.task_id ?? null);

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    if (!description.trim()) return;
    setLoading(true);
    reset();
    try {
      const result = await api.createTask(description) as Task;
      setTask(result);
    } catch (err) {
      alert('Failed to create task');
    } finally {
      setLoading(false);
    }
  }

  const finalStep = steps.find(s => s.type === 'FINAL');

  return (
    <main style={{ maxWidth: 800, margin: '0 auto', padding: '40px 20px' }}>
      <div style={{ marginBottom: 40 }}>
        <h1 style={{ fontSize: 28, fontWeight: 500, marginBottom: 8 }}>AgentFlow</h1>
        <p style={{ color: 'var(--color-text-secondary)', fontSize: 15 }}>
          Submit a complex task and watch multi-agent AI complete it in real time.
        </p>
      </div>

      <form onSubmit={handleSubmit} style={{ marginBottom: 32 }}>
        <textarea
          value={description}
          onChange={e => setDescription(e.target.value)}
          placeholder="e.g. Research the top 5 EV companies and write a competitive analysis report"
          rows={3}
          disabled={loading}
          style={{
            width: '100%',
            padding: '12px 16px',
            fontSize: 15,
            borderRadius: 8,
            border: '1px solid var(--color-border-secondary)',
            background: 'var(--color-background-secondary)',
            color: 'var(--color-text-primary)',
            resize: 'vertical',
            boxSizing: 'border-box',
            marginBottom: 12,
          }}
        />
        <button
          type="submit"
          disabled={loading || !description.trim()}
          style={{
            padding: '10px 24px',
            background: '#7F77DD',
            color: '#fff',
            border: 'none',
            borderRadius: 8,
            fontSize: 14,
            fontWeight: 500,
            cursor: loading ? 'not-allowed' : 'pointer',
            opacity: loading ? 0.6 : 1,
          }}
        >
          {loading ? 'Submitting...' : 'Run Agents'}
        </button>
      </form>

      {steps.length > 0 && (
        <div>
          <h2 style={{ fontSize: 16, fontWeight: 500, marginBottom: 16, color: 'var(--color-text-secondary)' }}>
            Agent timeline
          </h2>
          {steps.map((step, i) => (
            <AgentCard key={i} step={step} index={i} />
          ))}
        </div>
      )}

      {finalStep?.output && (
        <div style={{
          marginTop: 24,
          padding: '20px 24px',
          border: '1px solid var(--color-border-success)',
          borderRadius: 12,
          background: 'var(--color-background-success)',
        }}>
          <h2 style={{ fontSize: 16, fontWeight: 500, marginBottom: 12 }}>Final output</h2>
          <pre style={{ whiteSpace: 'pre-wrap', fontSize: 14, lineHeight: 1.7, margin: 0 }}>
            {finalStep.output}
          </pre>
        </div>
      )}

      {error && (
        <div style={{ color: 'var(--color-text-danger)', marginTop: 16, fontSize: 14 }}>
          Error: {error}
        </div>
      )}
    </main>
  );
}
