<script lang="ts">
	import { workspaceStore } from '$lib/stores/workspaceStore';
	import { schemaStore } from '$lib/stores/schemaStore';
	import { fade, slide } from 'svelte/transition';
	import axios from 'axios';

	let showingDiff = $state<any>(null);
	let selectedSnapshotId = $state('');
	let snapshotName = $state('');
	let isCapturing = $state(false);
	let generatedMigration = $state('');
	
	let isExecuting = $state(false);
	let showConfirmExecute = $state(false);
	let executionResult = $state<{success: boolean, message?: string, error?: string} | null>(null);
	let autoSnapshot = $state(true);

	async function captureSnapshot() {
		if (!snapshotName) return;
		isCapturing = true;
		await workspaceStore.captureSnapshot(snapshotName);
		snapshotName = '';
		isCapturing = false;
	}

	function checkBlastRadius(tableName: string) {
		const fullTable = tableName.includes('.') ? tableName : `public.${tableName}`;
		const dependents = $schemaStore.relations.filter(r => 
			(r.target_table.includes('.') ? r.target_table : `public.${r.target_table}`) === fullTable
		);
		return dependents.length;
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
		let sql = `-- Migration generated for ${showingDiff.snapshotName}\n-- Created: ${new Date().toLocaleString()}\n\n`;
		
		if (removed.length > 0) {
			sql += `-- TRUNCATING / DROPPING TABLES (HIGH IMPACT)\n`;
			removed.forEach(t => {
				const radius = checkBlastRadius(t);
				if (radius > 0) sql += `-- WARNING: Table ${t} has ${radius} dependent relations!\n`;
				sql += `DROP TABLE IF EXISTS ${t} CASCADE;\n`;
			});
			sql += '\n';
		}

		if (added.length > 0) {
			sql += `-- ADDING NEW TABLES\n`;
			added.forEach(t => {
				sql += `-- Note: Structure must be defined manually for full recreation\n`;
				sql += `CREATE TABLE ${t} (\n  id SERIAL PRIMARY KEY,\n  created_at TIMESTAMPTZ DEFAULT NOW()\n);\n`;
			});
			sql += '\n';
		}

		if (modified.length > 0) {
			sql += `-- MODIFYING EXISTING TABLES\n`;
			modified.forEach(m => {
				m.addedCols.forEach((c: string) => {
					sql += `ALTER TABLE ${m.table} ADD COLUMN ${c} TEXT; -- Defaulting to TEXT, adjust types\n`;
				});
				m.removedCols.forEach((c: string) => {
					sql += `ALTER TABLE ${m.table} DROP COLUMN ${c};\n`;
				});
				sql += '\n';
			});
		}

		generatedMigration = sql || '-- No changes detected';
	}

	async function runMigration() {
		isExecuting = true;
		executionResult = null;
		
		try {
			if (autoSnapshot) {
				const safetyName = `Pre-Migration_${new Date().toISOString().split('.')[0].replace(/:/g, '-')}`;
				await workspaceStore.captureSnapshot(safetyName);
			}

			const res = await axios.post('http://127.0.0.1:8000/db/execute-migration', {
				query: generatedMigration
			});
			
			executionResult = res.data;
			if (res.data.success) {
				await workspaceStore.fetchAll();
				await schemaStore.refresh();
			}
		} catch (err: any) {
			executionResult = { success: false, error: err.message };
		} finally {
			isExecuting = false;
			showConfirmExecute = false;
		}
	}
</script>

