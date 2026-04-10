<script lang="ts">
	let { 
		text, 
		variant = "neutral" 
	}: { 
		text: string, 
		variant?: "success" | "danger" | "warning" | "info" | "neutral" | "premium"
	} = $props();

	const variants = {
		success: "bg-emerald-500/10 text-emerald-500 border-emerald-500/20",
		danger: "bg-rose-500/10 text-rose-500 border-rose-500/20",
		warning: "bg-amber-500/10 text-amber-500 border-amber-500/20",
		info: "bg-blue-500/10 text-blue-500 border-blue-500/20",
		neutral: "bg-slate-500/10 text-slate-500 border-slate-500/20",
		premium: "bg-indigo-500/10 text-indigo-500 border-indigo-500/20"
	};
</script>

<div class="px-2.5 py-1 rounded-lg border text-[9px] font-black uppercase tracking-widest inline-flex items-center gap-1.5 transition-all {variants[variant]}">
	{#if variant === 'danger'}
		<span class="w-1 h-1 rounded-full bg-current animate-pulse"></span>
	{/if}
	{text}
</div>
