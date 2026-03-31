<script lang="ts">
	import { onMount, tick } from "svelte";
	import axios from "axios";
	import { Network } from "vis-network/standalone";

	let container = $state<HTMLElement>();
	let loading = $state(true);
	let hasRelations = $state(false);

	onMount(async () => {
		try {
			const res = await axios.get("http://127.0.0.1:8000/db/relations");
			const relations = Array.isArray(res.data) ? res.data : [];
			
			hasRelations = relations.length > 0;
			loading = false;
			
			await tick();

			if (hasRelations && container) {
				const nodesSet = new Set<string>();
				const edges: any[] = [];

				relations.forEach((r) => {
					nodesSet.add(r.source_table);
					nodesSet.add(r.target_table);

					edges.push({
						from: r.source_table,
						to: r.target_table,
						label: `${r.source_column} → ${r.target_column}`
					});
				});

				const nodes = Array.from(nodesSet).map((n) => ({
					id: n,
					label: n.toUpperCase()
				}));

				const data = {
					nodes,
					edges
				};

				const options: any = {
					nodes: {
						shape: "box",
						margin: { top: 20, right: 20, bottom: 20, left: 20 },
						color: {
							border: '#1e293b', // slate-800
							background: '#0f172a', // slate-950
							hover: {
								border: '#6366f1', // indigo-500
								background: '#1e1b4b' // indigo-950
							},
							highlight: {
								border: '#6366f1', // indigo-500
								background: '#1e1b4b' // indigo-950
							}
						},
						font: { 
							color: "#f8fafc", // slate-50
							face: "system-ui, sans-serif",
							size: 16,
							bold: {
								color: '#f8fafc',
								size: 16,
								vadjust: 0,
								mod: 'bold'
							}
						},
						borderWidth: 2,
						borderWidthSelected: 4,
						shapeProperties: {
							borderRadius: 16
						},
						shadow: {
							enabled: true,
							color: 'rgba(0,0,0,0.3)',
							size: 20,
							x: 0,
							y: 10
						}
					},
					edges: {
						arrows: "to",
						color: {
							color: '#f59e0b', // amber-500
							highlight: '#fbbf24', // amber-400
							hover: '#fbbf24'
						},
						width: 2,
						hoverWidth: 3,
						selectionWidth: 3,
						font: {
							color: '#94a3b8', // slate-400
							size: 11,
							align: 'middle',
							strokeWidth: 4,
							strokeColor: '#f8fafc' // for light mode readability
						},
						smooth: {
							enabled: true,
							type: 'cubicBezier',
							forceDirection: 'vertical',
							roundness: 0.4
						}
					},
					physics: {
						enabled: true,
						hierarchicalRepulsion: {
							centralGravity: 0.0,
							springLength: 200,
							springConstant: 0.01,
							nodeDistance: 250,
							damping: 0.09
						},
						solver: 'hierarchicalRepulsion'
					},
					layout: {
						hierarchical: {
							enabled: true,
							direction: 'UD',
							sortMethod: 'directed',
							nodeSpacing: 300,
							levelSeparation: 250
						}
					},
					interaction: {
						hover: true,
						tooltipDelay: 200,
						zoomView: true,
						dragView: true
					}
				};

				// Create a network instance
				new Network(container, data, options);
				
				// Apply dark mode overrides for edge text strokes if in dark mode
				const isDarkMode = document.documentElement.classList.contains('dark');
				if (isDarkMode) {
					options.edges.font.strokeColor = '#0f172a'; // slate-950 match background
					new Network(container, data, options);
				}
			}
		} catch (err) {
			console.error("Failed to load relations:", err);
		} finally {
			loading = false;
		}
	});
</script>

<div class="flex flex-col h-[calc(100vh-5rem)]">
	<header class="flex flex-col gap-3 shrink-0 mb-6">
		<div class="flex items-center gap-4">
			<a href="/" class="w-10 h-10 rounded-xl bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 flex items-center justify-center text-slate-400 dark:text-slate-500 hover:text-indigo-600 dark:hover:text-indigo-400 hover:border-indigo-200 dark:hover:border-indigo-800 transition-all shadow-sm" aria-label="Back to dashboard">
				<svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2.5" d="M15 19l-7-7 7-7" /></svg>
			</a>
			<h1 class="text-5xl font-black text-slate-900 dark:text-white tracking-tighter italic uppercase leading-none">Database Schema<span class="text-indigo-500 uppercase italic">.</span></h1>
		</div>
		<p class="text-slate-500 dark:text-slate-400 font-bold uppercase tracking-widest text-xs ml-14">Visualizing Foreign Key Relationships & Architecture</p>
	</header>

	{#if loading}
		<div class="flex items-center gap-4 text-indigo-600 dark:text-indigo-400 font-black animate-pulse uppercase tracking-wider text-sm ml-14">
			<div class="w-6 h-6 border-4 border-current border-t-transparent rounded-full animate-spin"></div>
			Analyzing Schema Topology...
		</div>
	{:else if !hasRelations}
		<div class="py-32 flex flex-col items-center justify-center gap-6 text-slate-300 dark:text-slate-700 h-full">
			<div class="text-8xl opacity-10 italic font-black uppercase tracking-tighter leading-none">Isolated</div>
			<p class="text-sm font-bold uppercase tracking-[0.3em] text-center max-w-md">No Foreign Key relationships detected in the current public schema.</p>
		</div>
	{:else}
		<div class="flex-1 min-h-[400px] w-full bg-white/50 dark:bg-slate-950/50 rounded-[2.5rem] p-4 border border-slate-200/60 dark:border-slate-800 shadow-inner relative overflow-hidden backdrop-blur-sm">
			<!-- Controls Hint overlay -->
			<div class="absolute top-8 left-8 z-10 bg-white/80 dark:bg-slate-900/80 backdrop-blur-md px-4 py-3 rounded-2xl border border-slate-200 dark:border-slate-800 shadow-xl pointer-events-none flex flex-col gap-2">
				<div class="flex items-center gap-2 text-xs font-bold text-slate-600 dark:text-slate-300 uppercase tracking-widest">
					<span class="w-4 h-4 flex items-center justify-center bg-slate-200 dark:bg-slate-800 rounded">🖱️</span> 
					Drag canvas
				</div>
				<div class="flex items-center gap-2 text-xs font-bold text-slate-600 dark:text-slate-300 uppercase tracking-widest">
					<span class="w-4 h-4 flex items-center justify-center bg-slate-200 dark:bg-slate-800 rounded">🔄</span> 
					Scroll to zoom
				</div>
			</div>

			<!-- Vis Network Container -->
			<div bind:this={container} class="w-full h-full rounded-[2rem] focus:outline-none"></div>
		</div>
	{/if}
</div>

<style>
	/* Vis Network specific overrides to remove default blue selection outline */
	:global(.vis-network) {
		outline: none !important;
	}
</style>
