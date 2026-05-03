<script lang="ts">
	let { 
		children, 
		onclick, 
		variant = "primary", 
		size = "md",
		loading = false,
		disabled = false,
		type = "button",
		class: className = "",
		...rest
	}: { 
		children: any,
		onclick?: (e: MouseEvent) => void,
		variant?: "primary" | "secondary" | "danger" | "ghost" | "cyan" | "indigo",
		size?: "sm" | "md" | "lg",
		loading?: boolean,
		disabled?: boolean,
		type?: "button" | "submit",
		class?: string,
		[key: string]: any
	} = $props();

	const variants = {
		primary: "bg-indigo-600 hover:bg-indigo-500 text-white shadow-indigo-600/20",
		secondary: "bg-slate-100 dark:bg-slate-800 text-slate-600 dark:text-slate-300 hover:bg-slate-200 dark:hover:bg-slate-700",
		danger: "bg-rose-500 hover:bg-rose-400 text-white shadow-rose-500/20",
		ghost: "bg-transparent text-slate-500 hover:bg-slate-100 dark:hover:bg-slate-800",
		cyan: "bg-cyan-500 hover:bg-cyan-400 text-white shadow-cyan-500/20",
		indigo: "bg-indigo-500 hover:bg-indigo-400 text-white shadow-indigo-500/20"
	};

	const sizes = {
		sm: "px-4 py-2 text-[9px]",
		md: "px-6 py-3 text-[10px]",
		lg: "px-8 py-4 text-xs"
	};
</script>

<button 
	{type}
	{onclick}
	{...rest}
	disabled={disabled || loading}
	class="rounded-xl font-black italic uppercase tracking-widest transition-all hover:-translate-y-0.5 active:scale-95 disabled:opacity-50 disabled:hover:translate-y-0 disabled:active:scale-100 flex items-center justify-center gap-2 shadow-lg {variants[variant]} {sizes[size]} {className}"
>
	{#if loading}
		<div class="w-3 h-3 border-2 border-white/30 border-t-white rounded-full animate-spin"></div>
	{/if}
	{@render children()}
</button>

