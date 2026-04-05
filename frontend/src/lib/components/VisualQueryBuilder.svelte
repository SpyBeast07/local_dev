<script lang="ts">
	import { onMount, onDestroy, tick } from 'svelte';
	import axios from 'axios';
	import { schemaStore, type SchemaMetadata, type RelationMetadata } from '$lib/stores/schemaStore';
	import { Network, DataSet } from 'vis-network/standalone';
	import SqlEditor from './SqlEditor.svelte';

	interface FilterCondition {
		column: string;
		operator: string;
		value: string;
		logic: 'AND' | 'OR';
	}

	interface SortConfig {
		column: string;
		direction: 'ASC' | 'DESC';
	}

	interface BuilderNode {
		id: string;
		label: string;
		tableName: string;
		selectedColumns: string[];
		filters: FilterCondition[];
		x?: number;
		y?: number;
	}

	interface BuilderEdge {
		id: string;
		from: string;
		to: string;
		label: string;
		joinType: string;
		condition: string;
	}

	let { onSendToEditor, onCancel } = $props<{
		onSendToEditor: (sql: string) => void;
		onCancel: () => void;
	}>();

	let container = $state<HTMLElement>();
	let network: Network | null = null;
	const nodesDataSet = new DataSet<BuilderNode>([]);
	const edgesDataSet = new DataSet<BuilderEdge>([]);
	let generatedSql = $state('');
	let warning = $state('');
	let selectedEdgeId = $state<string | null>(null);
	let selectedNodeId = $state<string | null>(null);
	let limit = $state<number | null>(null);
	let sorts = $state<SortConfig[]>([]);

	const joinTypes = ['INNER JOIN', 'LEFT JOIN', 'RIGHT JOIN', 'FULL JOIN'];
	const operators = ['=', '>', '<', '>=', '<=', 'LIKE', 'IN', '!='];

	// Reactive subscription to schema store
	let schemaInfo = $state<{ metadata: SchemaMetadata; relations: RelationMetadata[] }>({ 
		metadata: {}, 
		relations: [] 
	});

	const unsubscribe = schemaStore.subscribe(s => {
		schemaInfo.metadata = s.metadata;
		schemaInfo.relations = s.relations || [];
	});

	onDestroy(() => unsubscribe());

	onMount(() => {
		// Ensure schema is fetched if not already loaded (useful for direct page hits / refresh)
		if (Object.keys(schemaInfo.metadata).length === 0) {
			schemaStore.fetchSchema();
		}

		if (container) {
			const options: any = {
				nodes: {
					shape: 'box',
					margin: 10,
					font: { face: 'Outfit', size: 14, color: '#f8fafc' },
					color: {
						border: '#475569',
						background: '#1e293b',
						highlight: { border: '#6366f1', background: '#312e81' }
					},
					borderWidth: 2,
					shadow: true
				},
				edges: {
					arrows: 'none',
					color: { color: '#64748b', highlight: '#6366f1' },
					width: 2,
					font: { 
						face: 'Outfit', 
						size: 10, 
						align: 'middle', 
						color: '#94a3b8', 
						strokeWidth: 0, 
						background: '#0f172a' 
					},
					smooth: { 
						enabled: true,
						type: 'cubicBezier', 
						roundness: 0.5 
					}
				},
				physics: {
					enabled: true,
					solver: 'repulsion',
					repulsion: { nodeDistance: 200, springLength: 150 }
				},
					interaction: {
						hover: true,
						multiselect: false,
						navigationButtons: false
					}
			};

			network = new Network(container, { nodes: nodesDataSet, edges: edgesDataSet }, options);

			network.on('selectNode', (params) => {
				selectedNodeId = (params.nodes[0] as string) || null;
				selectedEdgeId = null;
			});

			network.on('deselectNode', () => {
				selectedNodeId = null;
			});

			network.on('selectEdge', (params) => {
				selectedEdgeId = (params.edges[0] as string) || null;
				selectedNodeId = null;
			});

			network.on('deselectEdge', () => {
				selectedEdgeId = null;
			});

			// Manual connection logic
			network.on('dragEnd', (params) => {
				if (params.nodes.length === 0 && params.edges.length === 0) return;
				generateSQL();
			});
		}
	});

	function addTableToCanvas(tableName: string) {
		const id = `node_${Date.now()}_${tableName}`;
		nodesDataSet.add({
			id,
			label: tableName,
			tableName: tableName,
			selectedColumns: [],
			filters: [],
			// Position randomly or near center
			x: Math.random() * 200 - 100,
			y: Math.random() * 200 - 100
		});
		generateSQL();
	}

	function connectTables(fromId: string, toId: string) {
		const fromNode = nodesDataSet.get(fromId);
		const toNode = nodesDataSet.get(toId);
		if (!fromNode || !toNode || fromId === toId) return;

		// Check if already connected
		const existing = edgesDataSet.get({
			filter: (e) => (e.from === fromId && e.to === toId) || (e.from === toId && e.to === fromId)
		});
		if (existing && existing.length > 0) return;

		// Suggest join condition based on relations
		const rel = schemaInfo.relations.find(r => 
			(r.source_table === fromNode.tableName && r.target_table === toNode.tableName) ||
			(r.source_table === toNode.tableName && r.target_table === fromNode.tableName)
		);

		let condition = '';
		if (rel) {
			condition = `${rel.source_table}.${rel.source_column} = ${rel.target_table}.${rel.target_column}`;
		} else {
			// Try to find matching column names
			const fromCols = (schemaInfo.metadata[fromNode.tableName] as string[]) || [];
			const toCols = (schemaInfo.metadata[toNode.tableName] as string[]) || [];
			const common = fromCols.find(c => toCols.includes(c) && (c.endsWith('_id') || c === 'id'));
			if (common) {
				condition = `${fromNode.tableName}.${common} = ${toNode.tableName}.${common}`;
			} else {
				condition = '/* Add Join Condition */';
			}
		}

		edgesDataSet.add({
			id: `edge_${Date.now()}`,
			from: fromId,
			to: toId,
			label: 'INNER JOIN',
			joinType: 'INNER JOIN',
			condition: condition
		});
		generateSQL();
	}

	// For the UI to detect drag-overs
	function handleDrop(e: DragEvent) {
		e.preventDefault();
		const tableName = e.dataTransfer?.getData('tableName');
		if (tableName) {
			addTableToCanvas(tableName);
		}
	}

	function generateSQL() {
		const nodes = nodesDataSet.get();
		const edges = edgesDataSet.get();

		if (nodes.length === 0) {
			generatedSql = '';
			warning = '';
			return;
		}

		if (nodes.length > 10) {
			warning = 'Complex query: More than 10 tables may impact database performance.';
		} else {
			warning = '';
		}

		const stripSchema = (name: string) => name.includes('.') ? name.split('.').pop() : name;

		// 1. SELECT Clause
		let selectParts: string[] = [];
		nodes.forEach(node => {
			const shortName = stripSchema(node.tableName);
			if (node.selectedColumns && node.selectedColumns.length > 0) {
				node.selectedColumns.forEach(col => {
					selectParts.push(`${shortName}.${col}`);
				});
			}
		});

		let selectClause = selectParts.length > 0 ? `SELECT ${selectParts.join(', ')}` : 'SELECT *';

		// 2. FROM & JOIN Clauses
		const baseTable = nodes[0].tableName;
		let fromClause = `FROM ${nodes.length > 1 ? baseTable : stripSchema(baseTable)}`;
		
		const joinedNodeIds = new Set([nodes[0].id]);
		const pendingEdges = [...edges];
		let joinClauses = '';

		let addedInLoop = true;
		while (addedInLoop && pendingEdges.length > 0) {
			addedInLoop = false;
			for (let i = 0; i < pendingEdges.length; i++) {
				const edge = pendingEdges[i];
				let targetNodeId = null;
				if (joinedNodeIds.has(edge.from)) targetNodeId = edge.to;
				else if (joinedNodeIds.has(edge.to)) targetNodeId = edge.from;

				if (targetNodeId && !joinedNodeIds.has(targetNodeId)) {
					const targetNode = nodesDataSet.get(targetNodeId);
					if (targetNode) {
						const shortName = stripSchema(targetNode.tableName);
						joinClauses += `\n${edge.joinType} ${shortName} ON ${edge.condition}`;
						joinedNodeIds.add(targetNodeId);
						pendingEdges.splice(i, 1);
						addedInLoop = true;
						break;
					}
				}
			}
		}

		// Disconnected tables -> CROSS JOIN
		if (joinedNodeIds.size < nodes.length) {
			nodes.forEach(n => {
				if (!joinedNodeIds.has(n.id)) {
					const shortName = stripSchema(n.tableName);
					joinClauses += `\nCROSS JOIN ${shortName}`;
				}
			});
			warning = 'Incomplete query: Some tables are not connected (causing Cartesian products).';
		}

		// 3. WHERE Clause
		let whereParts: string[] = [];
		nodes.forEach(node => {
			const shortName = stripSchema(node.tableName);
			if (node.filters && node.filters.length > 0) {
				node.filters.forEach((f) => {
					if (!f.value || f.value.trim() === '') return; // Skip empty filters
					
					const prefix = (whereParts.length > 0) ? ` ${f.logic} ` : '';
					const value = isNaN(Number(f.value)) ? `'${f.value}'` : f.value;
					whereParts.push(`${prefix}${shortName}.${f.column} ${f.operator} ${value}`);
				});
			}
		});
		let whereClause = whereParts.length > 0 ? `\nWHERE ${whereParts.join('')}` : '';

		// 4. ORDER BY
		let orderClause = '';
		if (sorts.length > 0) {
			const sortStrings = sorts.map(s => `${s.column} ${s.direction}`);
			orderClause = `\nORDER BY ${sortStrings.join(', ')}`;
		}

		// 5. LIMIT
		let limitClause = limit ? `\nLIMIT ${limit}` : '';

		generatedSql = `${selectClause}\n${fromClause}${joinClauses}${whereClause}${orderClause}${limitClause}`;
	}

	function toggleColumn(nodeId: string, col: string) {
		const node = nodesDataSet.get(nodeId);
		if (!node) return;
		
		const cols = node.selectedColumns.includes(col)
			? node.selectedColumns.filter(c => c !== col)
			: [...node.selectedColumns, col];
			
		nodesDataSet.update({ id: nodeId, selectedColumns: cols });
		generateSQL();
	}

	function addFilter(nodeId: string) {
		const node = nodesDataSet.get(nodeId);
		if (!node) return;
		
		const newFilter: FilterCondition = {
			column: schemaInfo.metadata[node.tableName]?.[0] || '',
			operator: '=',
			value: '',
			logic: 'AND'
		};
		
		nodesDataSet.update({ id: nodeId, filters: [...node.filters, newFilter] });
		generateSQL();
	}

	function removeFilter(nodeId: string, index: number) {
		const node = nodesDataSet.get(nodeId);
		if (!node) return;
		
		const filters = node.filters.filter((_, i) => i !== index);
		nodesDataSet.update({ id: nodeId, filters });
		generateSQL();
	}

	function updateFilter(nodeId: string, index: number, field: keyof FilterCondition, value: string) {
		const node = nodesDataSet.get(nodeId);
		if (!node) return;
		
		const filters = [...node.filters];
		(filters[index] as any)[field] = value;
		nodesDataSet.update({ id: nodeId, filters });
		generateSQL();
	}

	function resetQuery() {
		nodesDataSet.clear();
		edgesDataSet.clear();
		selectedNodeId = null;
		selectedEdgeId = null;
		limit = null;
		sorts = [];
		generateSQL();
	}


	function updateJoinType(type: string) {
		if (selectedEdgeId) {
			edgesDataSet.update({ id: selectedEdgeId, label: type, joinType: type });
			generateSQL();
		}
	}

	function removeSelected() {
		const selectedNodes = network?.getSelectedNodes() || [];
		const selectedEdges = network?.getSelectedEdges() || [];

		if (selectedNodes.length > 0) {
			nodesDataSet.remove(selectedNodes);
			if (selectedNodeId && selectedNodes.includes(selectedNodeId)) selectedNodeId = null;
		}
		if (selectedEdges.length > 0) {
			edgesDataSet.remove(selectedEdges);
			if (selectedEdgeId && selectedEdges.includes(selectedEdgeId)) selectedEdgeId = null;
		}
		generateSQL();
	}

	function handleKeydown(e: KeyboardEvent, tableName: string) {
		if (e.key === 'Enter' || e.key === ' ') {
			e.preventDefault();
			addTableToCanvas(tableName);
		}
	}
