const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8080';

async function apiFetch<T>(path: string, options: RequestInit = {}): Promise<T> {
  const res = await fetch(`${API_URL}${path}`, {
    ...options,
    headers: {
      'Content-Type': 'application/json',
      ...options.headers,
    },
    credentials: 'include',
  });

  if (!res.ok) {
    const err = await res.text();
    throw new Error(err || `HTTP ${res.status}`);
  }

  return res.json();
}

export const api = {
  createTask: (description: string) =>
    apiFetch('/api/tasks', {
      method: 'POST',
      body: JSON.stringify({ description }),
    }),

  getTask: (taskId: string) =>
    apiFetch(`/api/tasks/${taskId}`),

  listTasks: () =>
    apiFetch('/api/tasks'),
};
