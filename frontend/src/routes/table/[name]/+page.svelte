<script lang="ts">
	import { onMount, tick } from "svelte";
	import axios from "axios";
	import { page } from "$app/state";

	let tableName = $derived(page.url.pathname.split('/').pop() || "");
	
	interface TableColumn {
		name: string;
		type: string;
		nullable: boolean;
		default: string | null;
		is_primary: boolean;
		foreign_key: string | null;
	}

	// State
	let activeTab = $state<"data" | "structure">("data");
	let structure = $state<TableColumn[]>([]);
	let primaryKeys = $derived(structure.filter(c => c.is_primary).map(c => c.name));
	
	let data = $state<any[]>([]);
	let totalRows = $state(0);
	let loading = $state(true);
	let errorMsg = $state<string | null>(null);

	// Pagination & Sorting
	let pageSize = $state(20);
	let offset = $state(0);
	let sortCol = $state<string | null>(null);
	let sortDir = $state<"asc" | "desc">("asc");
	let currentPage = $derived(Math.floor(offset / pageSize) + 1);
	let totalPages = $derived(Math.ceil(totalRows / pageSize) || 1);

	// Mutability Modals
	let isEditModalOpen = $state(false);
	let editMode = $state<"insert" | "update">("insert");
	let editingRow = $state<any>({});
	let originalEditingPks = $state<any>({});
	
	let isDeleteModalOpen = $state(false);
	let rowToDelete = $state<any>(null);
	let processingAction = $state(false);

	async function fetchStructure() {
		try {
			const res = await axios.get(`http://127.0.0.1:8000/db/table/${tableName}/structure`);
			if (res.data.success) {
				structure = res.data.columns;
			}
		} catch (err) {
			console.error("Failed to fetch structure", err);
		}
	}

	async function fetchData() {
		loading = true;
		try {
			let url = `http://127.0.0.1:8000/db/table/${tableName}?limit=${pageSize}&offset=${offset}`;
			if (sortCol) url += `&sort_col=${sortCol}&sort_dir=${sortDir}`;
			
			const res = await axios.get(url);
			if (res.data.error) {
				errorMsg = res.data.error;
			} else {
				data = res.data.data;
				totalRows = res.data.total_rows;
			}
		} catch (err) {
			console.error(err);
			errorMsg = "Failed to fetch data";
		} finally {
			loading = false;
		}
	}

	async function reload() {
		await fetchStructure();
		await fetchData();
	}

	onMount(() => {
		reload();
	});

	// Sorting Click Handler
	function toggleSort(colName: string) {
		if (sortCol === colName) {
			sortDir = sortDir === "asc" ? "desc" : "asc";
		} else {
			sortCol = colName;
			sortDir = "asc";
		}
		offset = 0; // reset to page 1
		fetchData();
	}

	function nextPage() {
		if (currentPage < totalPages) {
			offset += pageSize;
			fetchData();
		}
	}

	function prevPage() {
		if (offset > 0) {
			offset -= pageSize;
			fetchData();
		}
	}

	// Actions
	function openInsertModal() {
		editMode = "insert";
		let blankRow: any = {};
		structure.forEach(c => blankRow[c.name] = "");
		editingRow = blankRow;
		isEditModalOpen = true;
	}

	function openUpdateModal(row: any) {
		if (primaryKeys.length === 0) {
			alert("Cannot update a row in a table lacking Primary Keys. Safety abort.");
			return;
		}
		editMode = "update";
		editingRow = { ...row };
		originalEditingPks = {};
		primaryKeys.forEach(pk => originalEditingPks[pk] = row[pk]);
		isEditModalOpen = true;
	}

	function triggerDeleteRow(row: any) {
		if (primaryKeys.length === 0) {
			alert("Cannot target a specific row for deletion without Primary Keys. Safety abort.");
			return;
		}
		rowToDelete = row;
		isDeleteModalOpen = true;
	}

	async function saveRow() {
		processingAction = true;
		try {
			let res;
			if (editMode === "insert") {
				res = await axios.post(`http://127.0.0.1:8000/db/table/${tableName}/row`, {
					payload: editingRow
				});
			} else {
				res = await axios.put(`http://127.0.0.1:8000/db/table/${tableName}/row`, {
					primary_keys: originalEditingPks,
					payload: editingRow
				});
			}
			
			if (res.data.success) {
				isEditModalOpen = false;
				await fetchData();
			} else {
				alert("Transaction Failed: " + res.data.error);
			}
		} catch (err: any) {
			alert("System Error: " + (err.response?.data?.error || err.message));
			console.error(err);
		} finally {
			processingAction = false;
		}
	}

	async function confirmDelete() {
		processingAction = true;
		try {
			let pks: any = {};
			primaryKeys.forEach(pk => pks[pk] = rowToDelete[pk]);
			
			const res = await axios.delete(`http://127.0.0.1:8000/db/table/${tableName}/row`, {
				data: { primary_keys: pks }
			});
			
			if (res.data.success) {
				isDeleteModalOpen = false;
				rowToDelete = null;
				await fetchData();
			} else {
				alert("Delete Failed: " + res.data.error);
			}
		} catch (err: any) {
			alert("System Error: " + (err.response?.data?.error || err.message));
			console.error(err);
		} finally {
			processingAction = false;
		}
	}

	// Dynamic Input Mapper
	function getInputType(dbType: string) {
		const dt = dbType.toLowerCase();
		if (dt.includes("int") || dt.includes("serial") || dt.includes("numeric") || dt.includes("double")) return "number";
		if (dt.includes("time") || dt.includes("date")) return "datetime-local";
		if (dt.includes("bool")) return "checkbox";
		return "text";
	}

	// JSON Viewer
	let jsonViewerOpen = $state(false);
	let jsonViewerCol = $state("");
	let jsonViewerContent = $state<any>(null);
	let jsonCopied = $state(false);

	function isJsonValue(val: any): boolean {
		return val !== null && typeof val === 'object';
	}

	function openJsonViewer(colName: string, val: any) {
		jsonViewerCol = colName;
		jsonViewerContent = val;
		jsonViewerOpen = true;
		jsonCopied = false;
	}

	function copyJson() {
		navigator.clipboard.writeText(JSON.stringify(jsonViewerContent, null, 2));
		jsonCopied = true;
		setTimeout(() => jsonCopied = false, 2000);
	}

	function syntaxHighlight(json: string): string {
		return json
			.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;')
			.replace(/("(\\u[a-zA-Z0-9]{4}|\\[^u]|[^\\"])*"(\s*:)?|\b(true|false|null)\b|-?\d+(?:\.\d*)?(?:[eE][+\-]?\d+)?)/g, (match) => {
				let cls = 'text-blue-400'; // number
				if (/^"/.test(match)) {
					cls = /:$/.test(match) ? 'text-emerald-400' : 'text-amber-300'; // key vs string
				} else if (/true|false/.test(match)) {
					cls = 'text-purple-400';
				} else if (/null/.test(match)) {
					cls = 'text-slate-500';
				}
				return `<span class="${cls}">${match}</span>`;
			});
	}
