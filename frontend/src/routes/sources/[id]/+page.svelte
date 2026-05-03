<script lang="ts">
	import { onMount } from 'svelte';
	import { page } from '$app/state';
	import { fade, slide } from 'svelte/transition';
	import FilePreview from '$lib/components/storage/FilePreview.svelte';
	import Button from '$lib/components/common/Button.svelte';
	import Badge from '$lib/components/common/Badge.svelte';
	import Card from '$lib/components/common/Card.svelte';
	import Modal from '$lib/components/common/Modal.svelte';

	interface Bucket {
		name: string;
	}

	interface StorageObject {
		name: string;
		type: string;
		size: number;
		last_modified: string;
	}

	const sourceId = page.params.id;
	let buckets = $state<Bucket[]>([]);
	let selectedBucket = $state<string | null>(null);
	let objects = $state<StorageObject[]>([]);
	let loadingBuckets = $state(true);
	let loadingObjects = $state(false);
	let error = $state<string | null>(null);
	let newBucketName = $state("");

	// Preview State
	let showPreview = $state(false);
	let selectedFile = $state<StorageObject | null>(null);

	// Multi-select/Actions
	let searchQuery = $state("");
	let downloadingFile = $state<string | null>(null);


	// Modal State
	let deleteBucketModal = $state({ open: false, name: "" });
	let deleteObjectModal = $state({ open: false, name: "" });

	async function fetchBuckets() {
		loadingBuckets = true;
		try {
			const res = await fetch(`http://localhost:8000/storage/${sourceId}/buckets`);
			buckets = await res.json();
			if (buckets.length > 0 && !selectedBucket) {
				selectBucket(buckets[0].name);
			}
		} catch (err) {
			error = "Failed to load buckets";
		} finally {
			loadingBuckets = false;
		}
	}

	async function selectBucket(name: string) {
		selectedBucket = name;
		fetchObjects();
	}

	async function fetchObjects() {
		if (!selectedBucket) return;
		loadingObjects = true;
		try {
			const res = await fetch(`http://localhost:8000/storage/${sourceId}/buckets/${selectedBucket}/objects`);
			objects = await res.json();
		} catch (err) {
			console.error(err);
		} finally {
			loadingObjects = false;
		}
	}

	async function createBucket() {
		if (!newBucketName) return;
		try {
			const res = await fetch(`http://localhost:8000/storage/${sourceId}/buckets`, {
				method: 'POST',
				headers: { 'Content-Type': 'application/json' },
				body: JSON.stringify({ name: newBucketName })
			});
			if (res.ok) {
				newBucketName = "";
				fetchBuckets();
			}
		} catch (err) {
			alert("Failed to create bucket");
		}
	}

	async function deleteBucket(name: string) {
		try {
			const res = await fetch(`http://localhost:8000/storage/${sourceId}/buckets/${encodeURIComponent(name)}`, { method: 'DELETE' });
			if (res.ok) {
				if (selectedBucket === name) selectedBucket = null;
				fetchBuckets();
			} else {
				const data = await res.json();
				alert("Bucket delete failed: " + (data.error || res.statusText));
			}
		} catch (err) {
			alert("Failed to delete bucket");
		} finally {
			deleteBucketModal.open = false;
		}
	}

	async function uploadFile(event: Event) {
		const target = event.target as HTMLInputElement;
		const file = target.files?.[0];
		if (!file || !selectedBucket) return;

		const formData = new FormData();
		formData.append('file', file);

		try {
			const res = await fetch(`http://localhost:8000/storage/${sourceId}/buckets/${selectedBucket}/upload`, {
				method: 'POST',
				body: formData
			});
			if (res.ok) fetchObjects();
		} catch (err) {
			alert("Upload failed");
		}
	}

	async function deleteObject(name: string) {
		try {
			if (!selectedBucket) return;
			// Using encodeURIComponent but carefully for the object key
			const res = await fetch(`http://localhost:8000/storage/${sourceId}/buckets/${encodeURIComponent(selectedBucket)}/objects/${encodeURIComponent(name)}`, {
				method: 'DELETE'
			});
			if (res.ok) {
				objects = objects.filter(obj => obj.name !== name);
				await fetchObjects(); 
			} else {
				const data = await res.json();
				alert("Delete failed: " + (data.error || res.statusText));
			}
		} catch (err) {
			alert("Failed to delete object: " + err);
		} finally {
			deleteObjectModal.open = false;
		}
	}

	function openPreview(file: any) {
		selectedFile = file;
		showPreview = true;
	}

	async function downloadFileWithPicker(bucketName: string, fileName: string) {
		downloadingFile = fileName;
		try {
			// First, fetch the file blob from the local backend presigned redirect
			const res = await fetch(`http://localhost:8000/storage/${sourceId}/buckets/${encodeURIComponent(bucketName)}/download/${encodeURIComponent(fileName)}`);
			if (!res.ok) throw new Error("Download failed");
			const blob = await res.blob();

			// Force OS Save As dialog
			if ((window as any).showSaveFilePicker) {
				try {
					const fileHandle = await (window as any).showSaveFilePicker({
						suggestedName: fileName,
					});
					const writable = await fileHandle.createWritable();
					await writable.write(blob);
					await writable.close();
				} catch (err: any) {
					// Ignore abort errors (user cancelled dialog)
					if (err.name !== 'AbortError') {
						throw err;
					}
				}
			} else {
				// Fallback if browser doesn't support the OS picker
				const url = window.URL.createObjectURL(blob);
				const a = document.createElement('a');
				a.href = url;
				a.download = fileName;
				document.body.appendChild(a);
				a.click();
				window.URL.revokeObjectURL(url);
				document.body.removeChild(a);
			}
		} catch (err) {
			alert("Failed to download file: " + err);
		} finally {
			downloadingFile = null;
		}
	}

	function formatSize(bytes: number) {
		if (bytes === 0) return '0 B';
		const k = 1024;
		const sizes = ['B', 'KB', 'MB', 'GB', 'TB'];
		const i = Math.floor(Math.log(bytes) / Math.log(k));
		return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
	}

	function formatDate(dateStr: string) {
		return new Date(dateStr).toLocaleString();
	}

	onMount(fetchBuckets);

	let filteredObjects = $derived(
		objects.filter(obj => obj.name.toLowerCase().includes(searchQuery.toLowerCase()))
	);
