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
	let nodesDataSet = $state<any>(null);
	let edgesDataSet = $state<any>(null);
	let nodesView = $state<any>(null);
	let queryInput = $state('');
	let isTracing = $state(false);
	let traceData = $state<any>(null);

	let visibleCategories = $state({
		container: true,
		port: true,
		database: true,
		table: true
	});
	let hiddenNodeIds = $state<Record<string, boolean>>({});
	let expandedGroups = $state<Record<string, boolean>>({
		container: true,
		database: true,
		table: false,
		port: false
	});
	let activeTooltip = $state<string | null>(null);
	let searchTerm = $state('');

	// Persistence
	function saveSettings() {
		localStorage.setItem(
			'dependency_graph_settings',
			JSON.stringify({
				visibleCategories: $state.snapshot(visibleCategories),
				hiddenNodeIds: $state.snapshot(hiddenNodeIds)
			})
		);
	}

	function loadSettings() {
		const saved = localStorage.getItem('dependency_graph_settings');
		if (saved) {
			const parsed = JSON.parse(saved);
			Object.assign(visibleCategories, parsed.visibleCategories);
			if (parsed.hiddenNodeIds) {
				Object.assign(hiddenNodeIds, parsed.hiddenNodeIds);
			}
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

			// Close tooltips on outside click
			window.addEventListener('click', (e) => {
				const target = e.target as HTMLElement;
				// Close if clicking outside the legend/tooltip area
				if (!target.closest('.legend-container')) {
					activeTooltip = null;
				}
			});

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
					filter: (item: any) => {
						if (hiddenNodeIds[item.id]) return false;
						const group = item.group as string;
						if (group === 'service_group') {
							const children = nodesDataSet.get({
								filter: (childNode: any) => 
									childNode.group === 'container' && 
									childNode.metadata?.project === item.metadata?.project_name
							});
							return children.some((c: any) => visibleCategories.container && !hiddenNodeIds[c.id]);
						}
						return visibleCategories[group as keyof typeof visibleCategories] ?? true;
					}
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
						service_group: {
							shape: 'hexagon',
							color: {
								border: '#6366f1',
								background: '#312e81',
								highlight: '#818cf8'
							},
							font: { color: '#ffffff', face: 'Outfit', size: 20, bold: true },
							margin: 15
						},
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
			if (hiddenNodeIds[n.id]) return { id: n.id, hidden: true, opacity: 0 };
			let isVisible = visibleCategories[n.group as keyof typeof visibleCategories] ?? true;
			if (n.group === 'service_group') {
				const children = nodesDataSet.get({
					filter: (child: any) => 
						child.group === 'container' && 
						child.metadata?.project === n.metadata?.project_name
				});
				isVisible = children.some((c: any) => visibleCategories.container && !hiddenNodeIds[c.id]);
			}
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
				else if (n.type === 'container' || n.type === 'service_group')
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

			const getVis = (group: string, id: string) => {
				if (hiddenNodeIds[id]) return false;
				if (group === 'service_group') {
					const node = nodesDataSet.get(id);
					const children = nodesDataSet.get({
						filter: (child: any) => 
							child.group === 'container' && 
							child.metadata?.project === node.metadata?.project_name
					});
					return children.some((c: any) => visibleCategories.container && !hiddenNodeIds[c.id]);
				}
				return visibleCategories[group as keyof typeof visibleCategories] ?? true;
			};

			const fromVisible = getVis(fromNode.group, fromNode.id);
			const toVisible = getVis(toNode.group, toNode.id);
			const isImpacted = impactData ? impactSet.has(e.from) && impactSet.has(e.to) : true;

			let hidden = !fromVisible || !toVisible;
			let opacity = 0.8;
			let dashes = e.type === 'membership';

			if (e.type === 'membership') {
				opacity = 0.4;
			}

			if (impactData && !isImpacted) opacity = 0.05;

			return {
				id: e.id,
				hidden,
				dashes,
				color: {
					color:
						isImpacted && impactData
							? '#f97316'
							: e.type === 'provides'
								? '#10b981'
								: e.type === 'membership'
									? '#64748b'
									: '#334155',
					opacity
				},
				width: isImpacted && impactData ? 4 : e.type === 'provides' ? 4 : e.type === 'membership' ? 1 : 2,
				arrows: e.type === 'membership' ? '' : 'to'
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
		hiddenNodeIds = {};
		refreshVisuals();
	}

	function toggleNode(id: string) {
		hiddenNodeIds[id] = !hiddenNodeIds[id];
		refreshVisuals();
	}

	function toggleGroupNodes(type: string, show: boolean) {
		const nodes = nodesDataSet.get({ filter: (n: any) => n.type === type });
		nodes.forEach((n: any) => {
			hiddenNodeIds[n.id] = !show;
		});
		saveSettings();
		refreshVisuals();
	}

	function toggleAccordion(type: string) {
		expandedGroups[type] = !expandedGroups[type];
	}

	function toggleTooltip(type: string | null) {
		if (activeTooltip === type) activeTooltip = null;
		else activeTooltip = type;
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
		<!-- Query Tracer -->
		<div
			class="absolute top-0 right-20 -translate-y-1/2 z-50 w-[580px] bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 p-1.5 rounded-2xl shadow-2xl flex items-center gap-2 transition-all {queryInput
				? 'ring-4 ring-indigo-500/10'
				: ''}"
		>
				<div
					class="w-8 h-8 rounded-lg bg-indigo-500/10 flex items-center justify-center text-indigo-500 shrink-0 border border-indigo-500/5 group"
				>
					<svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"
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
						placeholder="Trace SQL impact..."
					/>
				</div>
				<button
					onclick={(e) => {
						e.stopPropagation();
						runTrace();
					}}
					disabled={isTracing || !queryInput}
					class="px-5 py-2 bg-indigo-600 hover:bg-indigo-500 disabled:bg-slate-200 dark:disabled:bg-slate-800 disabled:text-slate-400 dark:disabled:text-slate-500 text-white text-[10px] font-black uppercase tracking-widest rounded-xl transition-all flex items-center gap-2 shadow-sm active:scale-95 shrink-0"
				>
					{#if isTracing}
						<div
							class="w-3 h-3 border-2 border-current border-t-transparent rounded-full animate-spin"
						></div>
					{:else}
						Trace
					{/if}
				</button>
				{#if impactData || traceData}
					<button
						onclick={(e) => {
							e.stopPropagation();
							queryInput = '';
							resetHighlight();
						}}
						class="w-8 h-8 rounded-lg hover:bg-slate-100 dark:hover:bg-slate-800 flex items-center justify-center text-slate-500 transition-colors shrink-0"
						aria-label="Reset view"
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
				{/if}
			</div>

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
					class="legend-container absolute top-8 left-8 z-10 bg-white/80 dark:bg-slate-900/80 backdrop-blur-md px-6 py-5 rounded-[1.5rem] border border-slate-200 dark:border-slate-800 shadow-2xl flex flex-col gap-5 w-64 animate-in fade-in slide-in-from-left duration-500"
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
							{#each [ { id: 'container', label: 'Container', color: 'bg-sky-500', shape: 'rounded-sm' }, { id: 'port', label: 'Port', color: 'bg-amber-500', shape: 'rounded-full' }, { id: 'database', label: 'Database', color: 'bg-emerald-500', shape: 'rounded-sm' }, { id: 'table', label: 'Table', color: 'bg-indigo-500', shape: 'rounded-sm' } ] as cat}
								<div class="relative">
									<div
										class="flex items-center gap-3 group {visibleCategories[
											cat.id as keyof typeof visibleCategories
										]
											? ''
											: 'opacity-30 grayscale'}"
									>
										<button
											onclick={(e) => {
												e.stopPropagation();
												toggleCategory(cat.id as any);
											}}
											ondblclick={() => isolateCategory(cat.id as any)}
											class="w-3 h-3 {cat.shape} {cat.color} shadow-lg shadow-current/50 cursor-pointer hover:scale-125 transition-transform"
											title="Toggle Category (Dbl-click to isolate)"
										></button>
										<button
											onclick={(e) => {
												e.stopPropagation();
												toggleTooltip(cat.id);
											}}
											class="text-[10px] font-bold text-slate-600 dark:text-slate-300 uppercase tracking-widest leading-none hover:text-indigo-500 transition-colors text-left truncate flex-1 tooltip-trigger"
										>
											{cat.label}
										</button>
									</div>

									{#if activeTooltip === cat.id}
										{@const nodes =
											nodesDataSet?.get({ filter: (n: any) => n.type === cat.id }) || []}
										{@const allVisible = nodes.every((n: any) => !hiddenNodeIds[n.id])}
										<!-- Tooltip Dialog -->
										<div
											class="absolute top-full left-0 mt-3 w-64 bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-2xl shadow-2xl z-[100] p-4 animate-in fade-in zoom-in-95 duration-200"
										>
											<div class="flex items-center justify-between mb-4">
												<span
													class="text-[9px] font-black text-slate-400 uppercase tracking-widest"
													>{cat.label}S</span
												>
												<button
													onclick={(e) => {
														e.stopPropagation();
														toggleGroupNodes(cat.id, !allVisible);
													}}
													class="text-[8px] font-black uppercase px-2 py-1 rounded bg-slate-100 dark:bg-slate-800 text-slate-500 hover:bg-indigo-500 hover:text-white transition-all"
												>
													{allVisible ? 'Hide All' : 'Show All'}
												</button>
											</div>

											<div class="max-h-48 overflow-y-auto pr-1 space-y-1 custom-scrollbar">
												{#if nodes.length === 0}
													<div class="text-[9px] text-slate-400 italic py-2">
														No {cat.label.toLowerCase()}s found.
													</div>
												{:else}
													{#each nodes as node}
														<button
															onclick={(e) => {
																e.stopPropagation();
																toggleNode(node.id);
																saveSettings();
															}}
															class="w-full flex items-center justify-between px-2 py-1.5 rounded-lg hover:bg-slate-50 dark:hover:bg-white/5 transition-all {hiddenNodeIds[
																node.id
															]
																? 'opacity-40'
																: 'bg-slate-100/50 dark:bg-white/5 shadow-sm'}"
														>
															<span
																class="text-[10px] font-bold text-slate-600 dark:text-slate-300 truncate pr-2"
																>{node.label}</span
															>
															<div
																class="w-3.5 h-3.5 rounded border flex items-center justify-center transition-all {hiddenNodeIds[
																	node.id
																]
																	? 'border-slate-300 dark:border-slate-700'
																	: 'bg-indigo-500 border-indigo-500'}"
															>
																{#if !hiddenNodeIds[node.id]}
																	<svg
																		class="w-2.5 h-2.5 text-white"
																		fill="none"
																		stroke="currentColor"
																		viewBox="0 0 24 24"
																		><path
																			stroke-linecap="round"
																			stroke-linejoin="round"
																			stroke-width="4"
																			d="M5 13l4 4L19 7"
																		/></svg
																	>
																{/if}
															</div>
														</button>
													{/each}
												{/if}
											</div>

											<!-- Triangle Pointer -->
											<div
												class="absolute -top-1.5 left-3 w-3 h-3 bg-white dark:bg-slate-900 border-t border-l border-slate-200 dark:border-slate-800 rotate-45"
											></div>
										</div>
									{/if}
								</div>
							{/each}
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
							{#if selectedNode.type === 'service_group'}
								<span
									class="px-2 py-0.5 rounded-md bg-indigo-500/10 text-indigo-500 text-[10px] font-black uppercase tracking-widest border border-indigo-500/20"
									>Project Cluster</span
								>
							{:else if selectedNode.type === 'container'}
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
							{#if selectedNode.type === 'service_group'}
								<section>
									<h3 class="text-[10px] font-black text-slate-400 uppercase tracking-[0.2em] mb-4">
										Project Overview
									</h3>
									<div class="space-y-4">
										<div class="p-4 rounded-2xl bg-indigo-500/10 border border-indigo-500/20">
											<div class="text-[9px] font-bold text-indigo-400 uppercase mb-1">
												Project Stack
											</div>
											<div class="text-2xl font-black text-indigo-500 tracking-tighter uppercase italic">
												{selectedNode.metadata.project_name}
											</div>
										</div>
										<div class="p-3 rounded-2xl bg-slate-50 dark:bg-slate-800/50 border border-slate-100 dark:border-slate-800">
											<div class="text-[9px] font-bold text-slate-400 uppercase mb-1">
												Total Scaling
											</div>
											<div class="text-xs font-bold text-slate-700 dark:text-slate-300">
												{selectedNode.metadata.instance_count} CONTAINERS
											</div>
										</div>
									</div>
								</section>
							{/if}
							{#if selectedNode.type === 'container'}
								<section>
									<div class="flex items-center justify-between mb-3">
										<h3 class="text-[10px] font-black text-slate-400 uppercase tracking-[0.2em]">
											Service Details
										</h3>
										{#if selectedNode.metadata.is_group}
											<span class="px-2 py-0.5 rounded bg-indigo-500/10 text-indigo-500 text-[9px] font-black uppercase tracking-widest border border-indigo-500/20">
												{selectedNode.metadata.instance_count} INSTANCES
											</span>
										{/if}
									</div>
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
										
										{#if selectedNode.metadata.is_group}
											<div
												class="p-3 rounded-2xl bg-slate-50 dark:bg-slate-800/50 border border-slate-100 dark:border-slate-800"
											>
												<div class="text-[9px] font-bold text-slate-400 uppercase mb-1">
													Active Instances
												</div>
												<div class="flex flex-wrap gap-1 mt-1">
													{#each selectedNode.metadata.instances as inst}
														<span class="text-[9px] px-2 py-1 bg-indigo-500/10 text-indigo-400 rounded-md font-bold border border-indigo-500/10 uppercase tracking-tighter">
															{inst}
														</span>
													{/each}
												</div>
											</div>
										{/if}

										<div
											class="p-3 rounded-2xl bg-slate-50 dark:bg-slate-800/50 border border-slate-100 dark:border-slate-800"
										>
											<div class="text-[9px] font-bold text-slate-400 uppercase mb-1">
												Runtime Status
											</div>
											<div class="text-xs font-bold text-emerald-500">
												{selectedNode.metadata.status_summary || selectedNode.metadata.status}
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
