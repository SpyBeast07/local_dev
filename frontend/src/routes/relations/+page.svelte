<script lang="ts">
	import { onMount, tick } from 'svelte';
	import axios from 'axios';
	import { schemaStore } from '$lib/stores/schemaStore';
	import SqlEditor from '$lib/components/SqlEditor.svelte';
	import { Network } from 'vis-network/standalone';

	let container = $state<HTMLElement>();
	let loading = $state(true);
	let error = $state('');
	let network: Network | null = null;
	let selectedNode = $state<any>(null);
	let impactData = $state<any>(null);
	let nodesDataSet: any = null;
	let edgesDataSet: any = null;
	let nodesView: any = null;
	let queryInput = $state('');
	let isTracing = $state(false);
	let traceData = $state<any>(null);

	let visibleCategories = $state({
		container: true,
		port: true,
		database: true,
		table: true
	});

	// Persistence
	function saveSettings() {
		localStorage.setItem(
			'dependency_graph_settings',
			JSON.stringify({
				visibleCategories: $state.snapshot(visibleCategories)
			})
		);
	}

	function loadSettings() {
		const saved = localStorage.getItem('dependency_graph_settings');
		if (saved) {
			const parsed = JSON.parse(saved);
			Object.assign(visibleCategories, parsed.visibleCategories);
		}
	}

	onMount(async () => {
		try {
			schemaStore.fetchSchema();

			// Read query from URL if redirected from Database page
			const urlParams = new URLSearchParams(window.location.search);
			const urlQuery = urlParams.get('query');
			if (urlQuery) {
				queryInput = decodeURIComponent(urlQuery);
				// Small delay to ensure graph is ready before tracing
				setTimeout(() => runTrace(), 500);
			}

			const res = await axios.get('http://127.0.0.1:8000/system/dependency-graph');
			const { nodes: backendNodes, edges: backendEdges } = res.data;

			loading = false;
			await tick();

			if (container) {
				const { DataSet, DataView } = await import('vis-network/standalone');
				nodesDataSet = new DataSet(
					backendNodes.map((n: any) => ({
						...n,
						group: n.type,
						title: n.label,
						originalColor: null
					}))
				);

				nodesView = new DataView(nodesDataSet, {
					filter: (item: any) => visibleCategories[item.group as keyof typeof visibleCategories]
				});

				edgesDataSet = new DataSet(
					backendEdges.map((e: any) => ({
						...e,
						arrows: 'to',
						label: e.label || '',
						originalColor: null
					}))
				);

				const data = { nodes: nodesView, edges: edgesDataSet };

				const options: any = {
					groups: {
						container: {
							shape: 'box',
							color: {
								border: '#0ea5e9',
								background: '#0c4a6e',
								highlight: '#38bdf8'
							},
							font: { color: '#f0f9ff', face: 'Outfit', size: 16, bold: true }
						},
						port: {
							shape: 'dot',
							size: 20,
							color: {
								border: '#f59e0b',
								background: '#78350f',
								highlight: '#fbbf24'
							},
							font: { color: '#fef3c7', face: 'Outfit', size: 12 }
						},
						database: {
							shape: 'database',
							color: {
								border: '#10b981',
								background: '#064e3b',
								highlight: '#34d399'
							},
							font: { color: '#ecfdf5', face: 'Outfit', size: 18, bold: true }
						},
						table: {
							shape: 'box',
							color: {
								border: '#6366f1',
								background: '#1e1b4b',
								highlight: '#818cf8'
							},
							font: { color: '#eef2ff', face: 'Outfit', size: 14 },
							shapeProperties: { borderRadius: 8 }
						}
					},
					nodes: {
						font: { face: 'Outfit', color: '#ffffff' },
						margin: 10,
						shadow: { enabled: true, color: 'rgba(0,0,0,0.5)', size: 10 }
					},
					edges: {
						color: { color: '#334155', highlight: '#6366f1', opacity: 0.8 },
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
					}
				};

				network = new Network(container, data, options);

				network.on('selectNode', async (params) => {
					const nodeId = params.nodes[0];
					const node = nodesDataSet.get(nodeId);
					selectedNode = node;

					if (node.type === 'table') {
						try {
							const impactRes = await axios.get(
								`http://127.0.0.1:8000/system/impact-analysis?table=${nodeId}`
							);
							impactData = impactRes.data;
							highlightImpact(impactData.impact_ids);
						} catch (err) {
							console.error('Impact analysis failed:', err);
						}
					} else {
						resetHighlight();
					}
				});

				network.on('deselectNode', () => {
					selectedNode = null;
					impactData = null;
					resetHighlight();
				});

				network.on('click', (params) => {
					if (params.nodes.length === 0) {
						selectedNode = null;
						impactData = null;
						refreshVisuals();
					}
				});

				loadSettings();
				refreshVisuals();
			}
		} catch (err: any) {
			error = err.message || 'Failed to analyze dependency mesh.';
			loading = false;
		}
	});

	function refreshVisuals() {
		if (!nodesDataSet || !edgesDataSet) return;

		const impactSet = new Set(impactData?.impact_ids || []);
		const originSet = new Set(impactData?.tables || (impactData?.table ? [impactData.table] : []));

		const nodeUpdates = nodesDataSet.map((n: any) => {
			const isVisible = visibleCategories[n.group as keyof typeof visibleCategories];
			const isImpacted = impactData ? impactSet.has(n.id) : true;
			const isOrigin = impactData ? originSet.has(n.id) : false;

			let opacity = 1;
			let hidden = !isVisible; // Always hide if not visible

			if (impactData && isVisible) {
				opacity = isImpacted ? 1 : 0.05;
			}

			let color = n.originalColor || null;
			if (impactData && isImpacted) {
				if (isOrigin) color = { border: '#ef4444', background: '#7f1d1d', highlight: '#f87171' };
				else if (n.type === 'table')
					color = { border: '#f97316', background: '#7c2d12', highlight: '#fb923c' };
				else if (n.type === 'container')
					color = { border: '#0ea5e9', background: '#0c4a6e', highlight: '#38bdf8' };
			}

			return {
				id: n.id,
				hidden,
				opacity,
				color,
				shadow: {
					enabled: !hidden && (isImpacted || isOrigin),
					size: isOrigin ? 30 : 10,
					color: isOrigin ? 'rgba(239, 68, 68, 0.8)' : 'rgba(0,0,0,0.5)'
				}
			};
		});

		const edgeUpdates = edgesDataSet.map((e: any) => {
			const fromNode = nodesDataSet.get(e.from);
			const toNode = nodesDataSet.get(e.to);
			if (!fromNode || !toNode) return e;

			const fromVisible = visibleCategories[fromNode.group as keyof typeof visibleCategories];
			const toVisible = visibleCategories[toNode.group as keyof typeof visibleCategories];
			const isImpacted = impactData ? impactSet.has(e.from) && impactSet.has(e.to) : true;

			let hidden = !fromVisible || !toVisible;
			let opacity = 0.8;

			if (impactData && !isImpacted) opacity = 0.05;

			return {
				id: e.id,
				hidden,
				color: { color: isImpacted && impactData ? '#f97316' : '#334155', opacity },
				width: isImpacted && impactData ? 4 : 2
			};
		});

		nodesDataSet.update(nodeUpdates);
		edgesDataSet.update(edgeUpdates);
		if (nodesView) nodesView.refresh();
		saveSettings();
	}

	function toggleCategory(cat: keyof typeof visibleCategories) {
		visibleCategories[cat] = !visibleCategories[cat];
		refreshVisuals();
	}

	function isolateCategory(cat: keyof typeof visibleCategories) {
		Object.keys(visibleCategories).forEach((key) => {
			visibleCategories[key as keyof typeof visibleCategories] = key === cat;
		});
		refreshVisuals();
	}

	function fullView() {
		Object.keys(visibleCategories).forEach((key) => {
			visibleCategories[key as keyof typeof visibleCategories] = true;
		});
		refreshVisuals();
	}

	function infraView() {
		visibleCategories.container = true;
		visibleCategories.port = true;
		visibleCategories.database = false;
		visibleCategories.table = false;
		refreshVisuals();
	}

	function dataView() {
		visibleCategories.container = false;
		visibleCategories.port = false;
		visibleCategories.database = true;
		visibleCategories.table = true;
		refreshVisuals();
	}

	function resetFilters() {
		fullView();
		refreshVisuals();
	}

	async function runTrace() {
		if (!queryInput.trim()) return;
		isTracing = true;
		try {
			const res = await axios.post('http://127.0.0.1:8000/system/trace-query', {
				query: queryInput
			});
			impactData = res.data;
			refreshVisuals();
		} catch (err) {
			console.error('Trace failed:', err);
		} finally {
			isTracing = false;
		}
	}

	function highlightImpact(impactIds: string[], originIds: string[] = []) {
		if (!nodesDataSet || !edgesDataSet) return;

		const impactSet = new Set(impactIds);
		const originSet = new Set(
			originIds.length > 0 ? originIds : impactData?.table ? [impactData.table] : []
		);

		nodesDataSet.update(
			nodesDataSet.map((n: any) => {
				const isImpacted = impactSet.has(n.id);
				const isOrigin = originSet.has(n.id);

				let color = n.color;
				if (isOrigin) {
					color = { border: '#ef4444', background: '#7f1d1d', highlight: '#f87171' };
				} else if (isImpacted && n.type === 'table') {
					color = { border: '#f97316', background: '#7c2d12', highlight: '#fb923c' };
				} else if (isImpacted && n.type === 'container') {
					color = { border: '#0ea5e9', background: '#0c4a6e', highlight: '#38bdf8' };
				}

				return {
					id: n.id,
					opacity: isImpacted ? 1 : 0.1,
					color: isImpacted ? color : { opacity: 0.1 },
					shadow: {
						enabled: isImpacted,
						size: isOrigin ? 40 : 15,
						color: isOrigin ? 'rgba(239, 68, 68, 0.8)' : 'rgba(0,0,0,0.5)'
					}
				};
			})
		);

		edgesDataSet.update(
			edgesDataSet.map((e: any) => {
				const isImpacted = impactSet.has(e.from) && impactSet.has(e.to);
				return {
					id: e.id,
					color: isImpacted
						? { color: '#f97316', highlight: '#f97316' }
						: { color: '#1e293b', opacity: 0.1 },
					width: isImpacted ? 4 : 1
				};
			})
		);
	}

	function resetHighlight() {
		impactData = null;
		traceData = null;
		refreshVisuals();
	}

	function closePanel() {
		selectedNode = null;
		impactData = null;
		traceData = null;
		resetHighlight();
		if (network) network.unselectAll();
	}
