<script lang="ts">
	import { onMount } from "svelte";
	import axios from "axios";

	interface Container {
		id: string;
		name: string;
		image: string;
		status: string;
		ports: string;
		project?: string;
	}

	let containers = $state<Container[]>([]);
	let loading = $state(true);
	let loadingAction = $state<string | null>(null);
	let containerToDelete = $state<Container | null>(null);

	let groupedContainers = $derived.by(() => {
		const groups: Record<string, Container[]> = {};
		for (const c of containers) {
			const p = c.project || 'Standalone';
			if (!groups[p]) Object.assign(groups, { [p]: [] });
			groups[p].push(c);
		}
		return groups;
	});

	async function performAction(id: string, action: string) {
		loadingAction = id + '-' + action;
		try {
			await axios.post(`http://127.0.0.1:8000/containers/${id}/action`, { action });
			// Reload the list
			const res = await axios.get("http://127.0.0.1:8000/containers");
			containers = Array.isArray(res.data) ? res.data : [];
		} catch (err) {
			console.error("Action failed", err);
		} finally {
			loadingAction = null;
		}
	}

	onMount(async () => {
		try {
			const res = await axios.get("http://127.0.0.1:8000/containers");
			containers = Array.isArray(res.data) ? res.data : [];
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
			<a href="/" class="w-10 h-10 rounded-xl bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 flex items-center justify-center text-slate-400 dark:text-slate-500 hover:text-indigo-600 dark:hover:text-indigo-400 hover:border-indigo-200 dark:hover:border-indigo-800 transition-all shadow-sm" aria-label="Back to dashboard">
				<svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2.5" d="M15 19l-7-7 7-7" /></svg>
			</a>
			<h1 class="text-5xl font-black text-slate-900 dark:text-white tracking-tighter italic uppercase leading-none">Docker Nodes<span class="text-blue-600 uppercase italic">.</span></h1>
		</div>
		<p class="text-slate-500 dark:text-slate-400 font-bold uppercase tracking-widest text-xs ml-14">Comprehensive list of all running and stopped containers</p>
	</header>

	{#if loading}
		<div class="flex items-center gap-4 text-blue-600 dark:text-blue-400 font-black animate-pulse uppercase tracking-wider text-sm ml-14">
			<div class="w-6 h-6 border-4 border-current border-t-transparent rounded-full animate-spin"></div>
			Fetching Container State...
		</div>
	{:else}
		<div class="flex flex-col gap-12">
			{#each Object.entries(groupedContainers) as [project, pContainers]}
				<div class="flex flex-col gap-6">
					<div class="flex items-center gap-3">
						<h2 class="text-xl font-black text-slate-800 dark:text-slate-200 uppercase tracking-widest italic">{project}</h2>
						<span class="px-2.5 py-1 rounded-lg bg-slate-100 dark:bg-slate-800 text-[10px] font-bold text-slate-500">{pContainers.length}</span>
					</div>
					<div class="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-6">
						{#each pContainers as c}
							<div class="bg-white dark:bg-slate-900 rounded-[2rem] p-8 border border-slate-200/60 dark:border-slate-800 shadow-sm hover:shadow-xl hover:shadow-blue-500/5 transition-all duration-500 group flex flex-col gap-6 relative overflow-hidden">
								
								<div class="flex justify-between items-start">
									<div class="flex items-center gap-3 z-10">
										<div class="w-10 h-10 bg-blue-50 dark:bg-blue-900/40 text-blue-600 dark:text-blue-400 rounded-xl flex items-center justify-center text-xl shadow-inner uppercase font-black italic">
											{c.name.charAt(0)}
										</div>
										<div>
											<h3 class="font-black text-slate-900 dark:text-slate-100 group-hover:text-blue-600 dark:group-hover:text-blue-400 transition-colors uppercase tracking-tight italic">{c.name}</h3>
											<p class="text-[10px] font-bold font-mono text-slate-400 dark:text-slate-500 mt-1 bg-slate-100 dark:bg-slate-950 px-2 py-0.5 rounded-md inline-block uppercase italic">{c.image}</p>
										</div>
									</div>
									<div 
										class="flex items-center gap-2 px-3 py-1.5 rounded-xl text-[10px] font-black uppercase tracking-wider shadow-lg z-10
										{c.status.includes('Up') 
											? 'bg-emerald-500 text-white shadow-emerald-500/20' 
											: 'bg-rose-500 text-white shadow-rose-500/20'}"
									>
										{c.status.includes('Up') ? 'Online' : 'Stopped'}
									</div>
								</div>

								<div class="space-y-4 z-10">
									<div class="flex flex-col gap-1">
										<span class="text-[10px] font-black uppercase text-slate-400 dark:text-slate-500 tracking-widest leading-none">Status</span>
										<p class="text-sm font-bold text-slate-600 dark:text-slate-300 italic leading-tight">{c.status}</p>
									</div>

									<div class="flex flex-col gap-1">
										<span class="text-[10px] font-black uppercase text-slate-400 dark:text-slate-500 tracking-widest leading-none">Mapped Ports</span>
										<p class="text-xs font-mono font-bold text-slate-500 dark:text-slate-400 bg-slate-50 dark:bg-slate-950 p-3 rounded-xl border border-slate-100 dark:border-slate-800 uppercase italic leading-relaxed">{c.ports || 'No ports mapped'}</p>
									</div>
								</div>

								<div class="pt-4 border-t border-slate-50 dark:border-slate-800 mt-auto flex justify-between items-center gap-2 z-10">
									<div class="flex items-center gap-2">
										<!-- START -->
										<button onclick={() => performAction(c.id, 'start')} disabled={loadingAction !== null} title="Start Container" class="w-8 h-8 rounded-lg bg-emerald-50 dark:bg-emerald-900/20 text-emerald-600 dark:text-emerald-400 border border-emerald-100 dark:border-emerald-900/30 flex items-center justify-center hover:bg-emerald-500 hover:text-white dark:hover:text-white transition-all {loadingAction === c.id+'-start' ? 'opacity-50 animate-pulse' : ''}">
											<svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M14.752 11.168l-3.197-2.132A1 1 0 0010 9.87v4.263a1 1 0 001.555.832l3.197-2.132a1 1 0 000-1.664z"></path><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M21 12a9 9 0 11-18 0 9 9 0 0118 0z"></path></svg>
										</button>
										<!-- STOP -->
										<button onclick={() => performAction(c.id, 'stop')} disabled={loadingAction !== null} title="Stop Container" class="w-8 h-8 rounded-lg bg-slate-50 dark:bg-slate-800/50 text-slate-500 dark:text-slate-400 border border-slate-100 dark:border-slate-800 flex items-center justify-center hover:bg-slate-200 dark:hover:bg-slate-700 transition-all {loadingAction === c.id+'-stop' ? 'opacity-50 animate-pulse' : ''}">
											<svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M21 12a9 9 0 11-18 0 9 9 0 0118 0z" /><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 10a1 1 0 011-1h4a1 1 0 011 1v4a1 1 0 01-1 1h-4a1 1 0 01-1-1v-4z" /></svg>
										</button>
										<!-- RESTART -->
										<button onclick={() => performAction(c.id, 'restart')} disabled={loadingAction !== null} title="Restart Container" class="w-8 h-8 rounded-lg bg-amber-50 dark:bg-amber-900/20 text-amber-600 dark:text-amber-400 border border-amber-100 dark:border-amber-900/30 flex items-center justify-center hover:bg-amber-500 hover:text-white dark:hover:text-white transition-all {loadingAction === c.id+'-restart' ? 'opacity-50 animate-pulse' : ''}">
											<svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" /></svg>
										</button>
										<!-- REMOVE -->
										<button onclick={() => containerToDelete = c} disabled={loadingAction !== null} title="Remove Container" class="w-8 h-8 rounded-lg bg-rose-50 dark:bg-rose-900/10 text-rose-500 dark:text-rose-500/80 border border-rose-100 dark:border-rose-900/20 flex items-center justify-center hover:bg-rose-500 hover:text-white dark:hover:text-white transition-all ml-1 {loadingAction === c.id+'-rm' ? 'opacity-50 animate-pulse' : ''}">
											<svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" /></svg>
										</button>
									</div>

									<a href={`/container/${c.id}`} class="text-[10px] font-black uppercase text-blue-600 dark:text-blue-400 hover:text-blue-700 dark:hover:text-blue-300 underline decoration-2 underline-offset-4 leading-none uppercase italic tracking-widest ml-auto">Live Logs</a>
								</div>
							</div>
						{/each}
					</div>
				</div>
			{:else}
				<div class="col-span-full py-20 flex flex-col items-center gap-6 text-slate-300 dark:text-slate-700">
					<div class="text-8xl opacity-10 italic font-black uppercase tracking-tighter">Empty</div>
					<p class="text-sm font-bold uppercase tracking-[0.3em]">No Docker nodes found in environment</p>
				</div>
			{/each}
		</div>
	{/if}
</div>

<!-- CONFIRM DELETE MODAL -->
{#if containerToDelete}
<div class="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-900/80 backdrop-blur-sm">
	<div class="bg-white dark:bg-slate-950 border border-rose-500/30 shadow-2xl rounded-3xl p-8 max-w-sm w-full flex flex-col gap-6 animate-in slide-in-from-bottom-8 duration-200">
		<div class="w-16 h-16 rounded-full bg-rose-500/10 text-rose-500 flex items-center justify-center text-3xl mx-auto shadow-inner shadow-rose-500/20">🗑️</div>
		<div class="text-center space-y-2">
			<h3 class="text-xl font-black text-slate-900 dark:text-white uppercase tracking-tighter italic">Force Remove Container</h3>
			<p class="text-xs font-bold text-slate-500 uppercase tracking-widest leading-relaxed">Are you absolutely sure you want to delete <span class="text-rose-500">{containerToDelete.name}</span>? This action is immediate and cannot be reversed.</p>
		</div>
		<div class="flex gap-3">
			<button onclick={() => containerToDelete = null} class="flex-1 px-4 py-3 rounded-xl bg-slate-100 dark:bg-slate-800 text-slate-500 font-bold uppercase tracking-widest text-xs hover:bg-slate-200 dark:hover:bg-slate-700 transition-colors">Cancel</button>
			<button onclick={() => {
				const targetId = containerToDelete!.id;
				containerToDelete = null;
				performAction(targetId, 'rm');
			}} class="flex-1 px-4 py-3 rounded-xl bg-rose-500 text-white font-black uppercase tracking-widest text-xs hover:bg-rose-600 transition-colors shadow-lg shadow-rose-500/20">Delete Node</button>
		</div>
	</div>
</div>
{/if}
