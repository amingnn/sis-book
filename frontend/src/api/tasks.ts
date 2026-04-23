import client from "./client";

export type TaskStatus = "todo" | "doing" | "done";
export type TaskPriority = "high" | "medium" | "low";

export interface Task {
  id: number;
  title: string;
  description: string;
  category: string;
  priority: TaskPriority;
  status: TaskStatus;
  due_date: string | null;
  related_type: string;
  related_id: number | null;
  notes: string;
  created_at: string;
  completed_at: string | null;
}

export interface TaskForm {
  title: string;
  description?: string;
  category?: string;
  priority?: TaskPriority;
  status?: TaskStatus;
  due_date?: string | null;
  related_type?: string;
  related_id?: number | null;
  notes?: string;
}

export interface TaskSummary {
  total_count: number;
  todo_count: number;
  doing_count: number;
  done_count: number;
  overdue_count: number;
  recent_tasks: Array<{
    id: number;
    title: string;
    status: TaskStatus;
    priority: TaskPriority;
    category: string;
    due_date: string | null;
  }>;
}

export const tasksApi = {
  list: (params?: Record<string, unknown>) => client.get<Task[]>("/tasks", { params }),
  get: (id: number) => client.get<Task>(`/tasks/${id}`),
  create: (data: TaskForm) => client.post<Task>("/tasks", data),
  update: (id: number, data: Partial<TaskForm>) => client.put<Task>(`/tasks/${id}`, data),
  updateStatus: (id: number, status: TaskStatus) =>
    client.patch<Task>(`/tasks/${id}/status`, { status }),
  delete: (id: number) => client.delete(`/tasks/${id}`),
  summary: () => client.get<TaskSummary>("/tasks/summary"),
};
