<script lang="ts">
	import { onMount } from 'svelte';
	import axios from 'axios';
	import { fade } from 'svelte/transition';

	let tables = $state<string[]>([]);
	let loading = $state(true);

	let query = $state('');
	let queryResult = $state<any>(null);
	let queryLoading = $state(false);
	let showConfirmModal = $state(false);
	let showRootModal = $state(false);
	let queryTrace = $state<any>(null);
	let backupLoading = $state(false);
	let restoreLoading = $state(false);
	let showRestoreModal = $state(false);
	let restoreFile = $state<File | null>(null);
	let restoreClean = $state(false);
	let showExportDropdown = $state(false);

	let dbName = $state('postgres');
	let typedConfirmation = $state('');

	async function fetchDbConfig() {
		try {
			const res = await axios.get('http://127.0.0.1:8000/config/db');
			dbName = res.data.db_name || 'postgres';
		} catch (err) {
			console.error('Failed to fetch db config', err);
		}
	}

	onMount(() => {
		fetchDbConfig();
	});


	function triggerQuery() {
		if (!query.trim()) return;

		const cleanQuery = query.replace(/--.*$/gm, '').replace(/\/\*[\s\S]*?\*\//g, '');

		const destructiveKeywords =
			/\b(INSERT|UPDATE|DELETE|DROP|TRUNCATE|ALTER|CREATE|RENAME|GRANT|REVOKE)\b/i;
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
		typedConfirmation = ''; // Reset for the next step
	}

	function confirmRoot() {
		if (typedConfirmation !== dbName) return;
		showRootModal = false;
		executeSQL();
	}

	async function handleBackup(format: string = 'sql') {
		backupLoading = true;
		showExportDropdown = false;
		try {
			const res = await axios.get(`http://127.0.0.1:8000/db/backup?format=${format}`, {
				responseType: 'blob'
			});

			const extensions: any = {
				sql: '.sql',
				json: '.json',
				dbml: '.dbml',
				csv: '.zip',
				excel: '.xlsx'
			};
			const mimeTypes: any = {
				sql: 'application/sql',
				json: 'application/json',
				dbml: 'text/plain',
				csv: 'application/zip',
				excel: 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
			};

			const ext = extensions[format] || '.sql';
			const mime = mimeTypes[format] || 'application/sql';
			const defaultName = `backup_${new Date().toISOString().split('T')[0]}${ext}`;
			let finalName = defaultName;

			// Try to extract filename from Content-Disposition header if available
			const contentDisp = res.headers['content-disposition'];
			if (contentDisp && contentDisp.includes('filename=')) {
				finalName = contentDisp.split('filename=')[1].split(';')[0];
			}

			const blobContent = res.data;

			// Use File System Access API if available for "Save As" experience
			if ('showSaveFilePicker' in window) {
				try {
					const handle = await (window as any).showSaveFilePicker({
						suggestedName: finalName,
						types: [
							{
								description: `${format.toUpperCase()} Export File`,
								accept: { [mime]: [ext] }
							}
						]
					});
					finalName = handle.name;
					const writable = await handle.createWritable();
					await writable.write(blobContent);
					await writable.close();
				} catch (err: any) {
					if (err.name === 'AbortError') return;
					console.warn('Picker failed or cancelled, using fallback', err);

					const url = window.URL.createObjectURL(blobContent);
					const link = document.createElement('a');
					link.href = url;
					link.setAttribute('download', finalName);
					document.body.appendChild(link);
					link.click();
					document.body.removeChild(link);
				}
			} else {
				// Standard fallback download
				const url = window.URL.createObjectURL(blobContent);
				const link = document.createElement('a');
				link.href = url;
				link.setAttribute('download', finalName);
				document.body.appendChild(link);
				link.click();
				document.body.removeChild(link);
			}

			// Show success in Execution Results
			queryResult = {
				success: true,
				affected_rows: `SNAPSHOT '${finalName.toUpperCase()}' EXPORTED SUCCESSFULLY`
			};
		} catch (err: any) {
			console.error('Backup failed:', err);
		} finally {
			backupLoading = false;
		}
	}




	async function handleRestore() {
		if (!restoreFile) return;
		restoreLoading = true;
		showRestoreModal = false;
		try {
			const formData = new FormData();
			formData.append('file', restoreFile);
			// Pass the clean parameter to the API
			const res = await axios.post(
				`http://127.0.0.1:8000/db/restore?clean=${restoreClean}`,
				formData
			);
			if (res.data.success) {
				const refreshRes = await axios.get('http://127.0.0.1:8000/db/tables');
				tables = Array.isArray(refreshRes.data) ? refreshRes.data : [];
				queryResult = { success: true, affected_rows: 'Database Restored Successfully' };
			} else {
				queryResult = { success: false, error: res.data.error };
			}
		} catch (err: any) {
			queryResult = { success: false, error: err.message };
		} finally {
			restoreLoading = false;
			restoreFile = null;
			restoreClean = false; // Reset for next time
		}
	}

	async function executeSQL() {
		queryLoading = true;
		queryTrace = null;
		try {
			// Trigger Impact Trace in parallel
			axios
				.post('http://127.0.0.1:8000/system/trace-query', { query })
				.then((t) => (queryTrace = t.data))
				.catch((e) => console.error('Trace failed', e));

			const res = await axios.post('http://127.0.0.1:8000/db/query', { query });
			queryResult = res.data;

			// Auto refresh schemas
			const tableRes = await axios.get('http://127.0.0.1:8000/db/tables');
			tables = Array.isArray(tableRes.data) ? tableRes.data : [];
		} catch (err: any) {
			queryResult = { success: false, error: err.message };
		} finally {
			queryLoading = false;
		}
	}

	onMount(async () => {
		try {
			const res = await axios.get('http://127.0.0.1:8000/db/tables');
			tables = Array.isArray(res.data) ? res.data : [];
		} catch (err) {
			console.error(err);
		} finally {
			loading = false;
		}
	});

	function clickOutside(node: any, callback: () => void) {
		const handleClick = (e: MouseEvent) => {
			if (node && !node.contains(e.target as Node) && !e.defaultPrevented) {
				callback();
			}
		};
		document.addEventListener('click', handleClick, true);
		return {
			destroy() {
				document.removeEventListener('click', handleClick, true);
			}
		};
	}
</script>


<div class="flex flex-col gap-10 pb-20">
	<header class="flex flex-col gap-3">
		<div class="flex items-center gap-4">
			<a
				href="/"
				class="w-10 h-10 rounded-xl bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 flex items-center justify-center text-slate-400 dark:text-slate-500 hover:text-emerald-600 dark:hover:text-emerald-400 hover:border-emerald-200 dark:hover:border-emerald-800 transition-all shadow-sm"
				aria-label="Back to dashboard"
			>
				<svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"
					><path
						stroke-linecap="round"
						stroke-linejoin="round"
						stroke-width="2.5"
						d="M15 19l-7-7 7-7"
					/></svg
				>
			</a>
			<h1
				class="text-5xl font-black text-slate-900 dark:text-white tracking-tighter italic uppercase leading-none"
			>
				Database Schema<span class="text-emerald-500 uppercase italic">.</span>
			</h1>
		</div>
		<p class="text-slate-500 dark:text-slate-400 font-bold uppercase tracking-widest text-xs ml-14">
			Exploring all schema tables and metadata in PostgreSQL
		</p>
	</header>

	<!-- SQL RUNNER SECTION -->
	<div
		class="bg-white dark:bg-slate-900 rounded-[2.5rem] p-8 border border-slate-200 dark:border-slate-800 shadow-xl flex flex-col gap-6 relative w-full max-w-full"
	>

		<div class="flex items-center justify-between">
			<h2
				class="text-sm font-black text-slate-900 dark:text-slate-100 uppercase tracking-widest italic flex items-center gap-2"
			>
				<span class="text-emerald-500">ROOT</span> Raw SQL Editor
			</h2>
			{#if queryLoading || backupLoading || restoreLoading}
				<div
					class="flex items-center gap-3 text-[10px] font-bold text-emerald-500 uppercase tracking-widest"
				>
					<div
						class="w-4 h-4 border-2 border-emerald-500 border-t-transparent rounded-full animate-spin"
					></div>
					Processing Payload...
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

			<!-- Schema naming hint & Portability tools -->
			<div class="grid grid-cols-1 md:grid-cols-2 gap-4">
				<div
					class="bg-amber-50 dark:bg-amber-950/30 border border-amber-200 dark:border-amber-800/50 rounded-xl px-4 py-3 flex items-start gap-3"
				>
					<span class="text-amber-500 text-sm mt-0.5 shrink-0">⚠</span>
					<div class="flex flex-col gap-1">
						<p
							class="text-[11px] font-black text-amber-700 dark:text-amber-400 uppercase tracking-widest"
						>
							Schema-Qualified Names Required
						</p>
						<p
							class="text-[11px] font-bold text-amber-600/80 dark:text-amber-500/80 leading-relaxed"
						>
							PostgreSQL resolves unqualified names against <code
								class="bg-amber-100 dark:bg-amber-900/50 px-1 rounded font-mono">public</code
							>.
						</p>
					</div>
				</div>

				<div
					class="bg-emerald-500/5 dark:bg-emerald-500/10 border border-emerald-500/20 rounded-xl p-4 flex flex-col gap-3"
				>
					<div class="flex items-center justify-between">
						<p
							class="text-[11px] font-black text-emerald-600 dark:text-emerald-400 uppercase tracking-[0.2em] italic"
						>
							⚡ Database Portability
						</p>
						<div class="flex gap-2 items-center">
							<div class="relative">
								<button
									onclick={() => (showExportDropdown = !showExportDropdown)}
									disabled={backupLoading}
									class="bg-emerald-500/10 hover:bg-emerald-500 text-emerald-600 dark:text-emerald-400 hover:text-white px-3 py-1.5 rounded-lg border border-emerald-500/20 text-[10px] font-black uppercase tracking-widest transition-all active:scale-95 flex items-center gap-1.5"
								>
									Export ▾
								</button>
								{#if showExportDropdown}
									<div
										class="absolute right-0 top-full mt-2 w-32 bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-xl shadow-xl z-50 py-1.5 flex flex-col overflow-hidden animate-in fade-in slide-in-from-top-2 duration-200"
										use:clickOutside={() => (showExportDropdown = false)}
									>

										<button onclick={() => handleBackup('sql')} class="px-4 py-2 text-left text-[10px] font-black uppercase tracking-widest text-slate-600 dark:text-slate-400 hover:bg-emerald-500 hover:text-white transition-colors">SQL</button>
										<button onclick={() => handleBackup('json')} class="px-4 py-2 text-left text-[10px] font-black uppercase tracking-widest text-slate-600 dark:text-slate-400 hover:bg-emerald-500 hover:text-white transition-colors">JSON</button>
										<button onclick={() => handleBackup('dbml')} class="px-4 py-2 text-left text-[10px] font-black uppercase tracking-widest text-slate-600 dark:text-slate-400 hover:bg-emerald-500 hover:text-white transition-colors">DBML</button>
										<button onclick={() => handleBackup('csv')} class="px-4 py-2 text-left text-[10px] font-black uppercase tracking-widest text-slate-600 dark:text-slate-400 hover:bg-emerald-500 hover:text-white transition-colors">CSV (Zip)</button>
										<button onclick={() => handleBackup('excel')} class="px-4 py-2 text-left text-[10px] font-black uppercase tracking-widest text-slate-600 dark:text-slate-400 hover:bg-emerald-500 hover:text-white transition-colors">Excel</button>
									</div>
								{/if}
							</div>

							<label
								class="bg-blue-500/10 hover:bg-blue-500 text-blue-600 dark:text-blue-400 hover:text-white px-3 py-1.5 rounded-lg border border-blue-500/20 text-[10px] font-black uppercase tracking-widest transition-all active:scale-95 cursor-pointer"
							>
								Restore Payload
								<input
									type="file"
									accept=".sql,.dbml"
									class="hidden"
									onchange={(e) => {
										restoreFile = e.currentTarget.files?.[0] || null;
										if (restoreFile) showRestoreModal = true;
									}}
								/>

							</label>
						</div>
					</div>
				</div>
			</div>

			<div class="flex justify-between items-center">
				<span
					class="text-[10px] font-bold text-slate-400 dark:text-slate-500 uppercase tracking-widest"
					><kbd class="bg-slate-100 dark:bg-slate-800 px-1.5 py-0.5 rounded">CMD</kbd> +
					<kbd class="bg-slate-100 dark:bg-slate-800 px-1.5 py-0.5 rounded">ENTER</kbd> TO RUN</span
				>
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
			<div
				class="mt-4 pt-6 border-t border-slate-100 dark:border-slate-800 flex flex-col gap-4 overflow-hidden"
			>
				<div class="flex items-center justify-between">
					<h3 class="text-xs font-black text-slate-500 uppercase tracking-widest leading-none">
						Execution Result
					</h3>
					<button
						onclick={() => {
							queryResult = null;
							queryTrace = null;
						}}
						class="text-[10px] text-slate-400 hover:text-rose-500 font-bold uppercase tracking-widest transition-colors"
						>Clear</button
					>
				</div>

				{#if !queryResult.success}
					<div
						class="bg-rose-500/10 border border-rose-500/30 text-rose-500 dark:text-rose-400 p-4 rounded-xl text-sm font-bold uppercase tracking-widest font-mono break-all leading-relaxed whitespace-pre-wrap"
					>
						{queryResult.error}
					</div>
				{:else}
					<!-- New Trace Summary Section -->
					{#if queryTrace}
						<div
							class="p-4 rounded-2xl bg-indigo-500/5 border border-indigo-500/20 shadow-sm animate-in fade-in slide-in-from-top-2 duration-300"
						>
							<div
								class="flex items-center justify-between mb-3 border-b border-indigo-500/10 pb-2"
							>
								<div class="flex items-center gap-2">
									<span
										class="text-[10px] font-black text-indigo-500 uppercase tracking-[0.2em] italic"
										>⚡ Query Trace Summary</span
									>
									<a
										href="/relations"
										class="text-[9px] font-black px-2 py-0.5 bg-indigo-500/10 text-indigo-500 rounded border border-indigo-500/20 hover:bg-indigo-500 hover:text-white transition-all uppercase tracking-widest"
										>Jump to Graph</a
									>
								</div>
								<span
									class="px-2 py-0.5 rounded text-[9px] font-black uppercase tracking-widest border
									{queryTrace.severity === 'HIGH'
										? 'bg-rose-500 text-white border-rose-600 animate-pulse'
										: queryTrace.severity === 'MEDIUM'
											? 'bg-orange-500 text-white border-orange-600'
											: 'bg-emerald-500 text-white border-emerald-600'}"
								>
									{queryTrace.severity} RisK
								</span>
							</div>

							<div class="grid grid-cols-1 md:grid-cols-2 gap-4">
								<div class="space-y-3">
									<div>
										<div class="text-[9px] font-bold text-slate-400 uppercase tracking-widest mb-1">
											Impacted Containers
										</div>
										<div class="flex flex-wrap gap-1">
											{#each queryTrace.containers as c}
												<span
													class="text-[9px] px-2 py-0.5 bg-sky-500/10 text-sky-500 rounded border border-sky-500/20 font-bold uppercase"
													>{c}</span
												>
											{:else}
												<span class="text-[9px] font-bold text-slate-400 italic"
													>No container fallout detected</span
												>
											{/each}
										</div>
									</div>
									<div>
										<div class="text-[9px] font-bold text-slate-400 uppercase tracking-widest mb-1">
											Downstream Tables
										</div>
										<div class="flex flex-wrap gap-1">
											{#each queryTrace.dependent_tables as t}
												<span
													class="text-[9px] px-2 py-0.5 bg-rose-500/10 text-rose-500 rounded border border-rose-500/20 font-bold uppercase"
													>{t.split('.').pop()}</span
												>
											{:else}
												<span class="text-[9px] font-bold text-slate-400 italic"
													>No structural dependents</span
												>
											{/each}
										</div>
									</div>
								</div>
								<div
									class="bg-indigo-500/10 rounded-xl p-3 border border-indigo-500/10 flex flex-col justify-center"
								>
									<p
										class="text-[11px] font-bold text-indigo-700 dark:text-indigo-300 italic leading-relaxed"
									>
										{queryTrace.summary}
									</p>
									<p
										class="text-[9px] text-indigo-500 font-bold mt-2 uppercase tracking-widest opacity-60"
									>
										Result set contains {queryResult.data?.length || 0} rows
									</p>
								</div>
							</div>
						</div>
					{/if}

					{#if queryResult.columns && queryResult.data}
						{#if queryResult.is_truncated}
							<div
								class="bg-amber-500/10 border border-amber-500/30 text-amber-600 dark:text-amber-400 p-4 rounded-xl text-[10px] font-black uppercase tracking-widest flex items-center gap-3"
							>
								<span class="text-lg">🛑</span>
								<span>Result Set Truncated at 1,000 Rows for Performance Safety.</span>
							</div>
						{/if}

						<div
							class="bg-slate-50 dark:bg-slate-950 rounded-2xl border border-slate-200 dark:border-slate-800 overflow-x-auto custom-scrollbar shadow-inner"
						>
							<table class="w-full text-left border-collapse min-w-max">
								<thead>
									<tr>
										{#each queryResult.columns as col}
											<th
												class="p-4 text-[10px] bg-white dark:bg-slate-900 font-black text-slate-500 uppercase tracking-widest border-b border-r border-slate-200 dark:border-slate-800 whitespace-nowrap"
												>{col}</th
											>
										{/each}
									</tr>
								</thead>
								<tbody>
									{#each queryResult.data as row}
										<tr
											class="hover:bg-blue-50/50 dark:hover:bg-slate-900/50 transition-colors group"
										>
											{#each queryResult.columns as col}
												<td
													class="p-4 text-xs font-mono font-bold text-slate-600 dark:text-slate-300 border-b border-r border-slate-200 dark:border-slate-800 group-hover:border-blue-100 dark:group-hover:border-slate-700 whitespace-nowrap"
													>{row[col] === null ? 'NULL' : String(row[col])}</td
												>
											{/each}
										</tr>
									{/each}
									{#if queryResult.data.length === 0}
										<tr>
											<td
												colspan={queryResult.columns.length}
												class="p-8 text-center text-xs font-bold text-slate-400 uppercase tracking-widest"
												>0 Rows Returned</td
											>
										</tr>
									{/if}
								</tbody>
							</table>
						</div>
					{:else}
						<div
							class="bg-emerald-500/10 border border-emerald-500/30 text-emerald-600 dark:text-emerald-400 p-4 rounded-xl text-sm font-bold uppercase tracking-widest font-mono"
						>
							⚡ {queryResult.affected_rows}
						</div>
					{/if}
				{/if}
			</div>
		{/if}
	</div>

	{#if loading}
		<div
			class="flex items-center gap-4 text-emerald-600 dark:text-emerald-400 font-black animate-pulse uppercase tracking-wider text-sm ml-14"
		>
			<div
				class="w-6 h-6 border-4 border-current border-t-transparent rounded-full animate-spin"
			></div>
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
						<div
							class="w-12 h-12 bg-emerald-50 dark:bg-emerald-900/20 text-emerald-600 dark:text-emerald-400 rounded-2xl flex items-center justify-center text-xl shadow-inner border border-emerald-100 dark:border-emerald-900/30"
						>
							<svg class="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24"
								><path
									stroke-linecap="round"
									stroke-linejoin="round"
									stroke-width="2"
									d="M3 10h18M3 14h18m-9-4v8m-7 0h14a2 2 0 002-2V8a2 2 0 00-2-2H5a2 2 0 00-2 2v8a2 2 0 002 2z"
								/></svg
							>
						</div>
						<div class="flex items-center gap-2">
							<span
								class="text-[10px] font-black px-2.5 py-1 rounded-lg uppercase tracking-widest leading-none {isPublic
									? 'bg-emerald-50 dark:bg-emerald-900/20 text-emerald-600 dark:text-emerald-400'
									: 'bg-amber-50 dark:bg-amber-900/20 text-amber-600 dark:text-amber-400'}"
							>
								{schema}
							</span>
							<div
								class="w-10 h-10 rounded-xl bg-slate-50 dark:bg-slate-950 border border-slate-100 dark:border-slate-800 flex items-center justify-center text-slate-300 dark:text-slate-700 group-hover:text-emerald-500 transition-colors"
							>
								<svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"
									><path
										stroke-linecap="round"
										stroke-linejoin="round"
										stroke-width="2.5"
										d="M9 5l7 7-7 7"
									/></svg
								>
							</div>
						</div>
					</div>

					<div>
						<h3
							class="text-2xl font-black text-slate-900 dark:text-white group-hover:text-emerald-600 dark:group-hover:text-emerald-400 transition-colors tracking-tight uppercase italic leading-none"
						>
							{tableName}
						</h3>
						<div class="flex items-center gap-2 mt-3">
							<span class="w-1.5 h-1.5 rounded-full bg-emerald-500 group-hover:animate-ping"></span>
							<span
								class="text-[10px] font-black text-slate-400 dark:text-slate-500 uppercase tracking-widest leading-none"
								>Table</span
							>
						</div>
					</div>

					<div
						class="pt-4 border-t border-slate-50 dark:border-slate-800 mt-auto flex flex-col gap-1.5"
					>
						<span
							class="text-[9px] font-black text-slate-400 dark:text-slate-500 uppercase tracking-widest leading-none"
							>SQL Ref</span
						>
						<code
							class="text-[11px] font-mono font-bold {isPublic
								? 'text-emerald-600 dark:text-emerald-400'
								: 'text-amber-600 dark:text-amber-400'} leading-none">{sqlRef}</code
						>
					</div>
				</a>
			{:else}
				<div
					class="col-span-full py-20 flex flex-col items-center gap-6 text-slate-300 dark:text-slate-700"
				>
					<div
						class="text-8xl opacity-10 italic font-black uppercase tracking-tighter leading-none"
					>
						Void
					</div>
					<p class="text-sm font-bold uppercase tracking-[0.3em]">No tables found</p>
				</div>
			{/each}
		</div>
	{/if}
</div>

<!-- FIRST CONFIRMATION MODAL -->
{#if showConfirmModal}
	<div
		class="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-900/80 backdrop-blur-sm"
	>
		<div
			class="bg-white dark:bg-slate-950 border border-amber-500/30 shadow-2xl rounded-3xl p-8 max-w-sm w-full flex flex-col gap-6 animate-in slide-in-from-bottom-8 duration-200"
		>
			<div
				class="w-16 h-16 rounded-full bg-amber-500/10 text-amber-500 flex items-center justify-center text-3xl mx-auto shadow-inner shadow-amber-500/20"
			>
				⚠️
			</div>
			<div class="text-center space-y-2">
				<h3
					class="text-xl font-black text-slate-900 dark:text-white uppercase tracking-tighter italic"
				>
					Destructive Action Detected
				</h3>
				<p class="text-xs font-bold text-slate-500 uppercase tracking-widest leading-relaxed">
					Are you sure you want to run this modifying SQL payload against the root database?
				</p>
			</div>
			<div class="flex gap-3">
				<button
					onclick={() => (showConfirmModal = false)}
					class="flex-1 px-4 py-3 rounded-xl bg-slate-100 dark:bg-slate-800 text-slate-500 font-bold uppercase tracking-widest text-xs hover:bg-slate-200 dark:hover:bg-slate-700 transition-colors"
					>Cancel</button
				>
				<button
					onclick={confirmFirst}
					class="flex-1 px-4 py-3 rounded-xl bg-amber-500 text-white font-black uppercase tracking-widest text-xs hover:bg-amber-600 transition-colors shadow-lg shadow-amber-500/20"
					>Acknowledge</button
				>
			</div>
		</div>
	</div>
{/if}

<!-- ROOT DOUBLE CONFIRMATION MODAL -->
{#if showRootModal}
	<div
		class="fixed inset-0 z-50 flex items-center justify-center p-4 bg-rose-950/90 backdrop-blur-md"
		role="presentation"
		onkeydown={(e) => { if (e.key === 'Escape') showRootModal = false; }}
	>
		<div
			class="bg-rose-950 border-2 border-rose-500 shadow-2xl shadow-rose-900/50 rounded-3xl p-8 max-w-sm w-full flex flex-col gap-6 animate-in zoom-in-95 duration-200"
			role="dialog"
			aria-modal="true"
			aria-label="Root Mutation Verification"
			tabindex="-1"
			onclick={(e) => e.stopPropagation()}
		>
			<div
				class="w-16 h-16 rounded-full bg-rose-500/20 text-rose-500 flex items-center justify-center text-3xl mx-auto animate-pulse"
			>
				☢️
			</div>
			<div class="text-center space-y-3">
				<h3 class="text-2xl font-black text-white uppercase tracking-tighter italic">
					FINAL WARNING
				</h3>
				<p class="text-xs font-bold text-rose-300 uppercase tracking-widest leading-relaxed">
					This action provides absolute mutability to root schemas and data arrays. It CANNOT be
					undone.
				</p>
			</div>

			<div class="flex flex-col gap-2">
				<p class="text-[10px] font-black text-rose-400/70 uppercase tracking-widest text-center">
					Please type <span class="text-white select-all">{dbName}</span> to confirm.
				</p>
				<input
					bind:value={typedConfirmation}
					type="text"
					placeholder={dbName}
					onpaste={(e) => e.preventDefault()}
					oncopy={(e) => e.preventDefault()}
					onclick={(e) => e.stopPropagation()}
					class="w-full px-4 py-3 rounded-xl bg-black/20 border-2 {typedConfirmation === dbName ? 'border-emerald-500/50' : 'border-rose-500/30'} text-white text-center font-bold uppercase tracking-widest text-sm focus:outline-none focus:border-rose-500/60 transition-all placeholder:opacity-20"
				/>
				{#if typedConfirmation && typedConfirmation !== dbName}
					<p class="text-[9px] font-black text-rose-500 uppercase tracking-[0.2em] text-center animate-pulse">
						Verification Mismatch
					</p>
				{/if}
			</div>

			<div class="flex gap-3">
				<button
					onclick={() => (showRootModal = false)}
					class="flex-1 px-4 py-4 rounded-xl border border-rose-500/30 text-rose-300 font-bold uppercase tracking-widest text-xs hover:bg-rose-500/10 transition-colors"
					>Abort</button
				>
				<button
					onclick={confirmRoot}
					disabled={typedConfirmation !== dbName}
					class="flex-1 px-4 py-4 rounded-xl {typedConfirmation === dbName ? 'bg-emerald-600 hover:bg-emerald-500 shadow-emerald-500/40' : 'bg-rose-600 opacity-50 cursor-not-allowed'} text-white font-black uppercase tracking-widest text-xs transition-all shadow-lg"
					>Proceed</button
				>
			</div>
		</div>
	</div>
{/if}

<!-- RESTORE CONFIGURATION MODAL -->
{#if showRestoreModal}
	<div
		class="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-900/80 backdrop-blur-sm"
	>
		<div
			class="bg-white dark:bg-slate-950 border border-blue-500/30 shadow-2xl rounded-[2.5rem] p-10 max-w-md w-full flex flex-col gap-8 animate-in slide-in-from-bottom-12 duration-300"
		>
			<div
				class="w-20 h-20 rounded-3xl bg-blue-500/10 text-blue-500 flex items-center justify-center text-4xl mx-auto shadow-inner shadow-blue-500/20"
			>
				📥
			</div>

			<div class="text-center space-y-4">
				<h3
					class="text-3xl font-black text-slate-900 dark:text-white uppercase tracking-tighter italic"
				>
					Restore Payload
				</h3>
				<div class="flex flex-col gap-1 items-center">
					<p class="text-xs font-bold text-slate-500 uppercase tracking-[0.2em] leading-relaxed">
						Ready to inject <span class="text-blue-500 italic">{restoreFile?.name}</span>
					</p>
					<span class="px-2 py-0.5 bg-blue-500 text-white rounded text-[9px] font-black uppercase tracking-[0.2em]">
						Detected: {restoreFile?.name.split('.').pop()?.toUpperCase() || 'SQL'}
					</span>
				</div>
			</div>

			<div
				class="bg-slate-50 dark:bg-slate-900/50 p-6 rounded-3xl border border-slate-100 dark:border-slate-800 flex flex-col gap-4"
			>
				<label class="flex items-center gap-4 cursor-pointer group">
					<input
						type="checkbox"
						bind:checked={restoreClean}
						class="w-6 h-6 rounded-lg border-2 border-slate-300 dark:border-slate-700 bg-transparent text-blue-500 focus:ring-blue-500 transition-all cursor-pointer"
					/>
					<div class="flex flex-col">
						<span
							class="text-xs font-black text-slate-700 dark:text-slate-200 uppercase tracking-widest group-hover:text-blue-500 transition-colors"
							>Wipe and Overwrite</span
						>
						<span class="text-[10px] font-bold text-slate-400 dark:text-slate-500 leading-tight"
							>Clear existing schema tables before restoration.</span
						>
					</div>
				</label>

				{#if restoreClean}
					<div
						class="bg-rose-500/10 border border-rose-500/20 p-3 rounded-xl flex items-center gap-3 animate-in fade-in zoom-in-95"
					>
						<span class="text-lg">🔥</span>
						<p
							class="text-[10px] font-black text-rose-600 dark:text-rose-400 uppercase tracking-widest leading-tight"
						>
							Caution: All current tables in 'public' schema will be PERMANENTLY deleted.
						</p>
					</div>
				{/if}
			</div>

			<div class="flex gap-4">
				<button
					onclick={() => {
						showRestoreModal = false;
						restoreFile = null;
						restoreClean = false;
					}}
					class="flex-1 px-6 py-4 rounded-2xl bg-slate-100 dark:bg-slate-800 text-slate-500 font-bold uppercase tracking-widest text-[10px] hover:bg-slate-200 dark:hover:bg-slate-700 transition-colors"
				>
					Abort
				</button>
				<button
					onclick={handleRestore}
					class="flex-1 px-6 py-4 rounded-2xl bg-blue-500 text-white font-black uppercase tracking-widest text-[10px] hover:bg-blue-600 transition-colors shadow-lg shadow-blue-500/20 active:scale-95"
				>
					Start Restore
				</button>
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
