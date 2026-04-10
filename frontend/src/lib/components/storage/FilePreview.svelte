<script lang="ts">
	import { fade, slide } from 'svelte/transition';
	import SqlEditor from '$lib/components/SqlEditor.svelte';
	import Button from '$lib/components/common/Button.svelte';
	import Badge from '$lib/components/common/Badge.svelte';
	import Card from '$lib/components/common/Card.svelte';

	let { open = false, onClose, file, sourceId, bucketName } = $props();

	let content = $state(null);
	let loading = $state(false);
	let downloading = $state(false);
	let error = $state(null);

	$effect(() => {
		if (open && file) {
			const type = file.type;
			if (type.includes('json') || type.includes('text') || file.name.endsWith('.log')) {
				fetchContent();
			}
		} else {
			content = null;
			error = null;
		}
	});

	async function fetchContent() {
		loading = true;
		error = null;
		try {
			// Using raw name for the path parameter to avoid double encoding issues with FastAPI path capture
			const res = await fetch(`http://localhost:8000/storage/${sourceId}/buckets/${bucketName}/preview/${file.name}`);
			if (res.ok) {
				const text = await res.text();
				if (file.type.includes('json')) {
					try {
						content = JSON.stringify(JSON.parse(text), null, 2);
					} catch {
						content = text;
					}
				} else {
					content = text;
				}
			} else {
				error = "Failed to load content";
			}
		} catch (err) {
			error = "Error fetching preview";
		} finally {
			loading = false;
		}
	}

	async function downloadFileWithPicker() {
		downloading = true;
		try {
			const res = await fetch(`http://localhost:8000/storage/${sourceId}/buckets/${encodeURIComponent(bucketName)}/download/${encodeURIComponent(file.name)}`);
			if (!res.ok) throw new Error("Download failed");
			const blob = await res.blob();

			if (window.showSaveFilePicker) {
				try {
					const fileHandle = await window.showSaveFilePicker({
						suggestedName: file.name,
					});
					const writable = await fileHandle.createWritable();
					await writable.write(blob);
					await writable.close();
				} catch (err: any) {
					if (err.name !== 'AbortError') throw err;
				}
			} else {
				const url = window.URL.createObjectURL(blob);
				const a = document.createElement('a');
				a.href = url;
				a.download = file.name;
				document.body.appendChild(a);
				a.click();
				window.URL.revokeObjectURL(url);
				document.body.removeChild(a);
			}
		} catch (err) {
			alert("Failed to download: " + err);
		} finally {
			downloading = false;
		}
	}

	function getPreviewUrl() {
		return `http://localhost:8000/storage/${sourceId}/buckets/${encodeURIComponent(bucketName)}/preview/${file.name}`;
	}
</script>

{#if open}
	<div class="fixed inset-0 bg-slate-950/90 backdrop-blur-md z-[100] flex items-center justify-center p-4 md:p-10" transition:fade>
		<Card padding="p-0" class="w-full max-w-5xl h-full flex flex-col">
			<!-- Header -->
			<div class="p-6 md:p-8 border-b border-slate-100 dark:border-slate-800 flex items-center justify-between bg-white dark:bg-slate-900">
				<div class="flex items-center gap-4">
					<div class="w-14 h-14 bg-indigo-500/10 rounded-2xl flex items-center justify-center text-3xl shadow-inner border border-indigo-500/20">
						{#if file.type.includes('image')}
							🖼️
						{:else if file.type.includes('json')}
							📄
						{:else if file.name.endsWith('.log')}
							📝
						{:else}
							📁
						{/if}
					</div>
					<div>
						<h2 class="text-2xl font-black text-slate-900 dark:text-white truncate max-w-md uppercase italic tracking-tighter">{file.name}</h2>
						<div class="flex items-center gap-2 mt-2">
							<Badge text={file.type} variant="premium" />
							<Badge text={`${(file.size / 1024).toFixed(2)} KB`} variant="neutral" />
						</div>
					</div>
				</div>
				<button 
					onclick={onClose}
					class="w-12 h-12 rounded-full border border-slate-200 dark:border-slate-800 hover:bg-slate-100 dark:hover:bg-slate-900 flex items-center justify-center text-xl transition-all hover:rotate-90 shadow-sm"
				>
					✕
				</button>
			</div>

			<!-- Body -->
			<div class="flex-1 overflow-hidden bg-slate-50 dark:bg-slate-950 p-4 md:p-8">
				{#if loading}
					<div class="h-full flex flex-col items-center justify-center">
						<div class="w-12 h-12 border-4 border-indigo-500 border-t-transparent rounded-full animate-spin"></div>
						<p class="mt-4 text-[10px] font-black text-slate-500 uppercase tracking-[0.2em] animate-pulse">Synchronizing Data Buffer...</p>
					</div>
				{:else if error}
					<div class="h-full flex flex-col items-center justify-center text-center">
						<div class="text-6xl mb-6">⚠️</div>
						<h3 class="text-xl font-black text-slate-900 dark:text-white uppercase">Vault Access Interrupted</h3>
						<p class="text-slate-500 font-bold mt-2 uppercase tracking-widest text-[10px]">{error}</p>
					</div>
				{:else if file.type.includes('image')}
					<div class="h-full flex items-center justify-center p-4">
						<img 
							src={getPreviewUrl()} 
							alt={file.name} 
							class="max-w-full max-h-full object-contain rounded-3xl shadow-2xl border-8 border-white dark:border-slate-800 bg-white dark:bg-slate-900 transform transition-transform duration-500 hover:scale-[1.02]"
						/>
					</div>
				{:else if content}
					<div class="h-full flex flex-col">
						<SqlEditor 
							bind:value={content} 
							readOnly={true} 
							lang={file.type.includes('json') ? 'json' : 'sql'}
							height="100%"
							autocomplete={false}
						/>
					</div>
				{:else}
					<div class="h-full flex flex-col items-center justify-center text-center grayscale opacity-50">
						<div class="text-8xl mb-8">🚫</div>
						<h3 class="text-2xl font-black text-slate-900 dark:text-white uppercase tracking-tighter">Preview Void</h3>
						<p class="text-slate-500 mt-2 max-w-sm font-bold uppercase tracking-widest text-[10px]">Architectural constraints prevent real-time rendering of this buffer type.</p>
					</div>
				{/if}
			</div>

			<!-- Footer -->
			<div class="p-8 bg-white dark:bg-slate-900 border-t border-slate-100 dark:border-slate-800 flex justify-end gap-3">
				<Button variant="secondary" onclick={onClose}>Close Portal</Button>
				<Button 
					variant="indigo" 
					onclick={downloadFileWithPicker} 
					loading={downloading}
					class="px-8 shadow-lg shadow-indigo-600/20"
				>
					{downloading ? 'Syncing...' : '⬇️ Download Buffer'}
				</Button>
			</div>
		</Card>
	</div>
{/if}