</script>

<div class="flex flex-col h-full bg-slate-950/20 rounded-[2.5rem] border border-slate-200/60 dark:border-slate-800 overflow-hidden backdrop-blur-xl animate-in zoom-in-95 duration-500">
	<!-- Header -->
	<div class="px-8 py-5 border-b border-slate-200/60 dark:border-slate-800 flex items-center justify-between bg-white/40 dark:bg-slate-900/40">
		<div class="flex items-center gap-4">
			<div class="w-10 h-10 rounded-xl bg-indigo-500/10 flex items-center justify-center text-indigo-500 border border-indigo-500/10">
				<svg class="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2.5" d="M11 4a2 2 0 114 0v1a1 1 0 001 1h3a1 1 0 011 1v3a1 1 0 01-1 1h-1a2 2 0 100 4h1a1 1 0 011 1v3a1 1 0 01-1 1h-3a1 1 0 00-1 1v1a2 2 0 11-4 0v-1a1 1 0 00-1-1H7a1 1 0 01-1-1v-3a1 1 0 00-1-1H4a2 2 0 110-4h1a1 1 0 001-1V7a1 1 0 011-1h3a1 1 0 001-1V4z"></path></svg>
			</div>
			<div>
				<h2 class="text-xl font-black text-slate-900 dark:text-white uppercase italic tracking-tighter">Visual Query Builder</h2>
				<p class="text-[9px] font-black text-slate-500 uppercase tracking-widest mt-0.5">Drag tables to model complex joins</p>
			</div>
		</div>
		<div class="flex items-center gap-3">
			<button 
				onclick={onCancel}
				class="px-4 py-2.5 rounded-xl border border-slate-200 dark:border-slate-800 text-slate-500 hover:bg-slate-50 dark:hover:bg-slate-800 text-[10px] font-black uppercase tracking-widest transition-all"
			>
				Cancel
			</button>
			<button 
				onclick={() => onSendToEditor(generatedSql)}
				disabled={!generatedSql || nodesDataSet.length === 0}
				class="px-6 py-2.5 rounded-xl bg-indigo-600 hover:bg-indigo-500 text-white text-[10px] font-black uppercase tracking-widest transition-all shadow-lg shadow-indigo-500/20 disabled:opacity-50 active:scale-95"
			>
				Send to Editor
			</button>
		</div>
	</div>

	<div class="flex-1 flex min-h-0 relative">
		<!-- Impact Analysis Modal Overlay -->

		<!-- Sidebar: Tables -->
		<div class="w-64 border-r border-slate-200/60 dark:border-slate-800 flex flex-col bg-slate-50/50 dark:bg-slate-950/20">
			<div class="p-5 border-b border-slate-200/60 dark:border-slate-800">
				<span class="text-[9px] font-black text-slate-400 uppercase tracking-widest">Table Registry</span>
			</div>
			<div class="flex-1 overflow-y-auto p-3 space-y-1 custom-scrollbar">
				{#each Object.keys(schemaInfo.metadata) as tableName}
					<button 
						class="w-full text-left px-3 py-2.5 rounded-lg bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 hover:border-indigo-500/50 cursor-grab active:cursor-grabbing text-[11px] font-bold text-slate-600 dark:text-slate-300 transition-all select-none group"
						draggable="true"
						ondragstart={(e) => e.dataTransfer?.setData('tableName', tableName)}
						onclick={() => addTableToCanvas(tableName)}
						onkeydown={(e) => handleKeydown(e, tableName)}
					>
						<div class="flex items-center justify-between">
							<span class="truncate">{tableName}</span>
							<svg class="w-3.5 h-3.5 text-slate-400 opacity-0 group-hover:opacity-100 transition-opacity" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2.5" d="M12 4v16m8-8H4"></path></svg>
						</div>
					</button>
				{/each}
			</div>
		</div>

		<!-- Canvas Area -->
		<div 
			class="flex-1 relative bg-slate-100/30 dark:bg-slate-950/20" 
			ondrop={handleDrop} 
			ondragover={(e) => e.preventDefault()}
			role="application"
			aria-label="Query modeling canvas"
		>
			<div bind:this={container} class="w-full h-full focus:outline-none"></div>
			
			<!-- Canvas Controls Overlay -->
			<div class="absolute bottom-6 left-6 flex items-center gap-2">
				<button 
					onclick={removeSelected}
					class="w-10 h-10 rounded-xl bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 flex items-center justify-center text-rose-500 hover:bg-rose-500 hover:text-white transition-all shadow-xl"
					title="Delete selected item"
				>
					<svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2.5" d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16"></path></svg>
				</button>
				<button 
					onclick={() => network?.fit()}
					class="w-10 h-10 rounded-xl bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 flex items-center justify-center text-slate-500 hover:text-indigo-500 transition-all shadow-xl"
					title="Fit view"
				>
					<svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2.5" d="M4 8V4m0 0h4M4 4l5 5m11-1V4m0 0h-4m4 0l-5 5M4 16v4m0 0h4m-4 0l5-5m11 5l-5-5m5 5v-4m0 4h-4"></path></svg>
				</button>
			</div>

			<!-- Dynamic Connection Overlay -->
			<div class="absolute top-6 left-6 flex items-center gap-4">
				<div class="px-4 py-2 bg-indigo-500/10 border border-indigo-500/20 text-indigo-500 text-[10px] font-black uppercase tracking-[0.2em] rounded-lg backdrop-blur-md">
					Draw edges between tables to join them
				</div>
			</div>
		</div>

		<!-- Contextual Sidebar -->
		<div class="w-[450px] border-l border-slate-200/60 dark:border-slate-800 flex flex-col bg-slate-900/20 overflow-hidden">
			{#if selectedNodeId}
				{@const node = nodesDataSet.get(selectedNodeId)}
				{#if node}
					<div class="flex-1 flex flex-col min-h-0 animate-in slide-in-from-right duration-300">
						<div class="p-6 border-b border-slate-200 dark:border-slate-800 bg-white/40 dark:bg-slate-900/40">
							<div class="flex items-center justify-between mb-2">
								<span class="text-[9px] font-black text-indigo-500 uppercase tracking-widest">Table Configuration</span>
								<button onclick={() => selectedNodeId = null} class="text-[9px] font-black text-slate-500 hover:text-white uppercase tracking-widest transition-colors">Close</button>
							</div>
							<h3 class="text-xl font-black text-slate-900 dark:text-white uppercase italic tracking-tighter truncate">{node.tableName}</h3>
						</div>

						<div class="flex-1 overflow-y-auto p-6 space-y-8 custom-scrollbar">
							<!-- Column Selection -->
							<section>
								<div class="flex items-center justify-between mb-4">
									<span class="text-[10px] font-black text-slate-400 uppercase tracking-widest">Selected Columns</span>
									<span class="text-[9px] font-bold text-slate-500">{node.selectedColumns.length || 'All'} selected</span>
								</div>
								<div class="grid grid-cols-1 gap-1">
									{#each (schemaInfo.metadata[node.tableName] || []) as col}
										<button 
											onclick={() => toggleColumn(node.id, col)}
											class="w-full flex items-center justify-between px-3 py-2 rounded-lg border transition-all {node.selectedColumns.includes(col) ? 'bg-indigo-600 border-indigo-500 text-white shadow-lg' : 'bg-white dark:bg-slate-900 border-slate-200 dark:border-slate-800 text-slate-600 dark:text-slate-400 hover:border-indigo-500/50'}"
										>
											<span class="text-[11px] font-bold">{col}</span>
											{#if node.selectedColumns.includes(col)}
												<svg class="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="3" d="M5 13l4 4L19 7"></path></svg>
											{/if}
										</button>
									{/each}
								</div>
							</section>

							<!-- WHERE Builder -->
							<section>
								<div class="flex items-center justify-between mb-4">
									<span class="text-[10px] font-black text-slate-400 uppercase tracking-widest">Where Filters</span>
									<button 
										onclick={() => addFilter(node.id)}
										class="px-2 py-1 rounded-md bg-indigo-500/10 text-indigo-500 border border-indigo-500/20 text-[9px] font-black hover:bg-indigo-500 hover:text-white transition-all uppercase tracking-widest"
									>
										+ Add Filter
									</button>
								</div>
								<div class="space-y-3">
									{#each node.filters as filter, idx}
										<div class="p-4 rounded-2xl bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 relative group animate-in zoom-in-95 duration-200">
											<button 
												onclick={() => removeFilter(node.id, idx)}
												class="absolute -top-2 -right-2 w-6 h-6 rounded-full bg-rose-500 text-white flex items-center justify-center opacity-0 group-hover:opacity-100 transition-opacity shadow-lg"
											>
												<svg class="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="3" d="M6 18L18 6M6 6l12 12"></path></svg>
											</button>
											<div class="flex flex-col gap-3">
												<div class="grid grid-cols-2 gap-2">
													<select 
														onchange={(e) => updateFilter(node.id, idx, 'column', (e.target as HTMLSelectElement).value)}
														class="bg-slate-50 dark:bg-slate-800 border-none rounded-xl text-[10px] font-bold p-2 focus:ring-1 focus:ring-indigo-500"
													>
														{#each (schemaInfo.metadata[node.tableName] || []) as col}
															<option value={col} selected={filter.column === col}>{col}</option>
														{/each}
													</select>
													<select 
														onchange={(e) => updateFilter(node.id, idx, 'operator', (e.target as HTMLSelectElement).value)}
														class="bg-slate-50 dark:bg-slate-800 border-none rounded-xl text-[10px] font-bold p-2 focus:ring-1 focus:ring-indigo-500"
													>
														{#each operators as op}
															<option value={op} selected={filter.operator === op}>{op}</option>
														{/each}
													</select>
												</div>
												<input 
													type="text"
													placeholder="Value..."
													value={filter.value}
													oninput={(e) => updateFilter(node.id, idx, 'value', (e.target as HTMLInputElement).value)}
													class="w-full bg-slate-50 dark:bg-slate-800 border-none rounded-xl text-[10px] font-bold p-2 focus:ring-1 focus:ring-indigo-500"
												/>
												{#if idx > 0}
													<select 
														onchange={(e) => updateFilter(node.id, idx, 'logic', (e.target as any).value)}
														class="bg-indigo-500/10 text-indigo-500 border-none rounded-lg text-[9px] font-black p-1 uppercase tracking-widest cursor-pointer"
													>
														<option value="AND" selected={filter.logic === 'AND'}>AND</option>
														<option value="OR" selected={filter.logic === 'OR'}>OR</option>
													</select>
												{/if}
											</div>
										</div>
									{/each}
								</div>
							</section>
						</div>
					</div>
				{/if}
			{:else if selectedEdgeId}
				<div class="flex-1 flex flex-col min-h-0 animate-in slide-in-from-right duration-300">
					<div class="p-6 border-b border-slate-200 dark:border-slate-800 bg-white/40 dark:bg-slate-900/40">
						<span class="text-[9px] font-black text-indigo-500 uppercase tracking-widest block mb-2">Join Configuration</span>
						<h3 class="text-xl font-black text-slate-900 dark:text-white uppercase italic tracking-tighter truncate">Edge Configuration</h3>
					</div>
					<div class="p-6">
						<span class="text-[10px] text-slate-400 block mb-3 font-bold uppercase tracking-widest">Join Type</span>
						<div class="grid grid-cols-1 gap-2">
							{#each joinTypes as type}
								<button 
									onclick={() => updateJoinType(type)}
									class="text-left px-4 py-3 rounded-xl text-xs font-bold transition-all {edgesDataSet.get(selectedEdgeId)?.joinType === type ? 'bg-indigo-600 text-white shadow-lg' : 'bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 text-slate-600 dark:text-slate-400 hover:border-indigo-500/50 hover:bg-slate-50'}"
								>
									{type}
								</button>
							{/each}
						</div>
					</div>
				</div>
			{:else}
				<div class="flex-1 flex flex-col min-h-0">
					<div class="p-5 border-b border-slate-200/60 dark:border-slate-800 flex items-center justify-between bg-white/40 dark:bg-slate-900/40">
						<span class="text-[9px] font-black text-slate-400 uppercase tracking-widest">Live Query Preview</span>
						{#if warning}
							<div class="flex items-center gap-1.5 text-[9px] font-black text-amber-500 bg-amber-500/10 px-2 py-0.5 rounded-md border border-amber-500/20 animate-pulse uppercase tracking-widest">
								<svg class="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="3" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z"></path></svg>
								Warning
							</div>
						{/if}
					</div>
					<div class="flex-1 p-6 flex flex-col min-h-0 bg-slate-950/20 overflow-y-auto custom-scrollbar">
						<div class="shrink-0 aspect-[4/3] min-h-[300px] mb-8 rounded-[1.5rem] border border-slate-800/80 bg-slate-900/50 overflow-hidden shadow-inner flex flex-col">
							<SqlEditor value={generatedSql} readOnly={true} />
						</div>

						<section class="space-y-6">
							<!-- ORDER & LIMIT -->
							<div>
								<span class="text-[10px] font-black text-slate-400 uppercase tracking-widest block mb-4">Query Modifiers</span>
								<div class="space-y-4">
									<div class="flex flex-col gap-1.5">
										<label class="text-[9px] font-black text-slate-500 uppercase tracking-widest pl-1" for="query-limit">Limit</label>
										<input 
											id="query-limit"
											type="number" 
											placeholder="No limit"
											value={limit}
											oninput={(e) => { limit = (e.currentTarget as HTMLInputElement).valueAsNumber || null; generateSQL(); }}
											class="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-xl p-3 text-xs font-bold focus:ring-2 focus:ring-indigo-500/50 transition-all shadow-sm"
										/>
									</div>

									<div class="flex flex-col gap-3">
										<div class="flex items-center justify-between">
											<label class="text-[9px] font-black text-slate-500 uppercase tracking-widest pl-1">Order By</label>
											<button 
												onclick={() => { sorts = [...sorts, { column: '', direction: 'ASC' }]; generateSQL(); }}
												class="text-[9px] font-black text-indigo-500 hover:text-indigo-400 uppercase tracking-widest"
											>
												+ Add Sort
											</button>
										</div>
										<div class="space-y-2">
											{#each sorts as sort, idx}
												<div class="flex items-center gap-2 animate-in slide-in-from-right-2 duration-200">
													<input 
														type="text" 
														placeholder="column..."
														value={sort.column}
														oninput={(e) => { sorts[idx].column = (e.currentTarget as HTMLInputElement).value; generateSQL(); }}
														class="flex-1 bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-lg p-2 text-[10px] font-bold"
													/>
													<select 
														onchange={(e) => { sorts[idx].direction = (e.target as any).value; generateSQL(); }}
														class="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-lg p-2 text-[10px] font-bold"
													>
														<option value="ASC" selected={sort.direction === 'ASC'}>ASC</option>
														<option value="DESC" selected={sort.direction === 'DESC'}>DESC</option>
													</select>
													<button 
														onclick={() => { sorts = sorts.filter((_, i) => i !== idx); generateSQL(); }}
														class="w-8 h-8 rounded-lg bg-rose-500/10 text-rose-500 flex items-center justify-center hover:bg-rose-500 hover:text-white transition-all"
													>
														<svg class="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="3" d="M6 18L18 6M6 6l12 12"></path></svg>
													</button>
												</div>
											{/each}
										</div>
									</div>
								</div>
							</div>

							{#if warning}
								<div class="p-4 rounded-2xl bg-amber-500/5 border border-amber-500/20">
									<p class="text-[10px] text-amber-500 font-bold tracking-tight leading-relaxed">
										{warning}
									</p>
								</div>
							{/if}
						</section>
					</div>
				</div>
			{/if}
		</div>
	</div>
</div>

<style>
	:global(.custom-scrollbar::-webkit-scrollbar) {
		width: 4px;
	}
	:global(.custom-scrollbar::-webkit-scrollbar-track) {
		background: transparent;
	}
	:global(.custom-scrollbar::-webkit-scrollbar-thumb) {
		background: rgba(148, 163, 184, 0.2);
		border-radius: 10px;
	}
	:global(.custom-scrollbar::-webkit-scrollbar-thumb:hover) {
		background: rgba(148, 163, 184, 0.4);
	}
</style>
