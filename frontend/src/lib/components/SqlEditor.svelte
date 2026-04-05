<script lang="ts">
	import { onMount, onDestroy } from 'svelte';
	import { EditorView, keymap, placeholder as cmPlaceholder, tooltips } from '@codemirror/view';
	import { EditorState } from '@codemirror/state';
	import { sql } from '@codemirror/lang-sql';
	import {
		autocompletion,
		type CompletionContext,
		type CompletionResult
	} from '@codemirror/autocomplete';
	import { indentWithTab } from '@codemirror/commands';
	import { schemaStore } from '$lib/stores/schemaStore';
	import { parseQueryContext } from '$lib/utils/SqlParser';

	let {
		value = $bindable(''),
		placeholder = 'SELECT * FROM users...',
		onRun = () => {},
		singleLine = false,
		autocomplete = true,
		readOnly = false,
		height = singleLine ? '64px' : '180px'
	} = $props();

	let editorContainer: HTMLElement;
	let view: EditorView;

	// 1. Completion Provider (The Core Logic)
	function customCompletions(context: CompletionContext): CompletionResult | null {
		const word = context.matchBefore(/\w*/);
		if (!word) return null;

		const query = context.state.doc.toString();
		const pos = context.pos;
		const queryContext = parseQueryContext(query, pos);
		const schema = $schemaStore.metadata;

		let options: any[] = [];

		// Helper to strip schema
		const getShortName = (name: string) => name.includes('.') ? name.split('.').pop()! : name;

		// Case 1: After a dot (e.g., "u." or "users.")
		if (queryContext.afterDot) {
			const target = queryContext.afterDot.toLowerCase();
			// Resolve alias or use direct table name
			const tableName =
				queryContext.aliases[target] ||
				(schema[target] ? target : schema[`public.${target}`] ? `public.${target}` : null);

			if (tableName && schema[tableName]) {
				options = schema[tableName].map((col) => ({
					label: col,
					type: 'property',
					detail: `📄 col from ${getShortName(tableName)}`,
					boost: 100, // Priority: Columns
					info: `📄 Column: ${col}`
				}));
			}
		}
		// Case 2: After FROM or JOIN (Suggest Tables)
		else if (queryContext.nearestKeyword === 'FROM' || queryContext.nearestKeyword === 'JOIN') {
			options = Object.keys(schema).map((table) => {
				const shortName = getShortName(table);
				return {
					label: shortName,
					type: 'class',
					detail: '🗄️ table',
					boost: 90, // Priority: Tables
					info: `🗄️ Table: ${table}`
				};
			});
		}
		// Case 3: Default Suggestions (Keywords + Tables + Columns from identified tables)
		else {
			// Add all tables
			options.push(
				...Object.keys(schema).map((table) => {
					const shortName = getShortName(table);
					return {
						label: shortName,
						type: 'class',
						detail: '🗄️ table',
						boost: 50,
						info: `🗄️ Table: ${table}`
					};
				})
			);

			// Add columns from tables already in the query (if any)
			const activeTables = Object.values(queryContext.aliases);
			activeTables.forEach((table) => {
				if (schema[table]) {
					options.push(
						...schema[table].map((col) => ({
							label: col,
							type: 'property',
							detail: `📄 col from ${getShortName(table)}`,
							boost: 60,
							info: `📄 Column: ${col}`
						}))
					);
				}
			});

			// Add basic SQL keywords
			const keywords = [
				'SELECT',
				'FROM',
				'WHERE',
				'JOIN',
				'INSERT INTO',
				'UPDATE',
				'DELETE FROM',
				'SET',
				'GROUP BY',
				'ORDER BY',
				'LIMIT',
				'OFFSET',
				'AND',
				'OR',
				'COUNT',
				'SUM',
				'AVG',
				'MIN',
				'MAX',
				'AS',
				'ON'
			];
			options.push(
				...keywords.map((kw) => ({
					label: kw,
					type: 'keyword',
					boost: 70,
					info: `⚡ SQL Keyword: ${kw}`
				}))
			);
		}

		// Filter by word and limit suggestions
		const filteredOptions = options
			.filter((opt) => opt.label.toLowerCase().includes(word.text.toLowerCase()))
			.sort((a, b) => (b.boost || 0) - (a.boost || 0))
			.slice(0, 40) // Suggestion limit
			.map((opt) => ({
				...opt,
				apply: opt.label + ' ' // Add space after selection
			}));

		return {
			from: word.from,
			options: filteredOptions,
			validFor: /^\w*$/
		};
	}

	onMount(() => {
		const extensions = [
			sql({
				schema: $schemaStore.metadata, // Built-in schema support for deep parsing
				upperCaseKeywords: true
			}),
			...(autocomplete ? [autocompletion({ override: [customCompletions] })] : []),
			keymap.of([
				indentWithTab,
				{
					key: 'Mod-Enter',
					run: () => {
						onRun();
						return true;
					}
				}
			]),
			EditorView.updateListener.of((update) => {
				if (update.docChanged) {
					value = update.state.doc.toString();
				}
			}),
			cmPlaceholder(placeholder),
			tooltips({
				parent: document.body,
				position: 'fixed'
			}),
			EditorView.theme({
				'&': {
					height,
					fontSize: '14px',
					fontFamily: "'JetBrains Mono', 'Fira Code', ui-monospace, monospace",
					backgroundColor: 'transparent'
				},
				'.cm-content': {
					padding: singleLine ? '12px 16px' : '16px',
					caretColor: '#6366f1' // Visible Indigo cursor
				},
				'&.cm-focused': {
					outline: 'none'
				},
				'&.cm-focused .cm-cursor': {
					borderLeft: '2px solid #6366f1',
					marginLeft: '-1px'
				},
				'&.cm-focused .cm-selectionBackground, .cm-selectionBackground, ::selection': {
					backgroundColor: 'rgba(99, 102, 241, 0.3) !important'
				},
				'.cm-scroller': {
					overflow: singleLine ? 'hidden' : 'auto',
					display: 'flex',
					alignItems: singleLine ? 'center' : 'flex-start',
					lineHeight: '1.6'
				},
				'.cm-placeholder': {
					color: '#64748b',
					fontStyle: 'italic'
				},
				'.cm-tooltip-autocomplete': {
					backgroundColor: '#0f172a',
					border: '1px solid #334155',
					borderRadius: '12px',
					boxShadow: '0 20px 25px -5px rgba(0, 0, 0, 0.3), 0 10px 10px -5px rgba(0, 0, 0, 0.1)',
					padding: '6px',
					overflow: 'hidden'
				},
				'.cm-completionIcon': { display: 'none' },
				'.cm-completionLabel': { color: '#f1f5f9', fontSize: '12px', fontWeight: '600' },
				'.cm-completionDetail': {
					color: '#94a3b8',
					fontSize: '10px',
					marginLeft: '8px',
					fontStyle: 'italic'
				},
				'.cm-completionInfo': {
					backgroundColor: '#1e293b',
					color: '#cbd5e1',
					border: '1px solid #334155',
					borderRadius: '8px',
					padding: '10px',
					fontSize: '11px',
					boxShadow: 'xl'
				}
			})
		];

		const startState = EditorState.create({
			doc: value,
			extensions
		});

		view = new EditorView({
			state: startState,
			parent: editorContainer
		});
	});

	onDestroy(() => {
		if (view) view.destroy();
	});

	// Sync value changes if updated externally
	$effect(() => {
		if (view && value !== view.state.doc.toString()) {
			view.dispatch({
				changes: { from: 0, to: view.state.doc.length, insert: value }
			});
		}
	});

	async function refresh() {
		await schemaStore.refresh();
	}
</script>

<div class="flex flex-col gap-2 w-full group">
	<div
		bind:this={editorContainer}
		class="w-full bg-white/5 dark:bg-slate-950/50 backdrop-blur-sm rounded-2xl border border-slate-200 dark:border-slate-800/80 overflow-hidden
		       focus-within:border-indigo-500/50 focus-within:ring-4 focus-within:ring-indigo-500/10 transition-all duration-300 shadow-sm group-hover:border-slate-300 dark:group-hover:border-slate-700
		       {singleLine ? 'flex items-center' : ''}"
	></div>
	{#if !singleLine}
		<div class="flex items-center justify-between px-2">
			<span class="text-[10px] text-slate-400 font-bold uppercase tracking-widest">
				{#if $schemaStore.loading}
					Syncing Schema...
				{:else if $schemaStore.lastUpdated}
					Synced: {new Date($schemaStore.lastUpdated).toLocaleTimeString()}
				{:else}
					Schema not synced
				{/if}
			</span>
			<button
				onclick={refresh}
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
				Refresh Schema
			</button>
		</div>
	{/if}
</div>

<style>
	:global(.cm-editor) {
		height: 100%;
	}
</style>
