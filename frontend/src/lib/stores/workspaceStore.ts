import { writable } from 'svelte/store';
import axios from 'axios';

const API_BASE = 'http://127.0.0.1:8000';

export interface HistoryEntry {
    id: string;
    query: string;
    duration_ms: number;
    affected_rows: number;
    timestamp: string;
    success: boolean;
    error?: string;
    table_name?: string;
    performance_tier?: 'FAST' | 'MEDIUM' | 'SLOW';
    explain_summary?: string;
    optimization_hints?: string[];
}

export interface AggregatedInsights {
    slowest_queries: HistoryEntry[];
    frequent_queries: { query: string; count: number }[];
    impacted_tables: { table: string; activity: number; rows: number }[];
}

export interface Snippet {
    id: string;
    name: string;
    query: string;
    tags: string[];
    is_favorite: boolean;
    created_at: string;
    last_used: string;
}

export interface Role {
    name: string;
    is_superuser: boolean;
    can_login: boolean;
    can_create_db: boolean;
}

export interface Privilege {
    grantee: string;
    schema: string;
    table: string;
    type: string;
}

interface WorkspaceState {
    history: HistoryEntry[];
    snippets: Snippet[];
    snapshots: any[];
    insights: AggregatedInsights | null;
    roles: Role[];
    privileges: Privilege[];
    activeQueries: any[];
    isLoading: boolean;
    error: string | null;
}

function createWorkspaceStore() {
    const { subscribe, set, update } = writable<WorkspaceState>({
        history: [],
        snippets: [],
        snapshots: [],
        insights: null,
        roles: [],
        privileges: [],
        activeQueries: [],
        isLoading: false,
        error: null
    });

    return {
        subscribe,
        async fetchAll() {
            update(s => ({ ...s, isLoading: true }));
            try {
                const [hist, snip, snaps, insights, roles, privs] = await Promise.all([
                    axios.get(`${API_BASE}/db/history`),
                    axios.get(`${API_BASE}/db/snippets`),
                    axios.get(`${API_BASE}/db/schema/snapshots`),
                    axios.get(`${API_BASE}/db/insights`),
                    axios.get(`${API_BASE}/db/roles`),
                    axios.get(`${API_BASE}/db/privileges`)
                ]);

                set({
                    history: hist.data.history || [],
                    snippets: snip.data.snippets || [],
                    snapshots: snaps.data.snapshots || [],
                    insights: insights.data.insights || null,
                    roles: roles.data.roles || [],
                    privileges: privs.data.privileges || [],
                    activeQueries: [],
                    isLoading: false,
                    error: null
                });
            } catch (err: any) {
                update(s => ({ ...s, isLoading: false, error: err.message }));
            }
        },
        async fetchActiveQueries() {
            try {
                const res = await axios.get(`${API_BASE}/db/queries/active`);
                update(s => ({ ...s, activeQueries: res.data.queries || [] }));
            } catch (err: any) {
                console.error('Failed to fetch active queries', err);
            }
        },
        async fetchInsights() {
            try {
                const res = await axios.get(`${API_BASE}/db/insights`);
                update(s => ({ ...s, insights: res.data.insights }));
            } catch (err: any) {
                console.error('Failed to fetch insights', err);
            }
        },
        async saveSnippet(name: string, query: string, tags: string[] = []) {
            try {
                await axios.post(`${API_BASE}/db/snippets`, { name, query, tags });
                await this.fetchAll();
            } catch (err: any) {
                update(s => ({ ...s, error: err.message }));
            }
        },
        async deleteSnippet(id: string) {
            try {
                await axios.delete(`${API_BASE}/db/snippets/${id}`);
                await this.fetchAll();
            } catch (err: any) {
                update(s => ({ ...s, error: err.message }));
            }
        },
        async toggleFavorite(id: string) {
            try {
                await axios.post(`${API_BASE}/db/snippets/${id}/favorite`);
                await this.fetchAll();
            } catch (err: any) {
                update(s => ({ ...s, error: err.message }));
            }
        },
        async trackSnippetUsage(id: string) {
            try {
                await axios.post(`${API_BASE}/db/snippets/${id}/track-usage`);
                await this.fetchAll();
            } catch (err: any) {
                update(s => ({ ...s, error: err.message }));
            }
        },
        async captureSnapshot(name: string) {
            try {
                await axios.post(`${API_BASE}/db/schema/snapshot`, { name });
                await this.fetchAll();
            } catch (err: any) {
                update(s => ({ ...s, error: err.message }));
            }
        }
    };
}


export const workspaceStore = createWorkspaceStore();
