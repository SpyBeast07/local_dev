<script lang="ts">
	import { onMount } from "svelte";
	import axios from "axios";

	let tables = $state<string[]>([]);
	let loading = $state(true);

	let query = $state("");
	let queryResult = $state<any>(null);
	let queryLoading = $state(false);
	let showConfirmModal = $state(false);
	let showRootModal = $state(false);

	function triggerQuery() {
		if (!query.trim()) return;

		// 1. Strip Single-line Comments (-- ...)
		// 2. Strip Multi-line Comments (/* ... */)
		const cleanQuery = query
			.replace(/--.*$/gm, '')
			.replace(/\/\*[\s\S]*?\*\//g, '');

		// Identify destructive/mutating keywords with word boundaries
		const destructiveKeywords = /\b(INSERT|UPDATE|DELETE|DROP|TRUNCATE|ALTER|CREATE|RENAME|GRANT|REVOKE)\b/i;
		const isDangerous = cleanQuery.match(destructiveKeywords);

		if (isDangerous) {
			showConfirmModal = true;
		} else {
			executeSQL();
		}
	}

	function confirmFirst() {
		showConfirmModal = false;
		showRootModal = true;
	}

	function confirmRoot() {
		showRootModal = false;
		executeSQL();
	}

	async function executeSQL() {
		queryLoading = true;
		try {
			const res = await axios.post("http://127.0.0.1:8000/db/query", { query });
			queryResult = res.data;
			
			// Auto refresh schemas
			const tableRes = await axios.get("http://127.0.0.1:8000/db/tables");
			tables = Array.isArray(tableRes.data) ? tableRes.data : [];
		} catch (err: any) {
			queryResult = { success: false, error: err.message };
		} finally {
			queryLoading = false;
		}
	}

	onMount(async () => {
		try {
			const res = await axios.get("http://127.0.0.1:8000/db/tables");
			tables = Array.isArray(res.data) ? res.data : [];
		} catch (err) {
			console.error(err);
		} finally {
			loading = false;
		}
	});
</script>

<div class="flex flex-col gap-10 pb-20">
	<header class="flex flex-col gap-3">
		<div class="flex items-center gap-4">
			<a href="/" class="w-10 h-10 rounded-xl bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 flex items-center justify-center text-slate-400 dark:text-slate-500 hover:text-emerald-600 dark:hover:text-emerald-400 hover:border-emerald-200 dark:hover:border-emerald-800 transition-all shadow-sm" aria-label="Back to dashboard">
				<svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2.5" d="M15 19l-7-7 7-7" /></svg>
			</a>
			<h1 class="text-5xl font-black text-slate-900 dark:text-white tracking-tighter italic uppercase leading-none">Database Schema<span class="text-emerald-500 uppercase italic">.</span></h1>
		</div>
		<p class="text-slate-500 dark:text-slate-400 font-bold uppercase tracking-widest text-xs ml-14">Exploring all schema tables and metadata in PostgreSQL</p>
	</header>

	<!-- SQL RUNNER SECTION -->
	<div class="bg-white dark:bg-slate-900 rounded-[2.5rem] p-8 border border-slate-200 dark:border-slate-800 shadow-xl flex flex-col gap-6 relative overflow-hidden w-full max-w-full">
		<div class="flex items-center justify-between">
			<h2 class="text-sm font-black text-slate-900 dark:text-slate-100 uppercase tracking-widest italic flex items-center gap-2"><span class="text-emerald-500">ROOT</span> Raw SQL Editor</h2>
			{#if queryLoading}
				<div class="flex items-center gap-3 text-[10px] font-bold text-emerald-500 uppercase tracking-widest">
					<div class="w-4 h-4 border-2 border-emerald-500 border-t-transparent rounded-full animate-spin"></div>
					Evaluating...
				</div>
			{/if}
		</div>
		
		<div class="flex flex-col gap-4">
			<textarea
				bind:value={query}
				placeholder="SELECT * FROM users;"
				rows="4"
				class="bg-slate-50 dark:bg-slate-950 p-6 rounded-2xl border border-slate-200 dark:border-slate-800 font-mono text-sm tracking-wider text-slate-700 dark:text-slate-300 placeholder:text-slate-400/50 focus:outline-none focus:border-emerald-500 transition-colors custom-scrollbar resize-y italic"
				onkeydown={(e) => {
					if ((e.ctrlKey || e.metaKey) && e.key === 'Enter') {
						e.preventDefault();
						triggerQuery();
					}
				}}
			></textarea>

			<!-- Schema naming hint -->
			<div class="bg-amber-50 dark:bg-amber-950/30 border border-amber-200 dark:border-amber-800/50 rounded-xl px-4 py-3 flex items-start gap-3">
				<span class="text-amber-500 text-sm mt-0.5 shrink-0">⚠</span>
				<div class="flex flex-col gap-1">
					<p class="text-[11px] font-black text-amber-700 dark:text-amber-400 uppercase tracking-widest">Schema-Qualified Names Required</p>
					<p class="text-[11px] font-bold text-amber-600/80 dark:text-amber-500/80 leading-relaxed">
						PostgreSQL resolves unqualified names against <code class="bg-amber-100 dark:bg-amber-900/50 px-1 rounded font-mono">public</code> only.
						Use the <span class="font-black">SQL Ref</span> shown on each table card.
						Tables in <code class="bg-amber-100 dark:bg-amber-900/50 px-1 rounded font-mono">public</code> can be queried by short name — all others need <code class="bg-amber-100 dark:bg-amber-900/50 px-1 rounded font-mono">schema.table</code>.
					</p>
				</div>
			</div>

			<div class="flex justify-between items-center">
				<span class="text-[10px] font-bold text-slate-400 dark:text-slate-500 uppercase tracking-widest"><kbd class="bg-slate-100 dark:bg-slate-800 px-1.5 py-0.5 rounded">CMD</kbd> + <kbd class="bg-slate-100 dark:bg-slate-800 px-1.5 py-0.5 rounded">ENTER</kbd> TO RUN</span>
				<button 
					onclick={triggerQuery} 
					disabled={!query.trim() || queryLoading}
					class="bg-emerald-500 hover:bg-emerald-600 active:scale-95 px-8 py-3 rounded-xl text-white font-black tracking-widest uppercase transition-all flex justify-center items-center gap-2 text-xs shadow-lg shadow-emerald-500/20 disabled:opacity-50 disabled:shadow-none"
				>
					⚡ Execute Segment
				</button>
			</div>
		</div>

		<!-- SQL RESULTS GRID -->
		{#if queryResult}
			<div class="mt-4 pt-6 border-t border-slate-100 dark:border-slate-800 flex flex-col gap-4">
				<div class="flex items-center justify-between">
					<h3 class="text-xs font-black text-slate-500 uppercase tracking-widest leading-none">Execution Result</h3>
					<button onclick={() => queryResult = null} class="text-[10px] text-slate-400 hover:text-rose-500 font-bold uppercase tracking-widest transition-colors">Clear</button>
				</div>
				
				{#if !queryResult.success}
					<div class="bg-rose-500/10 border border-rose-500/30 text-rose-500 dark:text-rose-400 p-4 rounded-xl text-sm font-bold uppercase tracking-widest font-mono break-all leading-relaxed whitespace-pre-wrap">
						{queryResult.error}
					</div>
				{:else if queryResult.columns && queryResult.data}
					{#if queryResult.is_truncated}
						<div class="bg-amber-500/10 border border-amber-500/30 text-amber-600 dark:text-amber-400 p-4 rounded-xl text-[10px] font-black uppercase tracking-widest flex items-center gap-3">
							<span class="text-lg">🛑</span>
							<span>Result Set Truncated at 1,000 Rows for Performance Safety.</span>
						</div>
					{/if}
					
					<div class="bg-slate-50 dark:bg-slate-950 rounded-2xl border border-slate-200 dark:border-slate-800 overflow-x-auto custom-scrollbar shadow-inner">
						<table class="w-full text-left border-collapse min-w-max">
							<thead>
								<tr>
									{#each queryResult.columns as col}
										<th class="p-4 text-[10px] bg-white dark:bg-slate-900 font-black text-slate-500 uppercase tracking-widest border-b border-r border-slate-200 dark:border-slate-800 whitespace-nowrap">{col}</th>
									{/each}
								</tr>
							</thead>
							<tbody>
								{#each queryResult.data as row}
									<tr class="hover:bg-blue-50/50 dark:hover:bg-slate-900/50 transition-colors group">
										{#each queryResult.columns as col}
											<td class="p-4 text-xs font-mono font-bold text-slate-600 dark:text-slate-300 border-b border-r border-slate-200 dark:border-slate-800 group-hover:border-blue-100 dark:group-hover:border-slate-700 whitespace-nowrap">{row[col] === null ? 'NULL' : String(row[col])}</td>
										{/each}
									</tr>
								{/each}
								{#if queryResult.data.length === 0}
									<tr>
										<td colspan={queryResult.columns.length} class="p-8 text-center text-xs font-bold text-slate-400 uppercase tracking-widest">0 Rows Returned</td>
									</tr>
								{/if}
							</tbody>
						</table>
					</div>
				{:else}
					<div class="bg-emerald-500/10 border border-emerald-500/30 text-emerald-600 dark:text-emerald-400 p-4 rounded-xl text-sm font-bold uppercase tracking-widest font-mono">
						SUCCESS: {queryResult.affected_rows} rows affected.
					</div>
				{/if}
			</div>
		{/if}
	</div>

	{#if loading}
		<div class="flex items-center gap-4 text-emerald-600 dark:text-emerald-400 font-black animate-pulse uppercase tracking-wider text-sm ml-14">
			<div class="w-6 h-6 border-4 border-current border-t-transparent rounded-full animate-spin"></div>
			Exploring Schema...
		</div>
	{:else}
		<div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
			{#each tables as t}
				{@const schema = t.includes('.') ? t.split('.')[0] : 'public'}
				{@const tableName = t.includes('.') ? t.split('.')[1] : t}
				{@const isPublic = schema === 'public'}
				{@const sqlRef = isPublic ? tableName : t}
				<a
					href={`/table/${t}`}
					class="bg-white dark:bg-slate-900 rounded-[2rem] p-8 border border-slate-200/60 dark:border-slate-800 shadow-sm hover:shadow-xl hover:shadow-emerald-500/5 transition-all duration-500 group flex flex-col gap-6"
				>
					<div class="flex justify-between items-start">
						<div class="w-12 h-12 bg-emerald-50 dark:bg-emerald-900/20 text-emerald-600 dark:text-emerald-400 rounded-2xl flex items-center justify-center text-xl shadow-inner border border-emerald-100 dark:border-emerald-900/30">
							<svg class="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M3 10h18M3 14h18m-9-4v8m-7 0h14a2 2 0 002-2V8a2 2 0 00-2-2H5a2 2 0 00-2 2v8a2 2 0 002 2z" /></svg>
						</div>
						<div class="flex items-center gap-2">
							<span class="text-[10px] font-black px-2.5 py-1 rounded-lg uppercase tracking-widest leading-none {isPublic ? 'bg-emerald-50 dark:bg-emerald-900/20 text-emerald-600 dark:text-emerald-400' : 'bg-amber-50 dark:bg-amber-900/20 text-amber-600 dark:text-amber-400'}">
								{schema}
							</span>
							<div class="w-10 h-10 rounded-xl bg-slate-50 dark:bg-slate-950 border border-slate-100 dark:border-slate-800 flex items-center justify-center text-slate-300 dark:text-slate-700 group-hover:text-emerald-500 transition-colors">
								<svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2.5" d="M9 5l7 7-7 7" /></svg>
							</div>
						</div>
					</div>

					<div>
						<h3 class="text-2xl font-black text-slate-900 dark:text-white group-hover:text-emerald-600 dark:group-hover:text-emerald-400 transition-colors tracking-tight uppercase italic leading-none">{tableName}</h3>
						<div class="flex items-center gap-2 mt-3">
							<span class="w-1.5 h-1.5 rounded-full bg-emerald-500 group-hover:animate-ping"></span>
							<span class="text-[10px] font-black text-slate-400 dark:text-slate-500 uppercase tracking-widest leading-none">Table</span>
						</div>
					</div>

					<div class="pt-4 border-t border-slate-50 dark:border-slate-800 mt-auto flex flex-col gap-1.5">
						<span class="text-[9px] font-black text-slate-400 dark:text-slate-500 uppercase tracking-widest leading-none">SQL Ref</span>
						<code class="text-[11px] font-mono font-bold {isPublic ? 'text-emerald-600 dark:text-emerald-400' : 'text-amber-600 dark:text-amber-400'} leading-none">{sqlRef}</code>
					</div>
				</a>
			{:else}
				<div class="col-span-full py-20 flex flex-col items-center gap-6 text-slate-300 dark:text-slate-700">
					<div class="text-8xl opacity-10 italic font-black uppercase tracking-tighter leading-none">Void</div>
					<p class="text-sm font-bold uppercase tracking-[0.3em]">No tables found</p>
				</div>
			{/each}
		</div>
	{/if}
</div>

<!-- FIRST CONFIRMATION MODAL -->
{#if showConfirmModal}
<div class="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-900/80 backdrop-blur-sm">
	<div class="bg-white dark:bg-slate-950 border border-amber-500/30 shadow-2xl rounded-3xl p-8 max-w-sm w-full flex flex-col gap-6 animate-in slide-in-from-bottom-8 duration-200">
		<div class="w-16 h-16 rounded-full bg-amber-500/10 text-amber-500 flex items-center justify-center text-3xl mx-auto shadow-inner shadow-amber-500/20">⚠️</div>
		<div class="text-center space-y-2">
			<h3 class="text-xl font-black text-slate-900 dark:text-white uppercase tracking-tighter italic">Destructive Action Detected</h3>
			<p class="text-xs font-bold text-slate-500 uppercase tracking-widest leading-relaxed">Are you sure you want to run this modifying SQL payload against the root database?</p>
		</div>
		<div class="flex gap-3">
			<button onclick={() => showConfirmModal = false} class="flex-1 px-4 py-3 rounded-xl bg-slate-100 dark:bg-slate-800 text-slate-500 font-bold uppercase tracking-widest text-xs hover:bg-slate-200 dark:hover:bg-slate-700 transition-colors">Cancel</button>
			<button onclick={confirmFirst} class="flex-1 px-4 py-3 rounded-xl bg-amber-500 text-white font-black uppercase tracking-widest text-xs hover:bg-amber-600 transition-colors shadow-lg shadow-amber-500/20">Acknowledge</button>
		</div>
	</div>
</div>
{/if}

<!-- ROOT DOUBLE CONFIRMATION MODAL -->
{#if showRootModal}
<div class="fixed inset-0 z-50 flex items-center justify-center p-4 bg-rose-950/90 backdrop-blur-md">
	<div class="bg-rose-950 border-2 border-rose-500 shadow-2xl shadow-rose-900/50 rounded-3xl p-8 max-w-sm w-full flex flex-col gap-6 animate-in zoom-in-95 duration-200">
		<div class="w-16 h-16 rounded-full bg-rose-500/20 text-rose-500 flex items-center justify-center text-3xl mx-auto animate-pulse">☢️</div>
		<div class="text-center space-y-3">
			<h3 class="text-2xl font-black text-white uppercase tracking-tighter italic">FINAL WARNING</h3>
			<p class="text-xs font-bold text-rose-300 uppercase tracking-widest leading-relaxed">This action provides absolute mutability to root schemas and data arrays. It CANNOT be undone.</p>
		</div>
		<div class="flex gap-3 mt-4">
			<button onclick={() => showRootModal = false} class="flex-1 px-4 py-4 rounded-xl border border-rose-500/30 text-rose-300 font-bold uppercase tracking-widest text-xs hover:bg-rose-500/10 transition-colors">Abort</button>
			<button onclick={confirmRoot} class="flex-1 px-4 py-4 rounded-xl bg-rose-600 text-white font-black uppercase tracking-widest text-xs hover:bg-rose-500 transition-colors shadow-lg shadow-rose-600/50">Proceed</button>
		</div>
	</div>
</div>
{/if}

<style>
	.custom-scrollbar::-webkit-scrollbar {
		width: 6px;
		height: 6px;
	}
	.custom-scrollbar::-webkit-scrollbar-track {
		background: transparent;
	}
	.custom-scrollbar::-webkit-scrollbar-thumb {
		background: #334155;
		border-radius: 10px;
	}
	.custom-scrollbar::-webkit-scrollbar-thumb:hover {
		background: #475569;
	}
</style>