</script>

<div class="grid grid-cols-1 lg:grid-cols-4 gap-8 flex-1 overflow-hidden" in:fade>
	<!-- Sidebar: Buckets -->
	<aside class="lg:col-span-1 space-y-6 flex flex-col min-h-0">
		<Card padding="p-6" class="flex-1 flex flex-col overflow-hidden">
			<div class="flex items-center justify-between mb-6 pb-4 border-b border-slate-100 dark:border-slate-800 shrink-0">
				<div>
					<h2 class="text-xs font-black text-slate-400 uppercase tracking-[0.2em]">Data Vaults</h2>
					<p class="text-[9px] font-bold text-slate-500 uppercase tracking-widest mt-1">S3 Instances</p>
				</div>
				<Badge text={buckets.length.toString()} variant="neutral" />
			</div>
			
			<div class="space-y-2 flex-1 overflow-y-auto custom-scrollbar pr-2 mb-6">
				{#each buckets as bucket}
					<div 
						onclick={() => selectBucket(bucket.name)}
						onkeydown={(e) => e.key === 'Enter' && selectBucket(bucket.name)}
						role="button"
						tabindex="0"
						class={[
							"w-full flex items-center justify-between p-4 rounded-2xl transition-all group/bucket relative cursor-pointer",
							selectedBucket === bucket.name 
								? "bg-indigo-500 text-white shadow-xl shadow-indigo-500/20" 
								: "bg-slate-50 dark:bg-slate-950/50 text-slate-600 dark:text-slate-400 hover:bg-slate-100 dark:hover:bg-slate-900 border border-transparent hover:border-slate-200 dark:hover:border-slate-800"
						].join(" ")}
					>
						<div class="flex items-center gap-3">
							<span class="text-lg">🪣</span>
							<span class="text-xs font-bold truncate max-w-[120px]">{bucket.name}</span>
						</div>
						
						<button 
							onclick={(e) => { e.stopPropagation(); deleteBucketModal = { open: true, name: bucket.name }; }}
							class={[
								"p-2 rounded-lg transition-all",
								selectedBucket === bucket.name ? "hover:bg-white/20 text-white" : "hover:bg-rose-500/10 text-rose-500"
							].join(" ")}
						>
							🗑️
						</button>
					</div>
				{/each}
			</div>

			<div class="pt-6 border-t border-slate-100 dark:border-slate-800 shrink-0">
				<div class="flex gap-2">
					<input 
						bind:value={newBucketName} 
						placeholder="New Bucket..." 
						class="flex-1 bg-slate-50 dark:bg-slate-950/50 border border-slate-200 dark:border-slate-800 rounded-xl px-4 py-3 text-[10px] font-bold uppercase tracking-widest focus:outline-none focus:ring-2 focus:ring-indigo-500/50 transition-all"
					/>
					<Button onclick={createBucket} variant="indigo" size="sm" class="min-w-0 px-3">
						+
					</Button>
				</div>
			</div>
		</Card>
	</aside>

	<!-- Main content: Objects -->
	<main class="lg:col-span-3 space-y-8 flex flex-col min-h-0">
		<Card padding="p-8" class="flex-1 flex flex-col overflow-hidden relative">
			<div class="absolute -right-20 -top-20 w-64 h-64 bg-indigo-500/5 rounded-full blur-3xl pointer-events-none"></div>

			{#if selectedBucket}
				<!-- Bucket Header -->
				<div class="flex items-center justify-between mb-8 shrink-0">
					<div class="flex items-center gap-4">
						<div class="w-14 h-14 bg-indigo-50 dark:bg-indigo-900/20 rounded-2xl flex items-center justify-center text-3xl shadow-inner border border-indigo-100 dark:border-indigo-900/30">📦</div>
						<div>
							<h2 class="text-3xl font-black text-slate-900 dark:text-white uppercase tracking-tighter italic leading-none">{selectedBucket}</h2>
							<div class="flex items-center gap-2 mt-2">
								<Badge text="Bucket Active" variant="success" />
								<Badge text={`${objects.length} Objects`} variant="neutral" />
							</div>
						</div>
					</div>
					
					<div class="flex items-center gap-3">
						<Button onclick={fetchObjects} variant="secondary" size="sm" class="min-w-0 p-3">🔄</Button>
						<label class="cursor-pointer">
							<input type="file" class="hidden" onchange={uploadFile} />
							<div class="px-8 py-3 bg-indigo-600 hover:bg-indigo-500 text-white rounded-2xl font-black uppercase tracking-widest text-[10px] shadow-lg shadow-indigo-600/20 transition-all hover:-translate-y-1 active:scale-95 flex items-center gap-2 italic">
								<span>⬆️</span> Upload Buffer
							</div>
						</label>
					</div>
				</div>

				<!-- Search Bar -->
				<div class="relative w-full mb-8 shrink-0">
					<span class="absolute left-4 top-1/2 -translate-y-1/2 text-slate-400">🔍</span>
					<input 
						bind:value={searchQuery}
						placeholder="Search in {selectedBucket}..." 
						class="w-full bg-slate-50 dark:bg-slate-950 border border-slate-200 dark:border-slate-800 rounded-2xl pl-12 pr-4 py-4 text-sm font-medium focus:outline-none focus:ring-2 focus:ring-indigo-500/20 focus:border-indigo-500 transition-all dark:text-white"
					/>
				</div>

				<!-- Table Area -->
				<div class="flex-1 overflow-auto custom-scrollbar -mx-8 px-8">
					{#if loadingObjects}
						<div class="h-full flex flex-col items-center justify-center opacity-50 py-20">
							<div class="w-12 h-12 border-4 border-indigo-500 border-t-transparent rounded-full animate-spin"></div>
							<p class="mt-6 text-[10px] font-black uppercase tracking-widest text-slate-500">Indexing Vault Contents...</p>
						</div>
					{:else if filteredObjects.length === 0}
						<div class="h-full flex flex-col items-center justify-center p-20 text-center opacity-50 grayscale">
							<div class="text-6xl mb-6">🏝️</div>
							<h3 class="text-xl font-black text-slate-900 dark:text-white uppercase italic tracking-tight">Empty or No Results</h3>
							<p class="text-slate-500 mt-2 font-medium">Verify your search term or initialize the vault with a file.</p>
						</div>
					{:else}
						<table class="w-full text-left border-collapse">
							<thead class="sticky top-0 bg-white dark:bg-slate-900 z-10">
								<tr class="text-[10px] font-black text-slate-400 uppercase tracking-widest border-b border-slate-100 dark:border-slate-800">
									<th class="px-8 py-5">Identified Format / Name</th>
									<th class="px-8 py-5">Buffer Size</th>
									<th class="px-8 py-5">Media Type</th>
									<th class="px-8 py-5 text-right">Actions</th>
								</tr>
							</thead>
							<tbody class="divide-y divide-slate-50 dark:divide-slate-800">
								{#each filteredObjects as obj}
									<tr class="group hover:bg-slate-50/50 dark:hover:bg-indigo-500/5 transition-colors">
										<td class="px-8 py-5">
											<div class="flex items-center gap-4">
												<div class="w-12 h-12 bg-slate-100 dark:bg-slate-800 rounded-2xl flex items-center justify-center group-hover:bg-indigo-500/10 transition-colors shadow-inner border border-transparent group-hover:border-indigo-500/20">
													{#if obj.type.includes('image')}
														🖼️
													{:else if obj.type.includes('json')}
														📄
													{:else if obj.name.endsWith('.log')}
														📝
													{:else}
														📁
													{/if}
												</div>
												<div class="flex flex-col min-w-0">
													<div class="flex items-center gap-2">
														<span class="font-bold text-slate-800 dark:text-slate-200 truncate max-w-[280px]">{obj.name}</span>
													</div>
													<span class="text-[10px] text-slate-400 font-black uppercase tracking-widest mt-1 bg-slate-50 dark:bg-slate-800/50 self-start px-2 py-0.5 rounded-lg border border-slate-100 dark:border-slate-800">{formatDate(obj.last_modified)}</span>
												</div>
											</div>
										</td>
										<td class="px-8 py-5">
											<Badge text={formatSize(obj.size)} variant="neutral" />
										</td>
										<td class="px-8 py-5">
											<code class="text-[10px] font-black text-slate-400 font-mono italic uppercase tracking-tighter">{obj.type}</code>
										</td>
										<td class="px-8 py-5 text-right">
											<div class="flex items-center justify-end gap-2 translate-x-0">
												<Button onclick={() => openPreview(obj)} variant="ghost" size="sm" class="p-2.5 min-w-0 border border-slate-200 dark:border-slate-800" title="Quick Preview">👁️</Button>
												
												<Button 
													onclick={() => selectedBucket && downloadFileWithPicker(selectedBucket, obj.name)} 
													variant="secondary" 
													size="sm" 
													class="p-2.5 min-w-10 border border-slate-200 dark:border-slate-800"
													loading={downloadingFile === obj.name}
													title="Download"
												>
													{downloadingFile === obj.name ? '' : '⬇️'}
												</Button>

												<Button onclick={() => deleteObjectModal = { open: true, name: obj.name }} variant="ghost" size="sm" class="p-2.5 min-w-0 border border-slate-200 dark:border-slate-800 text-rose-500" title="Delete">🗑️</Button>
											</div>
										</td>
									</tr>
								{/each}
							</tbody>
						</table>
					{/if}
				</div>
			{:else}
				<div class="h-full flex flex-col items-center justify-center p-20 text-center opacity-30 grayscale">
					<div class="text-[120px] mb-12 animate-float">🛸</div>
					<h3 class="text-3xl font-black text-slate-900 dark:text-white uppercase tracking-tighter italic">Workspace Inactive</h3>
					<p class="text-slate-500 mt-4 max-w-sm font-bold uppercase tracking-widest text-xs leading-relaxed">Select a high-speed data vault from the sidebar to initialize the exploration interface.</p>
				</div>
			{/if}
		</Card>
	</main>
</div>

<!-- FILE PREVIEW MODAL -->
<FilePreview 
	open={showPreview} 
	onClose={() => { showPreview = false; selectedFile = null; }} 
	file={selectedFile} 
	sourceId={sourceId}
	bucketName={selectedBucket}
/>

<!-- MODALS -->
<Modal 
	open={deleteBucketModal.open}
	title="Delete Bucket"
	message={`Are you sure you want to permanently delete bucket '${deleteBucketModal.name}'? This action cannot be undone.`}
	confirmText="Delete Bucket"
	variant="danger"
	onConfirm={() => deleteBucket(deleteBucketModal.name)}
	onCancel={() => deleteBucketModal.open = false}
/>

<Modal 
	open={deleteObjectModal.open}
	title="Delete File"
	message={`Are you sure you want to remove '${deleteObjectModal.name}' from storage?`}
	confirmText="Confirm Removal"
	variant="danger"
	onConfirm={() => deleteObject(deleteObjectModal.name)}
	onCancel={() => deleteObjectModal.open = false}
/>

<style>
	.custom-scrollbar::-webkit-scrollbar {
		width: 6px;
	}
	.custom-scrollbar::-webkit-scrollbar-thumb {
		background: #e2e8f0;
		border-radius: 10px;
	}
	:global(.dark) .custom-scrollbar::-webkit-scrollbar-thumb {
		background: #1e293b;
	}

	@keyframes float {
		0%, 100% { transform: translateY(0); }
		50% { transform: translateY(-20px); }
	}
	.animate-float {
		animation: float 6s ease-in-out infinite;
	}
</style>
