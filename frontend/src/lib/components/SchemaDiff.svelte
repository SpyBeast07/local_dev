<script lang="ts">
	import { workspaceStore } from '$lib/stores/workspaceStore';
	import { schemaStore } from '$lib/stores/schemaStore';
	import axios from 'axios';

	let showingDiff = $state<any>(null);
	let selectedSnapshotId = $state('');
	let snapshotName = $state('');
	let isCapturing = $state(false);
	let generatedMigration = $state('');

	async function captureSnapshot() {
		if (!snapshotName) return;
		isCapturing = true;
		await workspaceStore.captureSnapshot(snapshotName);
		snapshotName = '';
		isCapturing = false;
	}

	function compareSchema() {
		const snapshot = $workspaceStore.snapshots.find(s => s.id === selectedSnapshotId);
		if (!snapshot) return;

		const current = $schemaStore.metadata;
		const snap = snapshot.schema;

		const added = Object.keys(current).filter(t => !snap[t]);
		const removed = Object.keys(snap).filter(t => !current[t]);
		
		const modified: any[] = [];
		Object.keys(current).forEach(t => {
			if (snap[t]) {
				const currentCols = current[t];
				const snapCols = snap[t].map((c: any) => c.column);
				const addedCols = currentCols.filter(c => !snapCols.includes(c));
				const removedCols = snapCols.filter((c: any) => !currentCols.includes(c));
				
				if (addedCols.length > 0 || removedCols.length > 0) {
					modified.push({ table: t, addedCols, removedCols });
				}
			}
		});

		showingDiff = { added, removed, modified, snapshotName: snapshot.name };
		generateMigration(added, removed, modified);
	}

	function generateMigration(added: string[], removed: string[], modified: any[]) {
		let sql = `-- Migration generated for ${showingDiff.snapshotName}\n\n`;
		
		added.forEach(t => {
			sql += `-- Warning: Full CREATE TABLE statement not fully reconstructible from simple snapshot\n`;
			sql += `CREATE TABLE ${t} (\n  /* columns here */\n);\n\n`;
		});

		removed.forEach(t => {
			sql += `DROP TABLE ${t};\n\n`;
		});

		modified.forEach(m => {
			m.addedCols.forEach((c: string) => {
				sql += `ALTER TABLE ${m.table} ADD COLUMN ${c} /* type here */;\n`;
			});
			m.removedCols.forEach((c: string) => {
				sql += `ALTER TABLE ${m.table} DROP COLUMN ${c};\n`;
			});
			sql += '\n';
		});

		generatedMigration = sql;
	}
</script>

