<script lang="ts">
	interface Props {
		href: string;
		label: string;
		icon: string;
		isCollapsed: boolean;
		active: boolean;
		color: string;
		indent?: boolean;
		mt?: string;
	}

	let { 
		href, 
		label, 
		icon, 
		isCollapsed, 
		active, 
		color = "indigo", 
		indent = false,
		mt = ""
	}: Props = $props();

	const colorMap: Record<string, string> = {
		indigo: "bg-indigo-500/20 shadow-indigo-500/20 group-hover:bg-indigo-500/10",
		blue: "bg-blue-500/20 shadow-blue-500/20 group-hover:bg-blue-500/10",
		rose: "bg-rose-500/20 shadow-rose-500/20 group-hover:bg-rose-500/10",
		amber: "bg-amber-500/20 shadow-amber-500/20 group-hover:bg-amber-500/10",
		orange: "bg-orange-500/20 shadow-orange-500/20 group-hover:bg-orange-500/10",
		cyan: "bg-cyan-500/20 shadow-cyan-500/20 group-hover:bg-cyan-500/10",
		emerald: "bg-emerald-500/20 shadow-emerald-500/20 group-hover:bg-emerald-500/10",
		purple: "bg-purple-500/20 shadow-purple-500/20 group-hover:bg-purple-500/10",
		violet: "bg-violet-500/20 shadow-violet-500/20 group-hover:bg-violet-500/10"
	};

	let iconBgClass = $derived(active ? colorMap[color].split(" group-hover")[0] : `bg-slate-50 dark:bg-slate-900 ${colorMap[color].split("shadow")[1]?.split(" ")[1] || ""}`);
</script>

<a 
	{href} 
	class={[
		"flex items-center gap-3 rounded-xl transition-all duration-200 group border",
		mt,
		indent && !isCollapsed ? "ml-5 border-l-2 border-l-slate-100 dark:border-l-slate-800" : "",
		isCollapsed ? "px-3 py-2" : "px-3 py-2",
		active 
			? "bg-slate-100 dark:bg-slate-800 border-slate-200 dark:border-slate-700 shadow-inner" 
			: "border-transparent hover:bg-slate-100 dark:hover:bg-slate-800/50 hover:border-slate-200 dark:hover:border-slate-800"
	].join(" ")} 
	title={label}
>
	<span class={[
		"rounded-lg flex items-center justify-center transition-all duration-300 group-hover:scale-125 group-hover:rotate-12",
		isCollapsed ? "w-7 h-7 text-sm" : "w-7 h-7 text-sm",
		active ? "shadow-lg" : "",
		iconBgClass
	].join(" ")}>
		{icon}
	</span>
	{#if !isCollapsed}
		<span class={[
			"font-semibold text-sm tracking-tight transition-colors",
			active 
				? "text-slate-900 dark:text-white" 
				: "text-slate-500 dark:text-slate-400 group-hover:text-slate-700 dark:group-hover:text-slate-200"
		].join(" ")}>
			{label}
		</span>
	{/if}
</a>