<div class="flex flex-col h-full overflow-hidden animate-in fade-in slide-in-from-bottom-4 duration-500 relative">
	<!-- Confirm Modal -->
	{#if showConfirmExecute}
		<div class="absolute inset-0 z-50 flex items-center justify-center p-8 bg-slate-950/80 backdrop-blur-md animate-in fade-in duration-300">
			<div class="bg-white dark:bg-slate-900 border border-indigo-500/30 rounded-[3rem] p-10 max-w-xl w-full shadow-2xl space-y-8 animate-in zoom-in-95 duration-300">
				<div class="text-center space-y-4">
					<div class="text-5xl">🛡️</div>
					<h3 class="text-3xl font-black text-slate-900 dark:text-white uppercase tracking-tighter italic">Migration Integrity <span class="text-indigo-500">Seal</span></h3>
					<p class="text-xs font-bold text-slate-500 dark:text-slate-400 uppercase tracking-widest leading-relaxed px-6">
						You are about to apply structural mutations to the root schema. This action will be audited and logged in the execution registry.
					</p>
				</div>

				<div class="p-6 bg-slate-50 dark:bg-slate-950 rounded-3xl border border-slate-100 dark:border-slate-800 space-y-4">
					<div class="flex items-center justify-between">
						<span class="text-[10px] font-black text-slate-400 uppercase tracking-widest">Blast Radius</span>
						<div class="flex gap-2">
							<span class="px-2 py-0.5 rounded bg-emerald-500/10 text-emerald-500 text-[9px] font-black uppercase">+{showingDiff.added.length} Added</span>
							<span class="px-2 py-0.5 rounded bg-rose-500/10 text-rose-500 text-[9px] font-black uppercase">-{showingDiff.removed.length} Dropped</span>
						</div>
					</div>
					<label class="flex items-center gap-3 cursor-pointer group">
						<input type="checkbox" bind:checked={autoSnapshot} class="w-5 h-5 rounded-lg border-2 border-slate-300 dark:border-slate-700 bg-transparent text-indigo-500 focus:ring-indigo-500 transition-all cursor-pointer" />
						<div class="flex flex-col">
							<span class="text-[11px] font-black text-slate-700 dark:text-slate-200 uppercase tracking-widest group-hover:text-indigo-500 transition-colors">Automatic Safety Snapshot</span>
							<span class="text-[9px] font-bold text-slate-400 uppercase tracking-tighter">Capture current state before mutating</span>
						</div>
					</label>
				</div>

				<div class="flex gap-4">
					<button 
						onclick={() => showConfirmExecute = false}
						class="flex-1 py-4 rounded-2xl bg-slate-100 dark:bg-slate-800 text-slate-500 font-bold uppercase tracking-widest text-xs hover:bg-slate-200 dark:hover:bg-slate-700 transition-colors"
					>
						Abort
					</button>
					<button 
						onclick={runMigration}
						disabled={isExecuting}
						class="flex-[1.5] py-4 rounded-2xl bg-indigo-600 hover:bg-emerald-600 text-white font-black uppercase tracking-widest text-xs shadow-xl shadow-indigo-600/20 active:scale-95 transition-all flex items-center justify-center gap-3"
					>
						{#if isExecuting}
							<div class="w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin"></div>
							Executing integrity seal...
						{:else}
							<svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="3" d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z"></path></svg>
							Authorize & Execute
						{/if}
					</button>
				</div>
			</div>
		</div>
	{/if}

	<div class="p-6 border-b border-slate-200 dark:border-slate-800 bg-white/40 dark:bg-slate-900/40 flex flex-col gap-6">
		<div class="flex items-center justify-between">
			<div>
				<h3 class="text-sm font-black text-slate-900 dark:text-white uppercase tracking-widest italic tracking-widest leading-none">Safe Migration Layer</h3>
				<p class="text-[10px] text-slate-500 font-bold uppercase tracking-widest mt-1 italic leading-none">Structural Audit & Atomic Evolution</p>
			</div>
			<div class="flex items-center gap-2">
				<input 
					type="text" 
					placeholder="Snapshot Name..." 
					bind:value={snapshotName}
					class="px-4 py-2 rounded-xl bg-white dark:bg-slate-950 border border-slate-200 dark:border-slate-800 text-[10px] font-bold outline-none focus:ring-4 focus:ring-indigo-500/10 transition-all w-48"
				/>
				<button 
					onclick={captureSnapshot}
					disabled={!snapshotName || isCapturing}
					class="px-5 py-2.5 rounded-xl bg-indigo-600 hover:bg-emerald-500 text-white text-[10px] font-black uppercase tracking-widest transition-all shadow-lg active:scale-95 disabled:opacity-50"
				>
					{isCapturing ? 'Saving...' : 'Capture Snapshot'}
				</button>
			</div>
		</div>
	</div>

	<div class="flex-1 overflow-hidden flex flex-col md:flex-row">
		<!-- Sidebar: Saved Versions -->
		<div class="w-full md:w-72 border-r border-slate-200 dark:border-slate-800 bg-slate-50/50 dark:bg-slate-950/20 flex flex-col overflow-y-auto p-6 space-y-3 custom-scrollbar">
			<span class="text-[9px] font-black text-slate-400 uppercase tracking-widest mb-2 block border-b border-slate-200 dark:border-slate-800 pb-2">Versioning History</span>
			{#each [...$workspaceStore.snapshots].reverse() as snap}
				<button 
					onclick={() => { selectedSnapshotId = snap.id; compareSchema(); executionResult = null; }}
					class={[
						"w-full text-left px-5 py-4 rounded-2xl border transition-all flex flex-col gap-1 relative overflow-hidden group",
						selectedSnapshotId === snap.id 
							? "bg-indigo-600 border-indigo-500 text-white shadow-2xl scale-[1.02] z-10" 
							: "bg-white dark:bg-slate-900 border-slate-200 dark:border-slate-800 hover:border-indigo-500/50"
					].join(" ")}
				>
					{#if selectedSnapshotId === snap.id}
						<div class="absolute inset-0 bg-gradient-to-r from-white/10 to-transparent"></div>
					{/if}
					<span class="text-[11px] font-black uppercase tracking-widest italic">{snap.name}</span>
					<span class="text-[9px] opacity-70 font-bold uppercase tracking-tighter">{snap.timestamp}</span>
				</button>
			{:else}
				<div class="flex flex-col items-center justify-center h-40 opacity-20 text-center">
					<p class="text-[10px] font-black uppercase tracking-widest leading-relaxed">No snapshotted states available</p>
				</div>
			{/each}
		</div>

		<!-- Viewport: Comparative Analysis -->
		<div class="flex-1 overflow-y-auto p-10 space-y-12 custom-scrollbar">
			{#if executionResult}
				<div 
					in:fade
					class="p-10 rounded-[3rem] border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900 shadow-2xl space-y-8 animate-in zoom-in-95"
				>
					<div class="text-center space-y-4">
						<div class="text-6xl">{executionResult.success ? '✅' : '❌'}</div>
						<h4 class="text-3xl font-black text-slate-900 dark:text-white uppercase tracking-tighter italic">
							{executionResult.success ? 'Integrity Seal Applied' : 'Migration Collision'}
						</h4>
						<p class="text-[10px] font-bold text-slate-500 uppercase tracking-widest italic">
							{executionResult.success ? 'New architectural state has been persisted and registered.' : 'Architectural mutations failed reconciliation.'}
						</p>
					</div>

					{#if !executionResult.success}
						<div class="p-6 bg-rose-500/10 border border-rose-500/20 rounded-3xl">
							<p class="text-[11px] font-mono font-medium text-rose-500 leading-relaxed whitespace-pre-wrap">{executionResult.error}</p>
						</div>
					{/if}

					<div class="flex justify-center">
						<button 
							onclick={() => executionResult = null}
							class="px-8 py-3 rounded-2xl bg-indigo-600 text-white text-[10px] font-black uppercase tracking-widest shadow-xl shadow-indigo-600/20 active:scale-95 transition-all"
						>
							Restore Viewport
						</button>
					</div>
				</div>
			{:else if showingDiff}
				<div class="animate-in fade-in slide-in-from-right-4 duration-700 space-y-10">
					<header class="space-y-2">
						<h4 class="text-3xl font-black text-slate-900 dark:text-white uppercase italic tracking-tighter leading-none">
							Structural Comparative
						</h4>
						<p class="text-[10px] font-bold text-slate-500 uppercase tracking-[0.3em] italic">
							Comparing <span class="text-indigo-500">Live Schema</span> against <span class="text-slate-900 dark:text-white underline decoration-indigo-500/50 decoration-2">{showingDiff.snapshotName}</span>
						</p>
					</header>

					<div class="grid grid-cols-1 md:grid-cols-3 gap-6">
						<!-- ADDED (Green) -->
						<div class="p-6 bg-emerald-500/10 border border-emerald-500/20 rounded-3xl group hover:shadow-xl hover:shadow-emerald-500/10 transition-all flex flex-col">
							<div class="flex items-center gap-2 mb-6">
								<span class="text-xs">🌱</span>
								<span class="text-[10px] font-black text-emerald-500 uppercase tracking-[0.3em]">Added Entities</span>
							</div>
							<div class="flex flex-wrap gap-2 flex-1 items-start">
								{#each showingDiff.added as table}
									<div class="px-3 py-2 bg-emerald-500/10 border border-emerald-500/20 rounded-xl text-[10px] font-black uppercase tracking-widest text-emerald-600 dark:text-emerald-400">
										{table}
									</div>
								{:else}
									<p class="text-[9px] text-slate-400 font-bold uppercase tracking-widest italic mt-4">Static Entity Set</p>
								{/each}
							</div>
						</div>

						<!-- REMOVED (Red) -->
						<div class="p-6 bg-rose-500/10 border border-rose-500/20 rounded-3xl group hover:shadow-xl hover:shadow-rose-500/10 transition-all flex flex-col">
							<div class="flex items-center gap-2 mb-6">
								<span class="text-xs">⚠️</span>
								<span class="text-[10px] font-black text-rose-500 uppercase tracking-[0.3em]">Removed Entities</span>
							</div>
							<div class="flex flex-col gap-3 flex-1">
								{#each showingDiff.removed as table}
									<div class="flex items-center justify-between p-3 bg-rose-500/10 border border-rose-500/20 rounded-xl">
										<span class="text-[10px] font-black uppercase tracking-widest text-rose-600 dark:text-rose-400">{table}</span>
										{#if checkBlastRadius(table) > 0}
											<span class="px-2 py-0.5 rounded-full bg-rose-600 text-white text-[8px] font-black uppercase tracking-tighter flex items-center gap-1 shadow-lg shadow-rose-600/30">
												Radius: {checkBlastRadius(table)}
											</span>
										{/if}
									</div>
								{:else}
									<p class="text-[9px] text-slate-400 font-bold uppercase tracking-widest italic mt-4 whitespace-nowrap">No Entity Volatility</p>
								{/each}
							</div>
						</div>

						<!-- MODIFIED (Yellow) -->
						<div class="p-6 bg-amber-500/10 border border-amber-500/20 rounded-3xl group hover:shadow-xl hover:shadow-amber-500/10 transition-all flex flex-col">
							<div class="flex items-center gap-2 mb-6">
								<span class="text-xs">⚡</span>
								<span class="text-[10px] font-black text-amber-500 uppercase tracking-[0.3em]">Modified Fields</span>
							</div>
							<div class="flex flex-col gap-2 flex-1">
								{#each showingDiff.modified as mod}
									<div class="p-3 bg-white dark:bg-slate-900 border border-amber-500/20 rounded-xl">
										<p class="text-[10px] font-black text-slate-700 dark:text-slate-300 uppercase tracking-widest mb-2 border-b border-amber-500/10 pb-1 italic">{mod.table}</p>
										<div class="flex flex-wrap gap-1">
											{#each mod.addedCols as c}
												<span class="px-1.5 py-0.5 bg-emerald-500/10 text-emerald-500 text-[8px] font-bold uppercase tracking-tighter border border-emerald-500/10 rounded-md">+{c}</span>
											{/each}
											{#each mod.removedCols as c}
												<span class="px-1.5 py-0.5 bg-rose-500/10 text-rose-500 text-[8px] font-bold uppercase tracking-tighter border border-rose-500/10 rounded-md">-{c}</span>
											{/each}
										</div>
									</div>
								{:else}
									<p class="text-[9px] text-slate-400 font-bold uppercase tracking-widest italic mt-4">No internal changes</p>
								{/each}
							</div>
						</div>
					</div>

					<div class="space-y-4 pt-10">
						<div class="flex items-center justify-between">
							<div class="flex items-center gap-4">
								<span class="text-[10px] font-black text-slate-400 uppercase tracking-[0.2em] italic leading-none">Automated Forward Migration</span>
								<div class="h-2 w-2 rounded-full bg-indigo-500 animate-pulse"></div>
							</div>
							<div class="flex items-center gap-3">
								<button 
									onclick={(event: any) => {
										navigator.clipboard.writeText(generatedMigration);
										const btn = event.currentTarget as HTMLButtonElement;
										btn.textContent = 'Copied!';
										setTimeout(() => btn.textContent = 'Copy Logic', 2000);
									}}
									class="px-4 py-1.5 rounded-full bg-slate-100 dark:bg-slate-800 text-[9px] font-black text-slate-600 dark:text-slate-400 uppercase tracking-widest border border-slate-200 dark:border-slate-700 hover:bg-slate-200 transition-all shadow-sm"
								>
									Copy Logic
								</button>
								<button 
									onclick={() => showConfirmExecute = true}
									class="px-6 py-1.5 rounded-full bg-indigo-600 hover:bg-emerald-600 text-white text-[9px] font-black uppercase tracking-widest transition-all shadow-lg shadow-indigo-600/20 active:scale-95"
								>
									Run Migration
								</button>
							</div>
						</div>
						<div class="bg-indigo-950 p-8 rounded-[40px] border border-indigo-500/30 shadow-2xl relative overflow-hidden group/m">
							<div class="absolute inset-0 bg-[radial-gradient(circle_at_top_right,rgba(99,102,241,0.1),transparent)] pointer-events-none"></div>
							<pre class="text-[11px] font-mono font-medium text-indigo-300/90 selection:bg-indigo-500/40 leading-relaxed font-mono whitespace-pre-wrap">{generatedMigration}</pre>
						</div>
					</div>
				</div>
			{:else}
				<div class="h-full flex flex-col items-center justify-center text-slate-500 gap-6 opacity-30 animate-in fade-in zoom-in-95 duration-1000">
					<div class="text-[120px] filter saturate-0 hover:saturate-100 transition-all cursor-default">🔭</div>
					<div class="text-center space-y-2">
						<p class="text-sm font-black uppercase tracking-[0.5em] text-indigo-500">Audit View Dead</p>
						<p class="text-[10px] font-bold uppercase tracking-widest leading-relaxed">Select a version from history to initialize comparative analysis</p>
					</div>
				</div>
			{/if}
		</div>
	</div>
</div>
