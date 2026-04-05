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
}

export interface Snippet {
    id: string;
    name: string;
    query: string;
    tags: string[];
    created_at: string;
}

export interface Role {
    name: string;
    is_superuser: boolean;
    can_inherit: boolean;
    can_create_role: boolean;
    can_create_db: boolean;
    can_login: boolean;
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
    roles: Role[];
    privileges: Privilege[];
    snapshots: any[];
    isLoading: boolean;
    error: string | null;
}

function createWorkspaceStore() {
    const { subscribe, set, update } = writable<WorkspaceState>({
        history: [],
        snippets: [],
        roles: [],
        privileges: [],
        snapshots: [],
        isLoading: false,
        error: null
    });

    return {
        subscribe,
        async fetchAll() {
            update(s => ({ ...s, isLoading: true }));
            try {
                const [hist, snip, roles, snaps] = await Promise.all([
                    axios.get(`${API_BASE}/db/history`),
                    axios.get(`${API_BASE}/db/snippets`),
                    axios.get(`${API_BASE}/db/roles-permissions`),
                    axios.get(`${API_BASE}/db/schema/snapshots`)
                ]);

                set({
                    history: hist.data.history || [],
                    snippets: snip.data.snippets || [],
                    roles: roles.data.roles || [],
                    privileges: roles.data.privileges || [],
                    snapshots: snaps.data.snapshots || [],
                    isLoading: false,
                    error: null
                });
            } catch (err: any) {
                update(s => ({ ...s, isLoading: false, error: err.message }));
            }
        },
        async saveSnippet(name: string, query: string, tags: string[] = []) {
            try {
                await axios.post(`${API_BASE}/db/snippets`, { name, query, tags });
                this.fetchAll();
            } catch (err: any) {
                update(s => ({ ...s, error: err.message }));
            }
        },
        async deleteSnippet(id: string) {
            try {
                await axios.delete(`${API_BASE}/db/snippets/${id}`);
                this.fetchAll();
            } catch (err: any) {
                update(s => ({ ...s, error: err.message }));
            }
        },
        async captureSnapshot(name: string) {
            try {
                await axios.post(`${API_BASE}/db/schema/snapshot`, { name });
                this.fetchAll();
            } catch (err: any) {
                update(s => ({ ...s, error: err.message }));
            }
        }
    };
}

export const workspaceStore = createWorkspaceStore();
