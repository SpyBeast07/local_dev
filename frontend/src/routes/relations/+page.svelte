<script lang="ts">
	import { onMount, tick } from "svelte";
	import axios from "axios";
	import { Network } from "vis-network/standalone";

	let container = $state<HTMLElement>();
	let loading = $state(true);
	let error = $state("");
	let network: Network | null = null;
	let selectedNode = $state<any>(null);

	onMount(async () => {
		try {
			const res = await axios.get("http://127.0.0.1:8000/system/dependency-graph");
			const { nodes: backendNodes, edges: backendEdges } = res.data;
			
			loading = false;
			await tick();

			if (container) {
				const data = {
					nodes: backendNodes.map((n: any) => ({
						...n,
						group: n.type,
						title: n.label
					})),
					edges: backendEdges.map((e: any) => ({
						...e,
						arrows: "to",
						label: e.label || ""
					}))
				};

				const options: any = {
					groups: {
						container: {
							shape: 'box',
							color: {
								border: '#0ea5e9', // sky-500
								background: '#0c4a6e', // sky-900
								highlight: '#38bdf8'
							},
							font: { color: '#f0f9ff', face: 'Outfit', size: 16, bold: true },
							borderWidth: 2,
							shadow: { enabled: true, color: 'rgba(14, 165, 233, 0.2)', size: 15 }
						},
						port: {
							shape: 'dot',
							size: 20,
							color: {
								border: '#f59e0b', // amber-500
								background: '#78350f', // amber-900
								highlight: '#fbbf24'
							},
							font: { color: '#fef3c7', face: 'Outfit', size: 12 },
							borderWidth: 2
						},
						database: {
							shape: 'database',
							color: {
								border: '#10b981', // emerald-500
								background: '#064e3b', // emerald-900
								highlight: '#34d399'
							},
							font: { color: '#ecfdf5', face: 'Outfit', size: 18, bold: true },
							borderWidth: 3,
							shadow: { enabled: true, color: 'rgba(16, 185, 129, 0.3)', size: 20 }
						},
						table: {
							shape: 'box',
							color: {
								border: '#6366f1', // indigo-500
								background: '#1e1b4b', // indigo-900 
								highlight: '#818cf8'
							},
							font: { color: '#eef2ff', face: 'Outfit', size: 14 },
							borderWidth: 2,
							shapeProperties: { borderRadius: 8 }
						}
					},
					nodes: {
						font: { face: 'Outfit', color: '#ffffff' },
						margin: 10
					},
					edges: {
						color: { color: '#334155', highlight: '#6366f1' },
						width: 2,
						smooth: { type: 'continuous' },
						font: { color: '#64748b', size: 10, strokeWidth: 0 }
					},
					physics: {
						enabled: true,
						solver: 'forceAtlas2Based',
						forceAtlas2Based: {
							gravitationalConstant: -100,
							centralGravity: 0.01,
							springLength: 150,
							springConstant: 0.08
						},
						maxVelocity: 50,
						minVelocity: 0.1,
						stabilization: { iterations: 150 }
					},
					interaction: {
						hover: true,
						tooltipDelay: 100,
						zoomView: true,
						dragView: true
					}
				};

				network = new Network(container, data, options);
				
				network.on("selectNode", (params) => {
					const nodeId = params.nodes[0];
					selectedNode = backendNodes.find((n: any) => n.id === nodeId);
				});

				network.on("deselectNode", () => {
					selectedNode = null;
				});
			}
		} catch (err: any) {
			error = err.message || "Failed to analyze dependency mesh.";
			loading = false;
		}
	});

	function closePanel() {
		selectedNode = null;
		if (network) network.unselectAll();
	}
</script>

