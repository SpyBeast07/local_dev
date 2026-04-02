import { writable } from 'svelte/store';
import axios from 'axios';

export interface SchemaMetadata {
	[tableName: string]: string[];
}

function createSchemaStore() {
	const { subscribe, set, update } = writable<{
		metadata: SchemaMetadata;
		loading: boolean;
		error: string | null;
		lastUpdated: number | null;
	}>({
		metadata: {},
		loading: false,
		error: null,
		lastUpdated: null
	});

	async function fetchSchema() {
		update((s) => ({ ...s, loading: true, error: null }));
		try {
			// Backend endpoint implemented in backend/main.py
			const res = await axios.get('http://127.0.0.1:8000/db/schema');
			if (res.data.success) {
				set({
					metadata: res.data.schema,
					loading: false,
					error: null,
					lastUpdated: Date.now()
				});
			} else {
				throw new Error(res.data.error || 'Failed to fetch schema');
			}
		} catch (err: any) {
			update((s) => ({
				...s,
				loading: false,
				error: err.message || 'Unknown error fetching schema'
			}));
		}
	}

	return {
		subscribe,
		fetchSchema,
		refresh: fetchSchema
	};
}

export const schemaStore = createSchemaStore();