</script>

<div class="flex flex-col h-[calc(100vh-5rem)]">
	<header class="flex flex-col gap-3 shrink-0 mb-6">
		<div class="flex items-center gap-4">
			<a
				href="/"
				class="w-10 h-10 rounded-xl bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 flex items-center justify-center text-slate-400 dark:text-slate-500 hover:text-indigo-600 dark:hover:text-indigo-400 hover:border-indigo-200 dark:hover:border-indigo-800 transition-all shadow-sm"
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
				class="text-4xl font-black text-slate-900 dark:text-white tracking-tighter italic uppercase leading-none"
			>
				Dependency Graph<span class="text-indigo-500 uppercase italic">.</span>
			</h1>
		</div>
		<p
			class="text-slate-500 dark:text-slate-400 font-bold uppercase tracking-widest text-[10px] ml-14"
		>
			Infrastructure Topology & Service Mesh Visualization
		</p>
	</header>

	<div class="flex-1 flex gap-6 min-h-0 relative">
		<div
			class="relative flex-1 bg-white/50 dark:bg-slate-950/50 rounded-[2.5rem] p-4 border border-slate-200/60 dark:border-slate-800 shadow-inner overflow-hidden backdrop-blur-sm"
		>
			{#if loading}
				<div
					class="absolute inset-0 flex items-center justify-center bg-slate-950/80 z-20 rounded-[2.5rem] backdrop-blur-md"
				>
					<div
						class="flex flex-col items-center gap-4 text-emerald-400 font-black animate-pulse uppercase tracking-wider text-sm"
					>
						<div
							class="w-10 h-10 border-4 border-current border-t-transparent rounded-full animate-spin"
						></div>
						Compiling Service Mesh...
					</div>
				</div>
			{/if}

			{#if error}
				<div
					class="absolute inset-0 flex flex-col items-center justify-center gap-4 text-rose-500 font-black"
				>
					<div class="text-4xl italic uppercase">Offline</div>
					<p class="text-xs tracking-widest">{error}</p>
				</div>
			{/if}

			<div
				class="absolute top-8 left-8 z-10 bg-white/80 dark:bg-slate-900/80 backdrop-blur-md px-6 py-5 rounded-[1.5rem] border border-slate-200 dark:border-slate-800 shadow-2xl flex flex-col gap-5 w-64 animate-in fade-in slide-in-from-left duration-500"
			>
				<div>
					<div class="flex items-center justify-between mb-4">
						<span class="text-[10px] font-black text-slate-400 uppercase tracking-[0.2em]"
							>LEGEND</span
						>
						<button
							onclick={resetFilters}
							class="text-[9px] font-black text-indigo-500 hover:text-indigo-600 uppercase tracking-widest transition-colors flex items-center gap-1"
						>
							<svg class="w-2.5 h-2.5" fill="none" stroke="currentColor" viewBox="0 0 24 24"
								><path
									stroke-linecap="round"
									stroke-linejoin="round"
									stroke-width="3"
									d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15"
								/></svg
							>
							Reset
						</button>
					</div>
					<div class="grid grid-cols-2 gap-x-6 gap-y-3">
						<!-- Legend Toggles -->
						<button
							onclick={() => toggleCategory('container')}
							ondblclick={() => isolateCategory('container')}
							class="flex items-center gap-3 cursor-pointer group text-left {visibleCategories.container
								? ''
								: 'opacity-30 grayscale'}"
							title="Click to toggle, Double-click to isolate"
						>
							<div
								class="w-3 h-3 rounded-sm bg-sky-500 shadow-lg shadow-sky-500/50 group-hover:scale-110 transition-transform"
							></div>
							<span
								class="text-[10px] font-bold text-slate-600 dark:text-slate-300 uppercase tracking-widest leading-none"
								>Container</span
							>
						</button>
						<button
							onclick={() => toggleCategory('port')}
							ondblclick={() => isolateCategory('port')}
							class="flex items-center gap-3 cursor-pointer group text-left {visibleCategories.port
								? ''
								: 'opacity-30 grayscale'}"
							title="Click to toggle, Double-click to isolate"
						>
							<div
								class="w-3 h-3 rounded-full bg-amber-500 shadow-lg shadow-amber-500/50 group-hover:scale-110 transition-transform"
							></div>
							<span
								class="text-[10px] font-bold text-slate-600 dark:text-slate-300 uppercase tracking-widest leading-none"
								>Port</span
							>
						</button>
						<button
							onclick={() => toggleCategory('database')}
							ondblclick={() => isolateCategory('database')}
							class="flex items-center gap-3 cursor-pointer group text-left {visibleCategories.database
								? ''
								: 'opacity-30 grayscale'}"
							title="Click to toggle, Double-click to isolate"
						>
							<div
								class="w-3 h-3 rounded-sm bg-emerald-500 shadow-lg shadow-emerald-500/50 group-hover:scale-110 transition-transform"
							></div>
							<span
								class="text-[10px] font-bold text-slate-600 dark:text-slate-300 uppercase tracking-widest leading-none"
								>Database</span
							>
						</button>
						<button
							onclick={() => toggleCategory('table')}
							ondblclick={() => isolateCategory('table')}
							class="flex items-center gap-3 cursor-pointer group text-left {visibleCategories.table
								? ''
								: 'opacity-30 grayscale'}"
							title="Click to toggle, Double-click to isolate"
						>
							<div
								class="w-3 h-3 rounded-sm bg-indigo-500 shadow-lg shadow-indigo-500/50 group-hover:scale-110 transition-transform"
							></div>
							<span
								class="text-[10px] font-bold text-slate-600 dark:text-slate-300 uppercase tracking-widest leading-none"
								>Table</span
							>
						</button>
					</div>
				</div>

				<div class="h-px bg-slate-200 dark:bg-slate-800"></div>

				<div>
					<span class="text-[10px] font-black text-slate-400 uppercase tracking-[0.2em] mb-3 block"
						>Presets</span
					>
					<div class="flex flex-wrap gap-2">
						<button
							onclick={infraView}
							class="px-2 py-1.5 rounded-lg bg-slate-100 dark:bg-slate-800 hover:bg-indigo-500 dark:hover:bg-indigo-600 text-slate-600 dark:text-slate-400 hover:text-white text-[9px] font-black uppercase tracking-widest transition-all"
						>
							Infra
						</button>
						<button
							onclick={dataView}
							class="px-2 py-1.5 rounded-lg bg-slate-100 dark:bg-slate-800 hover:bg-indigo-500 dark:hover:bg-indigo-600 text-slate-600 dark:text-slate-400 hover:text-white text-[9px] font-black uppercase tracking-widest transition-all"
						>
							Data
						</button>
						<button
							onclick={fullView}
							class="px-2 py-1.5 rounded-lg bg-slate-100 dark:bg-slate-800 hover:bg-indigo-500 dark:hover:bg-indigo-600 text-slate-600 dark:text-slate-400 hover:text-white text-[9px] font-black uppercase tracking-widest transition-all"
						>
							Full
						</button>
					</div>
				</div>
			</div>

			<div bind:this={container} class="w-full h-full rounded-[2rem] focus:outline-none"></div>

			<div
				class="absolute bottom-8 left-1/2 -translate-x-1/2 z-20 w-[800px] bg-slate-900/95 backdrop-blur-2xl border border-slate-700/80 p-3 rounded-[1.8rem] shadow-[0_30px_50px_-15px_rgba(0,0,0,0.6)] flex items-center gap-4 transition-all {queryInput
					? 'ring-4 ring-indigo-500/20'
					: ''}"
			>
				<div
					class="w-12 h-12 rounded-2xl bg-indigo-500/10 flex items-center justify-center text-indigo-400 shrink-0 border border-indigo-500/20 shadow-inner"
				>
					<svg class="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24"
						><path
							stroke-linecap="round"
							stroke-linejoin="round"
							stroke-width="2.5"
							d="M13 10V3L4 14h7v7l9-11h-7z"
						/></svg
					>
				</div>
				<div class="flex-1 min-w-0">
					<SqlEditor
						bind:value={queryInput}
						onRun={runTrace}
						singleLine={true}
						autocomplete={false}
						placeholder="Trace SQL impact (e.g. SELECT * FROM users)..."
					/>
				</div>
				<button
					onclick={runTrace}
					disabled={isTracing || !queryInput}
					class="px-8 py-3.5 bg-indigo-600 hover:bg-indigo-500 disabled:bg-slate-800 disabled:text-slate-600 text-white text-[11px] font-black uppercase tracking-[0.2em] rounded-2xl transition-all flex items-center gap-3 shadow-lg shadow-indigo-500/20 active:scale-95"
				>
					{#if isTracing}
						<div
							class="w-3 h-3 border-2 border-current border-t-transparent rounded-full animate-spin"
						></div>
						Tracing
					{:else}
						Trace Query
					{/if}
				</button>
				{#if impactData || traceData}
					<button
						onclick={() => {
							queryInput = '';
							resetHighlight();
						}}
						class="w-12 h-12 rounded-2xl hover:bg-slate-800 flex items-center justify-center text-slate-500 transition-colors"
						aria-label="Reset view"
					>
						<svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"
							><path
								stroke-linecap="round"
								stroke-linejoin="round"
								stroke-width="2"
								d="M6 18L18 6M6 6l12 12"
							/></svg
						>
					</button>
				{/if}
			</div>
		</div>

		{#if selectedNode || impactData || traceData}
			<div
				class="w-96 bg-white dark:bg-slate-900 rounded-[2.5rem] border border-slate-200 dark:border-slate-800 shadow-2xl flex flex-col overflow-hidden animate-in slide-in-from-right duration-300 relative z-30"
			>
				<button
					onclick={closePanel}
					class="absolute top-6 right-6 w-8 h-8 rounded-full bg-slate-100 dark:bg-slate-800 flex items-center justify-center text-slate-500 hover:bg-slate-200 dark:hover:bg-slate-700 transition-colors"
					aria-label="Close panel"
				>
					<svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"
						><path
							stroke-linecap="round"
							stroke-linejoin="round"
							stroke-width="2.5"
							d="M6 18L18 6M6 6l12 12"
						/></svg
					>
				</button>

				<div class="p-8 pb-4">
					{#if traceData}
						<div class="flex items-center gap-3 mb-2">
							<span
								class="px-2 py-0.5 rounded-md bg-indigo-500/10 text-indigo-500 text-[10px] font-black uppercase tracking-widest border border-indigo-500/20"
								>Query Flow Trace</span
							>
						</div>
						<h2
							class="text-xl font-black text-slate-900 dark:text-white uppercase tracking-tighter leading-tight line-clamp-2 italic"
						>
							"{queryInput}"
						</h2>
					{:else if selectedNode}
						<div class="flex items-center gap-3 mb-2">
							{#if selectedNode.type === 'container'}
								<span
									class="px-2 py-0.5 rounded-md bg-sky-500/10 text-sky-500 text-[10px] font-black uppercase tracking-widest border border-sky-500/20"
									>Compute Node</span
								>
							{:else if selectedNode.type === 'port'}
								<span
									class="px-2 py-0.5 rounded-md bg-amber-500/10 text-amber-500 text-[10px] font-black uppercase tracking-widest border border-amber-500/20"
									>Network Gate</span
								>
							{:else if selectedNode.type === 'database'}
								<span
									class="px-2 py-0.5 rounded-md bg-emerald-500/10 text-emerald-500 text-[10px] font-black uppercase tracking-widest border border-emerald-500/20"
									>Persistent Storage</span
								>
							{:else}
								<span
									class="px-2 py-0.5 rounded-md bg-indigo-500/10 text-indigo-500 text-[10px] font-black uppercase tracking-widest border border-indigo-500/20"
									>Relational Table</span
								>
							{/if}
						</div>
						<h2
							class="text-2xl font-black text-slate-900 dark:text-white uppercase tracking-tighter leading-tight break-all"
						>
							{selectedNode.label}
						</h2>
					{/if}
				</div>

				<div class="flex-1 overflow-y-auto px-8 pb-8 custom-scrollbar">
					<div class="flex flex-col gap-6 pt-4">
						{#if impactData}
							<section
								class="p-4 rounded-2xl bg-rose-500/10 border border-rose-500/20 {impactData.severity ===
								'HIGH'
									? 'animate-pulse shadow-[0_0_20px_rgba(239,68,68,0.2)]'
									: ''}"
							>
								<div class="flex items-center justify-between mb-2">
									<h3 class="text-[10px] font-black text-rose-500 uppercase tracking-[0.2em]">
										🚨 {traceData ? 'Cloud Fallout' : 'Impact Analysis'}
									</h3>
									<span
										class="px-2 py-0.5 rounded text-[10px] font-black uppercase tracking-widest border
										{impactData.severity === 'HIGH'
											? 'bg-rose-500 text-white border-rose-600'
											: impactData.severity === 'MEDIUM'
												? 'bg-orange-500 text-white border-orange-600'
												: 'bg-emerald-500 text-white border-emerald-600'}"
									>
										{impactData.severity} IMPACT
									</span>
								</div>
								<p class="text-xs font-bold text-rose-400 leading-relaxed mb-4">
									{impactData.summary}
								</p>

								<div class="space-y-4">
									<div>
										<div class="text-[9px] font-bold text-rose-500/60 uppercase mb-1">
											Affected Tables
										</div>
										<div class="flex flex-wrap gap-1">
											{#each impactData.dependent_tables as table}
												<span
													class="text-[9px] px-2 py-1 bg-rose-500/20 text-rose-300 rounded-md font-bold uppercase"
													>{table.split('.').pop()}</span
												>
											{/each}
										</div>
									</div>
									<div>
										<div class="text-[9px] font-bold text-rose-500/60 uppercase mb-1">
											Impacted Containers
										</div>
										<div class="flex flex-wrap gap-1">
											{#each impactData.containers as container}
												<span
													class="text-[9px] px-2 py-1 bg-sky-500/20 text-sky-300 rounded-md font-bold uppercase"
													>{container}</span
												>
											{/each}
										</div>
									</div>
								</div>
							</section>
						{/if}

						{#if selectedNode && selectedNode.metadata && !traceData}
							{#if selectedNode.type === 'container'}
								<section>
									<h3 class="text-[10px] font-black text-slate-400 uppercase tracking-[0.2em] mb-3">
										Service Details
									</h3>
									<div class="space-y-3">
										<div
											class="p-3 rounded-2xl bg-slate-50 dark:bg-slate-800/50 border border-slate-100 dark:border-slate-800"
										>
											<div class="text-[9px] font-bold text-slate-400 uppercase mb-1">
												Image Reference
											</div>
											<div
												class="text-xs font-mono font-bold text-slate-700 dark:text-slate-300 break-all"
											>
												{selectedNode.metadata.image}
											</div>
										</div>
										<div
											class="p-3 rounded-2xl bg-slate-50 dark:bg-slate-800/50 border border-slate-100 dark:border-slate-800"
										>
											<div class="text-[9px] font-bold text-slate-400 uppercase mb-1">
												Runtime Status
											</div>
											<div class="text-xs font-bold text-emerald-500">
												{selectedNode.metadata.status}
											</div>
										</div>
									</div>
								</section>
								<section>
									<h3 class="text-[10px] font-black text-slate-400 uppercase tracking-[0.2em] mb-3">
										Environment
									</h3>
									<div class="flex flex-col gap-2">
										{#each selectedNode.metadata.env || [] as env}
											<div
												class="text-[10px] font-mono p-2 bg-slate-950 text-emerald-400 rounded-lg border border-slate-800 break-all"
											>
												{env}
											</div>
										{/each}
									</div>
								</section>
							{/if}

							{#if selectedNode.type === 'port'}
								<section>
									<h3 class="text-[10px] font-black text-slate-400 uppercase tracking-[0.2em] mb-3">
										Exposure Mapping
									</h3>
									<div
										class="p-4 rounded-2xl bg-slate-50 dark:bg-slate-800/50 border border-slate-100 dark:border-slate-800 flex flex-col gap-4"
									>
										<div class="flex items-center justify-between">
											<span class="text-[10px] font-bold text-slate-400 uppercase">Host Port</span>
											<span class="text-lg font-black text-amber-500"
												>{selectedNode.metadata.host_port}</span
											>
										</div>
										<div class="w-full h-px bg-slate-200 dark:bg-slate-800"></div>
										<div class="flex items-center justify-between">
											<span class="text-[10px] font-bold text-slate-400 uppercase"
												>Container Internal</span
											>
											<span class="text-xs font-bold text-slate-600 dark:text-slate-300"
												>{selectedNode.metadata.container_port} ({selectedNode.metadata
													.protocol})</span
											>
										</div>
									</div>
								</section>
							{/if}

							{#if selectedNode.type === 'database'}
								<section>
									<h3 class="text-[10px] font-black text-slate-400 uppercase tracking-[0.2em] mb-3">
										Connection Params
									</h3>
									<div class="space-y-3">
										<div
											class="p-3 rounded-2xl bg-slate-50 dark:bg-slate-800/50 border border-slate-100 dark:border-slate-800"
										>
											<div class="text-[9px] font-bold text-slate-400 uppercase mb-1">
												Host Endpoint
											</div>
											<div class="text-xs font-bold text-slate-700 dark:text-slate-300">
												{selectedNode.metadata.db_host}
											</div>
										</div>
										<div
											class="p-3 rounded-2xl bg-slate-50 dark:bg-slate-800/50 border border-slate-100 dark:border-slate-800"
										>
											<div class="text-[9px] font-bold text-slate-400 uppercase mb-1">
												Database Name
											</div>
											<div class="text-xs font-bold text-emerald-500">
												{selectedNode.metadata.db_name}
											</div>
										</div>
									</div>
								</section>
							{/if}
						{/if}

						{#if !impactData && !selectedNode && !traceData}
							<div class="text-center py-20 text-slate-200 dark:text-slate-800">
								<svg
									class="w-12 h-12 mx-auto mb-4 opacity-50"
									fill="none"
									stroke="currentColor"
									viewBox="0 0 24 24"
									><path
										stroke-linecap="round"
										stroke-linejoin="round"
										stroke-width="2"
										d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"
									/></svg
								>
								<p class="text-[10px] font-black uppercase tracking-widest">
									Select Node or Trace Query
								</p>
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