<div class="flex flex-col h-[calc(100vh-5rem)]">
	<header class="flex flex-col gap-3 shrink-0 mb-6">
		<div class="flex items-center gap-4">
			<a href="/" class="w-10 h-10 rounded-xl bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 flex items-center justify-center text-slate-400 dark:text-slate-500 hover:text-indigo-600 dark:hover:text-indigo-400 hover:border-indigo-200 dark:hover:border-indigo-800 transition-all shadow-sm" aria-label="Back to dashboard">
				<svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2.5" d="M15 19l-7-7 7-7" /></svg>
			</a>
			<h1 class="text-4xl font-black text-slate-900 dark:text-white tracking-tighter italic uppercase leading-none">Dependency Graph<span class="text-indigo-500 uppercase italic">.</span></h1>
		</div>
		<p class="text-slate-500 dark:text-slate-400 font-bold uppercase tracking-widest text-[10px] ml-14">Infrastructure Topology & Service Mesh Visualization</p>
	</header>

	<div class="flex-1 flex gap-6 min-h-0">
		<div class="relative flex-1 bg-white/50 dark:bg-slate-950/50 rounded-[2.5rem] p-4 border border-slate-200/60 dark:border-slate-800 shadow-inner overflow-hidden backdrop-blur-sm">
			{#if loading}
				<div class="absolute inset-0 flex items-center justify-center bg-slate-950/80 z-20 rounded-[2.5rem] backdrop-blur-md">
					<div class="flex flex-col items-center gap-4 text-emerald-400 font-black animate-pulse uppercase tracking-wider text-sm">
						<div class="w-10 h-10 border-4 border-current border-t-transparent rounded-full animate-spin"></div>
						Compiling Service Mesh...
					</div>
				</div>
			{/if}

			{#if error}
				<div class="absolute inset-0 flex flex-col items-center justify-center gap-4 text-rose-500 font-black">
					<div class="text-4xl italic uppercase">Offline</div>
					<p class="text-xs tracking-widest">{error}</p>
				</div>
			{/if}

			<!-- Legend -->
			<div class="absolute top-8 left-8 z-10 bg-white/80 dark:bg-slate-900/80 backdrop-blur-md px-6 py-4 rounded-[1.5rem] border border-slate-200 dark:border-slate-800 shadow-xl flex flex-col gap-4">
				<div class="text-[10px] font-black text-slate-400 uppercase tracking-[0.2em] mb-1">LEGEND</div>
				<div class="grid grid-cols-2 gap-x-6 gap-y-3">
					<div class="flex items-center gap-3">
						<div class="w-3 h-3 rounded-sm bg-sky-500 shadow-lg shadow-sky-500/50"></div>
						<span class="text-[10px] font-bold text-slate-600 dark:text-slate-300 uppercase tracking-widest">Container</span>
					</div>
					<div class="flex items-center gap-3">
						<div class="w-3 h-3 rounded-full bg-amber-500 shadow-lg shadow-amber-500/50"></div>
						<span class="text-[10px] font-bold text-slate-600 dark:text-slate-300 uppercase tracking-widest">Port</span>
					</div>
					<div class="flex items-center gap-3">
						<div class="w-3 h-3 rounded-sm bg-emerald-500 shadow-lg shadow-emerald-500/50"></div>
						<span class="text-[10px] font-bold text-slate-600 dark:text-slate-300 uppercase tracking-widest">Database</span>
					</div>
					<div class="flex items-center gap-3">
						<div class="w-3 h-3 rounded-sm bg-indigo-500 shadow-lg shadow-indigo-500/50"></div>
						<span class="text-[10px] font-bold text-slate-600 dark:text-slate-300 uppercase tracking-widest">Table</span>
					</div>
				</div>
			</div>

			<!-- Vis Network Container -->
			<div bind:this={container} class="w-full h-full rounded-[2rem] focus:outline-none"></div>
		</div>

		<!-- Side Panel -->
		{#if selectedNode}
			<div class="w-96 bg-white dark:bg-slate-900 rounded-[2.5rem] border border-slate-200 dark:border-slate-800 shadow-2xl flex flex-col overflow-hidden animate-in slide-in-from-right duration-300 relative z-30">
				<button 
					onclick={closePanel}
					class="absolute top-6 right-6 w-8 h-8 rounded-full bg-slate-100 dark:bg-slate-800 flex items-center justify-center text-slate-500 hover:bg-slate-200 dark:hover:bg-slate-700 transition-colors"
				>
					<svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2.5" d="M6 18L18 6M6 6l12 12" /></svg>
				</button>

				<div class="p-8 pb-4">
					<div class="flex items-center gap-3 mb-2">
						{#if selectedNode.type === 'container'}
							<span class="px-2 py-0.5 rounded-md bg-sky-500/10 text-sky-500 text-[10px] font-black uppercase tracking-widest border border-sky-500/20">Compute Node</span>
						{:else if selectedNode.type === 'port'}
							<span class="px-2 py-0.5 rounded-md bg-amber-500/10 text-amber-500 text-[10px] font-black uppercase tracking-widest border border-amber-500/20">Network Gate</span>
						{:else if selectedNode.type === 'database'}
							<span class="px-2 py-0.5 rounded-md bg-emerald-500/10 text-emerald-500 text-[10px] font-black uppercase tracking-widest border border-emerald-500/20">Persistent Storage</span>
						{:else}
							<span class="px-2 py-0.5 rounded-md bg-indigo-500/10 text-indigo-500 text-[10px] font-black uppercase tracking-widest border border-indigo-500/20">Relational Table</span>
						{/if}
					</div>
					<h2 class="text-2xl font-black text-slate-900 dark:text-white uppercase tracking-tighter leading-tight break-all">{selectedNode.label}</h2>
				</div>

				<div class="flex-1 overflow-y-auto px-8 pb-8 custom-scrollbar">
					<div class="flex flex-col gap-6 pt-4">
						{#if selectedNode.metadata}
							{#if selectedNode.type === 'container'}
								<section>
									<h3 class="text-[10px] font-black text-slate-400 uppercase tracking-[0.2em] mb-3">Service Details</h3>
									<div class="space-y-3">
										<div class="p-3 rounded-2xl bg-slate-50 dark:bg-slate-800/50 border border-slate-100 dark:border-slate-800">
											<div class="text-[9px] font-bold text-slate-400 uppercase mb-1">Image Reference</div>
											<div class="text-xs font-mono font-bold text-slate-700 dark:text-slate-300 break-all">{selectedNode.metadata.image}</div>
										</div>
										<div class="p-3 rounded-2xl bg-slate-50 dark:bg-slate-800/50 border border-slate-100 dark:border-slate-800">
											<div class="text-[9px] font-bold text-slate-400 uppercase mb-1">Runtime Status</div>
											<div class="text-xs font-bold text-emerald-500">{selectedNode.metadata.status}</div>
										</div>
									</div>
								</section>

								<section>
									<h3 class="text-[10px] font-black text-slate-400 uppercase tracking-[0.2em] mb-3">Environment</h3>
									<div class="flex flex-col gap-2">
										{#each selectedNode.metadata.env as env}
											<div class="text-[10px] font-mono p-2 bg-slate-950 text-emerald-400 rounded-lg border border-slate-800 break-all">
												{env}
											</div>
										{/each}
									</div>
								</section>
							{/if}

							{#if selectedNode.type === 'port'}
								<section>
									<h3 class="text-[10px] font-black text-slate-400 uppercase tracking-[0.2em] mb-3">Exposure Mapping</h3>
									<div class="p-4 rounded-2xl bg-slate-50 dark:bg-slate-800/50 border border-slate-100 dark:border-slate-800 flex flex-col gap-4">
										<div class="flex items-center justify-between">
											<span class="text-[10px] font-bold text-slate-400 uppercase">Host Port</span>
											<span class="text-lg font-black text-amber-500">{selectedNode.metadata.host_port}</span>
										</div>
										<div class="w-full h-px bg-slate-200 dark:bg-slate-800"></div>
										<div class="flex items-center justify-between">
											<span class="text-[10px] font-bold text-slate-400 uppercase">Container Internal</span>
											<span class="text-xs font-bold text-slate-600 dark:text-slate-300">{selectedNode.metadata.container_port} ({selectedNode.metadata.protocol})</span>
										</div>
									</div>
								</section>
							{/if}

							{#if selectedNode.type === 'database'}
								<section>
									<h3 class="text-[10px] font-black text-slate-400 uppercase tracking-[0.2em] mb-3">Connection Params</h3>
									<div class="space-y-3">
										<div class="p-3 rounded-2xl bg-slate-50 dark:bg-slate-800/50 border border-slate-100 dark:border-slate-800">
											<div class="text-[9px] font-bold text-slate-400 uppercase mb-1">Host Endpoint</div>
											<div class="text-xs font-bold text-slate-700 dark:text-slate-300">{selectedNode.metadata.db_host}</div>
										</div>
										<div class="p-3 rounded-2xl bg-slate-50 dark:bg-slate-800/50 border border-slate-100 dark:border-slate-800">
											<div class="text-[9px] font-bold text-slate-400 uppercase mb-1">Database Name</div>
											<div class="text-xs font-bold text-emerald-500">{selectedNode.metadata.db_name}</div>
										</div>
									</div>
								</section>
							{/if}
						{:else}
							<div class="text-center py-20 text-slate-200 dark:text-slate-800">
								<svg class="w-12 h-12 mx-auto mb-4 opacity-50" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" /></svg>
								<p class="text-[10px] font-black uppercase tracking-widest">No Deep Metadata Available</p>
							</div>
						{/if}
					</div>
				</div>
			</div>
		{/if}
	</div>
</div>

<style>
	:global(.vis-network) {
		outline: none !important;
	}

	.custom-scrollbar::-webkit-scrollbar {
		width: 4px;
	}
	.custom-scrollbar::-webkit-scrollbar-track {
		background: transparent;
	}
	.custom-scrollbar::-webkit-scrollbar-thumb {
		background: #1e293b;
		border-radius: 10px;
	}
</style>