<div class="flex flex-col h-full overflow-hidden animate-in fade-in slide-in-from-bottom-4 duration-500">
	<div class="p-6 border-b border-slate-200 dark:border-slate-800 bg-white/40 dark:bg-slate-900/40 flex items-center justify-between">
		<div>
			<h3 class="text-sm font-black text-slate-900 dark:text-white uppercase tracking-widest italic">Schema Audit Engine</h3>
			<p class="text-[10px] text-slate-500 font-bold uppercase tracking-widest mt-1">Snapshot point-in-time comparison & diffing</p>
		</div>
		<div class="flex items-center gap-3">
			<input 
				type="text" 
				placeholder="Snapshot Name..." 
				bind:value={snapshotName}
				class="px-4 py-2 rounded-xl bg-white dark:bg-slate-950 border border-slate-200 dark:border-slate-800 text-[11px] font-bold focus:ring-2 focus:ring-indigo-500/50 transition-all shadow-inner"
			/>
			<button 
				onclick={captureSnapshot}
				disabled={!snapshotName || isCapturing}
				class="px-5 py-2.5 rounded-xl bg-indigo-600 hover:bg-indigo-500 text-white text-[10px] font-black uppercase tracking-widest transition-all shadow-lg shadow-indigo-500/20 disabled:opacity-50"
			>
				{isCapturing ? 'Capturing...' : '+ Create Snapshot'}
			</button>
		</div>
	</div>

	<div class="flex-1 overflow-hidden flex flex-col md:flex-row">
		<!-- Sidebar: Snapshot List -->
		<div class="w-full md:w-64 border-r border-slate-200 dark:border-slate-800 bg-slate-50/50 dark:bg-slate-950/20 flex flex-col overflow-y-auto p-4 space-y-2 custom-scrollbar">
			<span class="text-[9px] font-black text-slate-400 uppercase tracking-widest mb-2 block px-2">Saved Versions</span>
			{#each $workspaceStore.snapshots as snap}
				<button 
					onclick={() => { selectedSnapshotId = snap.id; compareSchema(); }}
					class={[
						"w-full text-left px-4 py-3 rounded-2xl border transition-all flex flex-col gap-1",
						selectedSnapshotId === snap.id 
							? "bg-indigo-600 border-indigo-500 text-white shadow-xl" 
							: "bg-white dark:bg-slate-900 border-slate-200 dark:border-slate-800 text-slate-600 dark:text-slate-400 hover:border-indigo-500/50"
					].join(" ")}
				>
					<span class="text-[11px] font-black uppercase tracking-tighter italic">{snap.name}</span>
					<span class="text-[9px] opacity-70 font-bold">{snap.timestamp}</span>
				</button>
			{:else}
				<p class="text-[10px] font-bold text-slate-500 italic px-2">No snapshots found.</p>
			{/each}
		</div>

		<!-- Main content: Diff & Migration -->
		<div class="flex-1 overflow-y-auto p-8 space-y-10 custom-scrollbar">
			{#if showingDiff}
				<div class="animate-in fade-in zoom-in-95 duration-500 space-y-8">
					<div class="flex items-center justify-between">
						<h4 class="text-xl font-black text-slate-900 dark:text-white uppercase italic tracking-tighter">
							Comparison: <span class="text-indigo-500">Live</span> vs <span class="text-slate-400">{showingDiff.snapshotName}</span>
						</h4>
					</div>

					<div class="grid grid-cols-1 md:grid-cols-2 gap-6">
						<!-- Added Tables -->
						<div class="p-6 bg-emerald-500/5 border border-emerald-500/10 rounded-3xl">
							<span class="text-[10px] font-black text-emerald-500 uppercase tracking-[0.2em] mb-4 block">Added Entities</span>
							<div class="flex flex-wrap gap-2">
								{#each showingDiff.added as table}
									<span class="px-3 py-1 bg-emerald-500/10 text-emerald-500 border border-emerald-500/20 rounded-xl text-[10px] font-black uppercase tracking-widest">{table}</span>
								{:else}
									<span class="text-[10px] text-slate-500 font-bold italic">No new tables</span>
								{/each}
							</div>
						</div>

						<!-- Removed Tables -->
						<div class="p-6 bg-rose-500/5 border border-rose-500/10 rounded-3xl">
							<span class="text-[10px] font-black text-rose-500 uppercase tracking-[0.2em] mb-4 block">Removed Entities</span>
							<div class="flex flex-wrap gap-2">
								{#each showingDiff.removed as table}
									<span class="px-3 py-1 bg-rose-500/10 text-rose-500 border border-rose-500/20 rounded-xl text-[10px] font-black uppercase tracking-widest">{table}</span>
								{:else}
									<span class="text-[10px] text-slate-500 font-bold italic">No deleted tables</span>
								{/each}
							</div>
						</div>
					</div>

					<!-- Migration Generator -->
					<div class="space-y-4">
						<div class="flex items-center justify-between">
							<span class="text-[10px] font-black text-slate-400 uppercase tracking-widest italic leading-none">Migration Generator (Postgres)</span>
							<button 
								onclick={() => navigator.clipboard.writeText(generatedMigration)}
								class="text-[9px] font-black text-indigo-500 hover:text-indigo-400 uppercase tracking-widest"
							>
								Copy SQL
							</button>
						</div>
						<div class="bg-slate-950 p-6 rounded-3xl border border-slate-800 shadow-2xl relative overflow-hidden group">
							<div class="absolute inset-0 bg-gradient-to-br from-indigo-500/5 to-transparent pointer-events-none"></div>
							<pre class="text-[11px] font-mono font-medium text-slate-300 selection:bg-indigo-500/30">{generatedMigration}</pre>
						</div>
					</div>
				</div>
			{:else}
				<div class="h-full flex flex-col items-center justify-center text-slate-500 gap-4 opacity-40">
					<div class="text-6xl">🔭</div>
					<p class="text-xs font-black uppercase tracking-[0.3em]">Select Snapshot to Audit</p>
					<p class="text-[10px] font-bold uppercase tracking-widest text-center">Compare the current live schema against a saved historic state</p>
				</div>
			{/if}
		</div>
	</div>
</div>