</script>

<div class="flex flex-col gap-10 pb-20 relative">
	<header class="flex flex-col gap-4">
		<div class="flex items-center justify-between">
			<div class="flex items-center gap-4">
				<a href="/database" class="w-10 h-10 rounded-xl bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 flex items-center justify-center text-slate-400 dark:text-slate-500 hover:text-emerald-600 dark:hover:text-emerald-400 hover:border-emerald-200 dark:hover:border-emerald-800 transition-all shadow-sm" aria-label="Back to database">
					<svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2.5" d="M15 19l-7-7 7-7" /></svg>
				</a>
				<h1 class="text-5xl font-black text-slate-900 dark:text-white tracking-tighter italic uppercase leading-none">{tableName}<span class="text-emerald-500 uppercase italic">.</span></h1>
			</div>

			<!-- TAB NAV -->
			<div class="flex bg-slate-100 dark:bg-slate-900 p-1 rounded-xl border border-slate-200 dark:border-slate-800 shadow-inner">
				<button onclick={() => activeTab = 'data'} class="px-6 py-2.5 rounded-lg text-xs font-black uppercase tracking-widest transition-all {activeTab === 'data' ? 'bg-white dark:bg-slate-800 text-emerald-600 dark:text-emerald-400 shadow-sm' : 'text-slate-400 dark:text-slate-500 hover:text-slate-900 dark:hover:text-slate-300'}">📋 Data</button>
				<button onclick={() => activeTab = 'structure'} class="px-6 py-2.5 rounded-lg text-xs font-black uppercase tracking-widest transition-all {activeTab === 'structure' ? 'bg-white dark:bg-slate-800 text-purple-600 dark:text-purple-400 shadow-sm' : 'text-slate-400 dark:text-slate-500 hover:text-slate-900 dark:hover:text-slate-300'}">🏗️ Structure</button>
			</div>
		</div>
		
		<div class="flex items-center gap-3 ml-14">
			{#if primaryKeys.length > 0}
				<span class="px-2 py-1 bg-emerald-100 dark:bg-emerald-900/30 text-emerald-600 dark:text-emerald-400 rounded-md text-[10px] font-black uppercase tracking-widest border border-emerald-200 dark:border-emerald-800">PK: {primaryKeys.join(', ')}</span>
			{:else}
				<span class="px-2 py-1 bg-amber-100 dark:bg-amber-900/30 text-amber-600 dark:text-amber-400 rounded-md text-[10px] font-black uppercase tracking-widest border border-amber-200 dark:border-amber-800">⚠️ No Primary Key (Read-Only Safety Lock)</span>
			{/if}
		</div>
	</header>

	{#if errorMsg}
		<div class="p-6 rounded-2xl bg-rose-50 dark:bg-rose-900/10 border border-rose-200 dark:border-rose-800 text-rose-600 dark:text-rose-400 font-bold uppercase tracking-widest text-sm">
			{errorMsg}
		</div>
	{:else if loading && !data.length}
		<div class="flex flex-col items-center justify-center py-32 gap-6 text-emerald-600 dark:text-emerald-400">
			<div class="w-12 h-12 border-4 border-current border-t-transparent rounded-full animate-spin"></div>
			<span class="font-black animate-pulse uppercase tracking-[0.2em]">Synchronizing State...</span>
		</div>
	{:else}
		<!-- STRUCTURE TAB -->
		{#if activeTab === 'structure'}
			<div class="bg-white dark:bg-slate-900 rounded-[2rem] border border-slate-200/60 dark:border-slate-800 shadow-sm overflow-hidden flex flex-col animate-in fade-in slide-in-from-bottom-4 duration-300 w-full max-w-full">
				<div class="px-8 py-6 bg-slate-50 dark:bg-slate-950/50 border-b border-slate-100 dark:border-slate-800 flex items-center justify-between">
					<span class="text-xs font-black text-slate-400 dark:text-slate-500 uppercase tracking-widest italic leading-none">{structure.length} Columns Detected</span>
				</div>
				<div class="overflow-x-auto">
					<table class="w-full text-left border-collapse">
						<thead>
							<tr class="bg-slate-50/50 dark:bg-slate-950/30">
								<th class="px-8 py-4 text-[10px] font-black uppercase tracking-[0.2em] text-slate-400 dark:text-slate-500 border-b border-slate-100 dark:border-slate-800">Column Name</th>
								<th class="px-8 py-4 text-[10px] font-black uppercase tracking-[0.2em] text-slate-400 dark:text-slate-500 border-b border-slate-100 dark:border-slate-800">Data Type</th>
								<th class="px-8 py-4 text-[10px] font-black uppercase tracking-[0.2em] text-slate-400 dark:text-slate-500 border-b border-slate-100 dark:border-slate-800">Attributes</th>
								<th class="px-8 py-4 text-[10px] font-black uppercase tracking-[0.2em] text-slate-400 dark:text-slate-500 border-b border-slate-100 dark:border-slate-800">Nullable</th>
								<th class="px-8 py-4 text-[10px] font-black uppercase tracking-[0.2em] text-slate-400 dark:text-slate-500 border-b border-slate-100 dark:border-slate-800">Default Value</th>
							</tr>
						</thead>
						<tbody class="divide-y divide-slate-50 dark:divide-slate-800">
							{#each structure as col}
								<tr class="hover:bg-slate-50/30 dark:hover:bg-slate-800/20 transition-colors {col.is_primary ? 'bg-purple-50/30 dark:bg-purple-900/10' : ''}">
									<td class="px-8 py-4 text-sm font-bold text-slate-600 dark:text-slate-300 italic flex items-center gap-2">
										{#if col.is_primary}<span class="text-purple-500" title="Primary Key">🔑</span>{/if}
										{col.name}
									</td>
									<td class="px-8 py-4 text-xs font-mono font-bold text-blue-500 dark:text-blue-400 uppercase">{col.type}</td>
									<td class="px-8 py-4">
										{#if col.foreign_key}
											<div class="px-2 py-1 rounded-md bg-rose-50 dark:bg-rose-900/20 border border-rose-100 dark:border-rose-900 text-rose-600 dark:text-rose-400 text-[10px] font-black uppercase tracking-widest flex items-center gap-2 inline-flex" title="Foreign Key Mapping">
												<span>🔗</span>
												<span>{col.foreign_key}</span>
											</div>
										{/if}
									</td>
									<td class="px-8 py-4 text-[10px] uppercase font-black tracking-wider {col.nullable ? 'text-amber-500' : 'text-emerald-500'}">{col.nullable ? 'YES' : 'NO'}</td>
									<td class="px-8 py-4 text-xs font-mono text-slate-400">{col.default || 'NULL'}</td>
								</tr>
							{/each}
						</tbody>
					</table>
				</div>
			</div>
		{/if}

		<!-- DATA TAB -->
		{#if activeTab === 'data'}
			<div class="bg-white dark:bg-slate-900 rounded-[2rem] border border-slate-200/60 dark:border-slate-800 shadow-sm overflow-hidden flex flex-col animate-in fade-in slide-in-from-bottom-4 duration-300 relative w-full max-w-full">
				
				<!-- Header Actions & Paginator top -->
				<div class="px-6 py-4 bg-slate-50 dark:bg-slate-950/50 border-b border-slate-100 dark:border-slate-800 flex items-center justify-between">
					<button onclick={openInsertModal} class="flex items-center gap-2 px-4 py-2 bg-emerald-50 dark:bg-emerald-900/20 text-emerald-600 dark:text-emerald-400 hover:bg-emerald-500 hover:text-white border border-emerald-200 dark:border-emerald-800/40 rounded-xl text-xs font-black uppercase tracking-widest transition-all shadow-sm">
						<svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2.5" d="M12 4v16m8-8H4" /></svg>
						Insert Row
					</button>

					<div class="flex items-center gap-4 text-[10px] font-black uppercase tracking-widest text-slate-500 dark:text-slate-400">
						<span>Rows {offset + 1}-{Math.min(offset + pageSize, totalRows)} of {totalRows}</span>
						
						<div class="flex items-center gap-1">
							<button onclick={prevPage} disabled={currentPage === 1} aria-label="Previous Page" class="p-1.5 rounded-lg border border-slate-200 dark:border-slate-700 hover:bg-slate-200 dark:hover:bg-slate-800 disabled:opacity-30 transition-all"><svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2.5" d="M15 19l-7-7 7-7" /></svg></button>
							<span class="px-3">Pg {currentPage}</span>
							<button onclick={nextPage} disabled={currentPage === totalPages} aria-label="Next Page" class="p-1.5 rounded-lg border border-slate-200 dark:border-slate-700 hover:bg-slate-200 dark:hover:bg-slate-800 disabled:opacity-30 transition-all"><svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2.5" d="M9 5l7 7-7 7" /></svg></button>
						</div>
					</div>
				</div>

				<div class="overflow-x-auto custom-scrollbar">
					<table class="min-w-full text-left border-collapse whitespace-nowrap">
						<thead>
							<tr class="bg-slate-50/50 dark:bg-slate-950/30">
								<th class="px-6 py-4 w-1 border-b border-slate-100 dark:border-slate-800 sticky left-0 z-20 bg-slate-50 dark:bg-slate-950"></th>
								{#each structure as col}
									<th 
										onclick={() => toggleSort(col.name)}
										class="px-6 py-4 text-[10px] font-black uppercase tracking-[0.2em] text-slate-400 dark:text-slate-500 border-b border-slate-100 dark:border-slate-800 cursor-pointer hover:bg-slate-100 dark:hover:bg-slate-800 transition-colors select-none group"
									>
										<div class="flex items-center gap-2">
											{col.name}
											{#if sortCol === col.name}
												<span class="text-emerald-500">{sortDir === 'asc' ? '▲' : '▼'}</span>
											{:else}
												<span class="opacity-0 group-hover:opacity-30">↕</span>
											{/if}
										</div>
									</th>
								{/each}
							</tr>
						</thead>
						<tbody class="divide-y divide-slate-50 dark:divide-slate-800">
							{#each data as row}
								<tr class="hover:bg-slate-50/30 dark:hover:bg-slate-800/20 transition-colors group">
									<!-- Actions -->
									<td class="px-6 py-3 border-r border-slate-50 dark:border-slate-800/50 sticky left-0 z-20 bg-white dark:bg-slate-900 group-hover:bg-slate-50 dark:group-hover:bg-slate-800/80 transition-colors">
										<div class="flex items-center gap-2 opacity-20 group-hover:opacity-100 transition-opacity">
											<button onclick={() => openUpdateModal(row)} disabled={primaryKeys.length === 0} class="w-7 h-7 flex items-center justify-center rounded-lg bg-blue-50 dark:bg-blue-900/20 text-blue-600 dark:text-blue-400 hover:bg-blue-500 hover:text-white disabled:opacity-20 transition-colors" title="Edit Row">
												✏️
											</button>
											<button onclick={() => triggerDeleteRow(row)} disabled={primaryKeys.length === 0} class="w-7 h-7 flex items-center justify-center rounded-lg bg-rose-50 dark:bg-rose-900/20 text-rose-600 dark:text-rose-400 hover:bg-rose-500 hover:text-white disabled:opacity-20 transition-colors" title="Delete Row">
												🗑️
											</button>
										</div>
									</td>
									
									<!-- Data Cells -->
									{#each structure as col}
										<td class="px-6 py-3 text-sm {col.is_primary ? 'text-purple-600 dark:text-purple-400 font-bold' : 'text-slate-600 dark:text-slate-300'} max-w-sm truncate">
											{#if row[col.name] === null}
												<span class="text-slate-400 dark:text-slate-600 italic font-mono text-[10px] uppercase tracking-widest opacity-50">NULL</span>
											
											{:else if col.type.toLowerCase().includes('bool')}
												{#if row[col.name] === true || String(row[col.name]).toLowerCase() === 'true'}
													<span class="px-2 py-0.5 rounded-md bg-emerald-500/10 text-emerald-500 text-[10px] font-black uppercase tracking-widest border border-emerald-500/20">TRUE</span>
												{:else}
													<span class="px-2 py-0.5 rounded-md bg-rose-500/10 text-rose-500 text-[10px] font-black uppercase tracking-widest border border-rose-500/20">FALSE</span>
												{/if}

											{:else if col.type.toLowerCase().includes('timestamp') || col.type.toLowerCase().includes('date')}
												<span class="text-cyan-600 dark:text-cyan-400 font-mono text-[11px] font-bold" title={String(row[col.name])}>
													{new Date(row[col.name]).toLocaleDateString(undefined, { month: 'short', day: '2-digit', year: 'numeric' })}
												</span>

											{:else if col.type.toLowerCase().includes('uuid')}
												<span class="text-purple-500 dark:text-purple-400 font-mono text-[11px] font-bold tracking-tight lowercase">
													{String(row[col.name])}
												</span>

											{:else if col.type.toLowerCase().includes('bytea')}
												<span class="px-2 py-0.5 rounded-md bg-slate-100 dark:bg-slate-800 text-slate-400 dark:text-slate-500 text-[9px] font-black uppercase tracking-widest border border-slate-200 dark:border-slate-700 italic">
													&lt;binary&gt;
												</span>

											{:else if isJsonValue(row[col.name])}
												<button
													onclick={(e) => { e.preventDefault(); e.stopPropagation(); openJsonViewer(col.name, row[col.name]); }}
													class="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-lg bg-blue-50 dark:bg-blue-900/20 text-blue-600 dark:text-blue-400 border border-blue-100 dark:border-blue-800/50 hover:bg-blue-500 hover:text-white hover:border-transparent text-[10px] font-black uppercase tracking-widest transition-all not-italic"
												>
													<svg class="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2.5" d="M10 20l4-16m4 4l4 4-4 4M6 16l-4-4 4-4" /></svg>
													JSON
												</button>

											{:else if col.type.toLowerCase().includes('int') || col.type.toLowerCase().includes('numeric') || col.type.toLowerCase().includes('serial') || col.type.toLowerCase().includes('double')}
												<span class="text-blue-500 dark:text-blue-400 font-mono font-bold">{row[col.name]}</span>

											{:else}
												<span class="italic font-bold" title={String(row[col.name])}>{String(row[col.name])}</span>
											{/if}
										</td>
									{/each}
								</tr>
							{:else}
								<tr>
									<td colspan={structure.length + 1} class="px-8 py-20 text-center italic text-slate-300 dark:text-slate-700 font-black uppercase text-2xl opacity-20 tracking-tighter leading-none">
										Table is empty
									</td>
								</tr>
							{/each}
						</tbody>
					</table>
				</div>
			</div>
		{/if}
	{/if}
</div>

<!-- DATA EDITOR MODAL (INSERT / UPDATE) -->
{#if isEditModalOpen}
<div class="fixed inset-0 z-[100] flex items-center justify-end p-6 bg-slate-900/40 backdrop-blur-sm">
	<div class="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 shadow-2xl rounded-[2rem] p-8 w-[500px] h-full overflow-y-auto flex flex-col gap-8 animate-in slide-in-from-right-8 duration-300 custom-scrollbar">
		
		<div class="flex items-center justify-between">
			<div class="flex items-center gap-3">
				<div class="w-12 h-12 rounded-xl bg-emerald-50 dark:bg-emerald-900/20 text-emerald-600 dark:text-emerald-400 flex items-center justify-center text-xl shadow-inner border border-emerald-100 dark:border-emerald-800">
					{editMode === 'insert' ? '➕' : '✏️'}
				</div>
				<div>
					<h3 class="text-2xl font-black text-slate-900 dark:text-white uppercase tracking-tighter italic leading-none">{editMode === 'insert' ? 'Insert Row' : 'Update Row'}</h3>
					<p class="text-[10px] font-bold text-slate-400 uppercase tracking-widest mt-1">Table: {tableName}</p>
				</div>
			</div>
			
			<button onclick={() => isEditModalOpen = false} class="w-10 h-10 rounded-full bg-slate-100 dark:bg-slate-800 flex items-center justify-center hover:bg-slate-200 dark:hover:bg-slate-700 transition-colors text-slate-500">
				✕
			</button>
		</div>

		<div class="flex flex-col gap-6 flex-1">
			{#each structure as col}
				<div class="flex flex-col gap-2">
					<span class="text-[10px] font-black uppercase tracking-widest text-slate-500 flex items-center gap-2">
						{#if col.is_primary}<span class="text-purple-500">🔑</span>{/if}
						{col.name}
						<span class="text-[8px] opacity-50 ml-auto font-mono">{col.type}</span>
					</span>
					
					{#if getInputType(col.type) === 'checkbox'}
						<input type="checkbox" bind:checked={editingRow[col.name]} class="w-6 h-6 rounded-md accent-emerald-500 bg-slate-100 dark:bg-slate-950 border-slate-200 dark:border-slate-800" />
					{:else}
						<input 
							type={getInputType(col.type)} 
							bind:value={editingRow[col.name]} 
							placeholder={col.nullable ? 'NULL' : col.default || ''}
							class="px-4 py-3 rounded-xl bg-slate-50 dark:bg-slate-950 border border-slate-200 dark:border-slate-800 outline-none focus:border-emerald-500 focus:ring-1 focus:ring-emerald-500 transition-all font-mono text-sm text-slate-700 dark:text-slate-300 placeholder:italic w-full"
						/>
					{/if}
				</div>
			{/each}
		</div>

		<button 
			onclick={saveRow} 
			disabled={processingAction}
			class="w-full px-6 py-4 rounded-xl bg-emerald-500 hover:bg-emerald-600 text-white font-black uppercase tracking-widest text-xs transition-colors shadow-lg shadow-emerald-500/20 disabled:opacity-50 mt-auto flex items-center justify-center"
		>
			{#if processingAction}
				<div class="w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin"></div>
			{:else}
				Commit Transaction
			{/if}
		</button>
	</div>
</div>
{/if}

<!-- JSON VIEWER MODAL -->
{#if jsonViewerOpen}
<div 
	class="fixed inset-0 z-[150] flex items-center justify-center p-6 bg-slate-900/70 backdrop-blur-sm" 
	onclick={() => jsonViewerOpen = false} 
	onkeydown={(e) => e.key === 'Escape' && (jsonViewerOpen = false)}
	tabindex="-1"
	role="dialog" 
	aria-modal="true"
>
	<div 
		class="bg-slate-950 border border-slate-700 shadow-2xl rounded-[2rem] w-full max-w-2xl max-h-[80vh] flex flex-col animate-in zoom-in-95 duration-200" 
		onclick={(e) => e.stopPropagation()} 
		onkeydown={(e) => e.stopPropagation()}
		role="presentation"
		tabindex="-1"
	>
		<!-- Header -->
		<div class="flex items-center justify-between px-6 py-4 border-b border-slate-800 shrink-0">
			<div class="flex items-center gap-3">
				<div class="w-8 h-8 rounded-lg bg-blue-500/10 text-blue-400 flex items-center justify-center">
					<svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2.5" d="M10 20l4-16m4 4l4 4-4 4M6 16l-4-4 4-4" /></svg>
				</div>
				<div>
					<p class="text-[10px] font-black text-slate-500 uppercase tracking-widest">JSON Field</p>
					<p class="text-sm font-black text-white uppercase tracking-tight italic">{jsonViewerCol}</p>
				</div>
			</div>
			<div class="flex items-center gap-2">
				<button onclick={copyJson} class="flex items-center gap-2 px-3 py-1.5 rounded-lg text-[10px] font-black uppercase tracking-widest transition-all {jsonCopied ? 'bg-emerald-500 text-white' : 'bg-slate-800 text-slate-400 hover:bg-slate-700 hover:text-white'}">
					{#if jsonCopied}
						✓ Copied
					{:else}
						<svg class="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2.5" d="M8 16H6a2 2 0 01-2-2V6a2 2 0 012-2h8a2 2 0 012 2v2m-6 12h8a2 2 0 002-2v-8a2 2 0 00-2-2h-8a2 2 0 00-2 2v8a2 2 0 002 2z" /></svg>
						Copy
					{/if}
				</button>
				<button onclick={() => jsonViewerOpen = false} class="w-8 h-8 rounded-full bg-slate-800 flex items-center justify-center hover:bg-slate-700 transition-colors text-slate-400 hover:text-white text-sm">✕</button>
			</div>
		</div>
		<!-- Body -->
		<div class="overflow-y-auto custom-scrollbar p-6">
			<pre class="text-xs font-mono leading-relaxed whitespace-pre-wrap break-all">{@html syntaxHighlight(JSON.stringify(jsonViewerContent, null, 2))}</pre>
		</div>
	</div>
</div>
{/if}

<!-- DESTRUCTIVE CONFIRM MODAL (DELETE ROW) -->
{#if isDeleteModalOpen}
<div class="fixed inset-0 z-[200] flex items-center justify-center p-4 bg-rose-950/90 backdrop-blur-md">
	<div class="bg-white dark:bg-slate-950 border-2 border-rose-500 shadow-2xl rounded-3xl p-10 max-w-lg w-full flex flex-col gap-6 animate-in zoom-in-95 duration-200">
		<div class="w-20 h-20 rounded-full bg-rose-500/10 text-rose-500 flex items-center justify-center text-4xl mx-auto shadow-inner shadow-rose-500/20 border border-rose-500/30">⚠️</div>
		<div class="text-center space-y-3">
			<h3 class="text-2xl font-black text-rose-600 dark:text-rose-500 uppercase tracking-tighter italic">Destructive Action Alert <br /> DROP ROW</h3>
			<p class="text-xs font-bold text-slate-500 dark:text-slate-400 uppercase tracking-widest leading-relaxed">You are about to permanently delete a row from <span class="text-white font-black">{tableName}</span> bound by Primary Keys:</p>
			
			<div class="bg-rose-50 dark:bg-rose-950/50 p-4 rounded-xl border border-rose-100 dark:border-rose-900 mt-4 text-left">
				{#each primaryKeys as pk}
					<div class="flex justify-between items-center py-1 border-b border-rose-100/10 last:border-0 text-sm font-mono text-rose-400">
						<span class="font-bold opacity-70 uppercase text-[10px]">{pk} = </span>
						<span class="font-black italic text-rose-300">{rowToDelete[pk]}</span>
					</div>
				{/each}
			</div>
		</div>
		<div class="flex gap-4 mt-4">
			<button onclick={() => {isDeleteModalOpen = false; rowToDelete = null;}} disabled={processingAction} class="flex-1 px-4 py-4 rounded-xl bg-slate-100 dark:bg-slate-800 text-slate-500 font-black uppercase tracking-widest text-xs hover:bg-slate-200 dark:hover:bg-slate-700 transition-colors">Cancel</button>
			<button onclick={confirmDelete} disabled={processingAction} class="flex-1 px-4 py-4 rounded-xl bg-rose-600 text-white font-black uppercase tracking-widest text-xs hover:bg-rose-700 transition-colors shadow-xl shadow-rose-600/30">
				{#if processingAction}
					...
				{:else}
					Acknowledge & Delete
				{/if}
			</button>
		</div>
	</div>
</div>
{/if}

<style>
	.custom-scrollbar::-webkit-scrollbar { width: 6px; height: 6px; }
	.custom-scrollbar::-webkit-scrollbar-track { background: transparent; }
	.custom-scrollbar::-webkit-scrollbar-thumb { background: #334155; border-radius: 10px; }
	.custom-scrollbar::-webkit-scrollbar-thumb:hover { background: #475569; }
</style>