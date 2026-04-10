<script lang="ts">
	import { fade, scale } from 'svelte/transition';
	import Button from './Button.svelte';
	import Card from './Card.svelte';

	let { 
		open = false, 
		title = "Confirm Action", 
		message = "Are you sure you want to proceed?", 
		confirmText = "Confirm", 
		cancelText = "Cancel",
		variant = "primary",
		onConfirm, 
		onCancel 
	}: {
		open: boolean,
		title?: string,
		message?: string,
		confirmText?: string,
		cancelText?: string,
		variant?: "primary" | "danger" | "indigo" | "cyan",
		onConfirm: () => void,
		onCancel: () => void
	} = $props();

	function handleKeydown(e: KeyboardEvent) {
		if (e.key === 'Escape') onCancel();
	}
</script>

{#if open}
	<div 
		class="fixed inset-0 z-[200] flex items-center justify-center p-4 bg-slate-950/80 backdrop-blur-sm"
		transition:fade={{ duration: 200 }}
		onkeydown={handleKeydown}
		role="presentation"
	>
		<div 
			class="w-full max-w-md"
			transition:scale={{ duration: 200, start: 0.95 }}
		>
			<Card padding="p-0" class="overflow-hidden border border-slate-200 dark:border-slate-800 shadow-2xl shadow-slate-950/50">
				<div class="p-8">
					<div class="flex items-center gap-4 mb-6">
						<div class={[
							"w-12 h-12 rounded-2xl flex items-center justify-center text-2xl shadow-inner border",
							variant === 'danger' ? "bg-rose-50 dark:bg-rose-900/20 text-rose-500 border-rose-100 dark:border-rose-900/30" : "bg-indigo-50 dark:bg-indigo-900/20 text-indigo-500 border-indigo-100 dark:border-indigo-900/30"
						].join(" ")}>
							{variant === 'danger' ? '⚠️' : '🔔'}
						</div>
						<div>
							<h3 class="text-xl font-black text-slate-900 dark:text-white uppercase italic tracking-tighter leading-none">{title}</h3>
							<p class="text-[9px] font-bold text-slate-400 uppercase tracking-widest mt-2 block">DevBeast Security Layer</p>
						</div>
					</div>

					<p class="text-sm font-medium text-slate-600 dark:text-slate-400 leading-relaxed mb-8">
						{message}
					</p>

					<div class="flex items-center justify-end gap-3 pt-6 border-t border-slate-100 dark:border-slate-800">
						<Button variant="ghost" size="md" onclick={onCancel}>
							{cancelText}
						</Button>
						<Button {variant} size="md" onclick={onConfirm}>
							{confirmText}
						</Button>
					</div>
				</div>
			</Card>
		</div>
	</div>
{/if}
